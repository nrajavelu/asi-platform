"""End-to-end benchmark: ingest -> retrieve -> generate -> verify.

Every number this prints is measured, not simulated. The ingestion and
retrieval stages need no credentials and always run. The generation and
grounding stages call the real Claude API and only run if ANTHROPIC_API_KEY
is set -- without it, the report says so explicitly instead of guessing.

Run:
    source .venv/bin/activate
    export ANTHROPIC_API_KEY=sk-...   # optional, enables the live pass
    python benchmark.py               # defaults to the EV Motor Co. case
    python benchmark.py --case cu     # or any id from `python cli.py list`
"""
import argparse
import json
import time

from cases import CASES, case_text
from chunking import chunk_text, estimate_tokens
from retrieval import Retriever


def run(case_id: str, question: str | None = None) -> dict:
    case = CASES[case_id]
    text = case_text(case_id)
    question = question or case["question"]

    t0 = time.perf_counter()
    chunks = chunk_text(text)
    chunk_seconds = time.perf_counter() - t0
    total_tokens_est = sum(estimate_tokens(c) for c in chunks)

    retriever = Retriever(chunks)
    retrieved, retrieval_seconds = retriever.query(question, k=4)

    report = {
        "case": {"id": case_id, "name": case["name"]},
        "layer_1_ingestion": {
            "source_words": len(text.split()),
            "chunks_produced": len(chunks),
            "chunking_seconds": round(chunk_seconds, 5),
            "estimated_tokens_indexed": total_tokens_est,
            "throughput_words_per_sec": round(len(text.split()) / max(chunk_seconds, 1e-6), 1),
        },
        "layer_2_retrieval": {
            "engine": "BM25 (stand-in for Qdrant dense retrieval)",
            "index_build_seconds": round(retriever.index_seconds, 5),
            "query_seconds": round(retrieval_seconds, 5),
            "k": len(retrieved),
            "top_chunk_preview": retrieved[0][0][:140] + "..." if retrieved else None,
        },
    }

    try:
        from analyze import analyze, check_grounding

        result = analyze(question, retrieved)
        parsed = json.loads(result["raw_text"])
        grounding = check_grounding(parsed, retrieved)

        out_tok = result["usage"]["output_tokens"]
        secs = result["timing"]["total_seconds"]
        report["layer_3_generation"] = {
            "model": result["model"],
            "input_tokens": result["usage"]["input_tokens"],
            "output_tokens": out_tok,
            "time_to_first_token_seconds": (
                round(result["timing"]["ttft_seconds"], 3)
                if result["timing"]["ttft_seconds"] else None
            ),
            "total_seconds": round(secs, 3),
            "output_tokens_per_second": round(out_tok / secs, 1) if secs else None,
            "estimated_cost_usd": round(result["estimated_cost_usd"], 6),
        }
        report["layer_4_guardrail"] = {
            "claims_checked": len(grounding["claims"]),
            "grounding_rate": (
                round(grounding["grounding_rate"], 3)
                if grounding["grounding_rate"] is not None else None
            ),
            "claims": grounding["claims"],
        }
        report["analysis"] = parsed
    except Exception as e:  # noqa: BLE001 -- surfaced in the report, not swallowed
        report["layer_3_generation"] = None
        report["layer_4_guardrail"] = None
        report["live_pass_skipped_reason"] = f"{type(e).__name__}: {e}"

    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--case", default="ev", choices=sorted(CASES), help="case id to run (default: ev)")
    parser.add_argument("--question", default=None, help="override the case's default analysis question")
    args = parser.parse_args()
    print(json.dumps(run(args.case, args.question), indent=2, default=str))


if __name__ == "__main__":
    main()
