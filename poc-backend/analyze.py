"""Real Claude API call for the orchestration + guardrail layers.

Requires ANTHROPIC_API_KEY. Streams the response to measure real
time-to-first-token, reads real input/output token counts off the API's
usage payload, and checks every cited quote against the actual retrieved
text -- this is the same check the platform's Guardrail Engine would run
before a response reaches a student.

Cost safety: defaults to Claude Haiku 4.5, the cheapest current model, so a
demo run costs fractions of a cent. Bump DEFAULT_MODEL to a stronger model
only when you deliberately want to compare quality -- see PRICING below for
what that costs.
"""
import time
from anthropic import Anthropic

# Prices are USD per million tokens, current as of this writing. Sonnet 5's
# lower figure is introductory pricing through 2026-08-31 -- after that it
# reverts to the higher one. Re-check platform.claude.com/docs/en/pricing
# before trusting these for a real budget decision.
PRICING = {
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00},
    "claude-sonnet-5": {"input": 2.00, "output": 10.00},  # intro price
    "claude-opus-5": {"input": 5.00, "output": 25.00},
}
DEFAULT_MODEL = "claude-haiku-4-5"


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    rates = PRICING.get(model)
    if not rates:
        return float("nan")
    return (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000


SYSTEM_PROMPT = (
    "You are an AI Business Strategy Professor. Given the retrieved case "
    "excerpts, produce STRICT JSON only (no prose, no markdown fences) with "
    "this shape: "
    '{"swot_analysis": {"strengths": [...], "weaknesses": [...], '
    '"opportunities": [...], "threats": [...]}, "socratic_pedagogy_feedback": '
    '{"student_guidance_prompt": "...", "analytical_score": 0-100}}. '
    "Each SWOT item is an object {\"claim\": string, \"source_quote\": string}. "
    "source_quote MUST be copied verbatim, word-for-word, from the provided "
    "excerpts -- never paraphrase it. If a claim requires inference beyond "
    "the excerpts, set source_quote to null and prefix the claim with "
    "'[inference]'."
)


def analyze(question: str, retrieved_chunks, model: str = DEFAULT_MODEL, max_tokens: int = 900):
    client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    context = "\n\n---\n\n".join(
        f"[chunk {i}] {c}" for i, (c, _score) in enumerate(retrieved_chunks)
    )
    user_msg = f"Case excerpts:\n{context}\n\nQuestion: {question}"

    t0 = time.perf_counter()
    first_token_at = None
    text = ""
    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,  # hard cap -- bounds worst-case spend per call
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    ) as stream:
        for event in stream:
            if event.type == "content_block_delta" and event.delta.type == "text_delta":
                if first_token_at is None:
                    first_token_at = time.perf_counter()
                text += event.delta.text
        final = stream.get_final_message()

    total = time.perf_counter() - t0
    ttft = (first_token_at - t0) if first_token_at else None

    return {
        "raw_text": text,
        "model": model,
        "usage": {
            "input_tokens": final.usage.input_tokens,
            "output_tokens": final.usage.output_tokens,
        },
        "timing": {"ttft_seconds": ttft, "total_seconds": total},
        "estimated_cost_usd": estimate_cost_usd(
            model, final.usage.input_tokens, final.usage.output_tokens
        ),
    }


def check_grounding(parsed_json: dict, retrieved_chunks):
    source_text = " ".join(c for c, _score in retrieved_chunks)
    results = []
    for quadrant in ("strengths", "weaknesses", "opportunities", "threats"):
        for item in parsed_json.get("swot_analysis", {}).get(quadrant, []):
            quote = (item.get("source_quote") or "").strip()
            is_inference = quote == "" or str(item.get("claim", "")).startswith("[inference]")
            grounded = (not is_inference) and quote in source_text
            results.append({
                "quadrant": quadrant,
                "claim": item.get("claim"),
                "inference": is_inference,
                "grounded": grounded,
            })
    checkable = [r for r in results if not r["inference"]]
    grounding_rate = (
        sum(r["grounded"] for r in checkable) / len(checkable) if checkable else None
    )
    return {"claims": results, "grounding_rate": grounding_rate}
