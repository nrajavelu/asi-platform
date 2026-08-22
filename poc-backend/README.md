# ASI Platform — POC implementation

This is a **real, runnable** application, not a mock — the technical
counterpart to the ASI Console and pitch deck. It answers two questions
before anyone commits engineering budget: *does the pipeline actually work
end to end, on more than one case,* and *which layer determines accuracy
and cost?*

Five files, one pipeline per case:

| File | Layer | Needs a key? |
|---|---|---|
| `cases.py` | Registry — case id → corpus file + question | No |
| `chunking.py` | Ingestion — structure-aware chunking | No |
| `retrieval.py` | Retrieval — BM25 today, swap for Qdrant later | No |
| `analyze.py` | Orchestration — real Claude API call, streamed | **Yes** |
| `analyze.py::check_grounding` | Guardrail — verifies every citation against the actual retrieved text | **Yes** |

`corpus/` holds five illustrative case documents (not real filings) —
EV Motor Co., Northwind Retail, Meridian Health, Vertex SaaS, and Crestwood
University — the same cases used in the console demo, now backed by real
text a real pipeline actually ingests.

Three ways to run it:

- **`benchmark.py`** — one-shot CLI, prints the full JSON report for one case
- **`cli.py`** — friendlier wrapper: list cases, analyze one, or start the API
- **`server.py`** — a real FastAPI app exposing the pipeline over HTTP

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# ingestion + retrieval run with no key at all, on any case:
python3 cli.py list
python3 cli.py analyze cu

# add a key to also run the live generation + guardrail pass:
export ANTHROPIC_API_KEY=sk-...
python3 cli.py analyze ev
python3 cli.py analyze ev -q "Is the tariff a threat or a cost EV Motor Co. can pass through?"

# or run it as a real API:
python3 cli.py serve --reload
curl http://localhost:8000/api/v1/cases
curl -X POST http://localhost:8000/api/v1/analyze-strategy \
  -H "Content-Type: application/json" -d '{"case_id": "mh"}'
```

`benchmark.py --case <id> --question "..."` does the same thing as
`cli.py analyze` for anyone who prefers the original entry point.

## What a full run tells you, layer by layer

- **Ingestion** — words/sec chunked, chunk count, estimated tokens. This is
  where document *size* turns into a cost and time number: a 300-word
  excerpt chunks in under a millisecond; a real 40–60K-token 10-K will be
  the actual stress test.
- **Retrieval** — index-build time and per-query latency, plus which chunk
  actually got selected for a given question. This is the layer most
  people underrate: if the wrong chunk gets retrieved, Claude reasons
  perfectly over the wrong evidence and the failure looks like a "model
  accuracy" problem when it's a retrieval problem.
- **Generation** — real `input_tokens` / `output_tokens` from the API's own
  usage payload, real time-to-first-token (streamed), real tokens/sec.
  This is what a per-student-turn latency and cost budget is actually
  built from — not a guess.
- **Guardrail** — every `source_quote` Claude returns is checked as a
  literal substring of the chunks it was actually given. `grounding_rate`
  is the one number that answers "does this hallucinate." Claims the
  model marks `[inference]` are excluded from the denominator by design —
  they're supposed to be unconfirmed, and the platform should present them
  that way rather than penalize them for not being cited.

## The API

`server.py` is a small FastAPI app — the same pipeline, reachable over
HTTP instead of a one-shot CLI run, so it can sit behind a real frontend
later without a rewrite.

| Endpoint | Method | Cost |
|---|---|---|
| `/health` | GET | Free |
| `/api/v1/cases` | GET | Free — lists the five cases, no key needed |
| `/api/v1/analyze-strategy` | POST | Ingestion + retrieval free; generation bills if a key is set |

`POST /api/v1/analyze-strategy` body: `{"case_id": "ev", "question": "..."}`
— `question` is optional and falls back to the case's default PESTLE/SWOT
prompt. An unknown `case_id` returns `404`. A missing `ANTHROPIC_API_KEY`
doesn't error the request — the response's `live_pass_skipped_reason`
explains why generation was skipped, and the ingestion/retrieval layers
still return real numbers.

This is intentionally **not** wired into the polished console
(`asi-console.html`) or the slide deck — those stay 100% simulated and
free to demo as many times as you want, on purpose (see below). This
server is the separate, real thing you run yourself, on your own key and
your own terms, when you want to verify the pipeline actually works rather
than take the pitch's word for it.

## Cost safety for repeated demos

This harness is set up so running it many times for a demo will not put a
dent in your Anthropic spend:

- **Default model is Claude Haiku 4.5** (`$1.00` / `$5.00` per million input /
  output tokens) — the cheapest current model, in `DEFAULT_MODEL` in
  `analyze.py`. A single run on any of these sample cases costs a small
  fraction of a cent. Only switch to `claude-sonnet-5` or `claude-opus-5`
  in `analyze.py` when you deliberately want to compare reasoning quality,
  and expect the cost to scale accordingly (Sonnet 5 is roughly 2x Haiku's
  rate at today's introductory pricing; Opus 5 is roughly 5x).
- **`max_tokens` is capped** (900) on every call, so a single request has a
  hard ceiling on worst-case output spend — it can't run away.
- **Every run prints its exact cost** — `estimated_cost_usd` in the JSON
  report — computed from the real `usage.input_tokens` /
  `usage.output_tokens` the API returns, not a guess.
- **Set a hard spend limit on the API key itself**, independent of anything
  in this code: in the Anthropic Console, under your API key's settings, set
  a monthly budget alert or a hard spend cap. That's the backstop if this
  script (or the server, run by someone else) is used far more than
  expected.
- **Use a separate, low-limit API key for demos** rather than a production
  key — if you're showing this to a room repeatedly, a key scoped to a small
  monthly cap means a mistake costs at most that cap, not your whole account.

At real scale (a full cohort, real 10-Ks instead of these samples), the
platform design in the pitch deck leans on two things this harness doesn't
exercise yet: **prompt caching** (the case document is reused across every
student's turns — cached reads cost roughly a tenth of the input price)
and **model routing** (cheap models like Haiku for factor extraction, a
mid-tier model for the main Socratic reasoning, escalating to a stronger
model only for faculty appeals). Both are the actual cost levers at
cohort scale, not the per-call price alone.

## Honest scope

This harness swaps BM25 for the vector DB and five hand-written cases for
a real institutional corpus. Both are narrow, well-defined swaps
(`retrieval.py`, `corpus/` + one line in `cases.py`) — the orchestration
and guardrail logic don't change. What it does *not* mock: the chunker,
the retrieval ranking, the API call, the token counts, the timing, the
citation check, or the HTTP layer. Every number this code prints came
from code that ran, not from a number someone typed into HTML.
