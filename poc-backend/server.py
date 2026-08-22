"""FastAPI app exposing the ASI Platform POC as a real HTTP API.

Same four-layer pipeline as benchmark.py (ingest -> retrieve -> generate ->
verify), reachable over HTTP instead of a one-shot CLI run. Ingestion and
retrieval always run and cost nothing; generation only runs -- and only
costs anything -- when ANTHROPIC_API_KEY is set in the server's environment.

Run:
    source .venv/bin/activate
    export ANTHROPIC_API_KEY=sk-...   # optional, enables live analysis
    uvicorn server:app --reload --port 8000

Try it:
    curl http://localhost:8000/api/v1/cases
    curl -X POST http://localhost:8000/api/v1/analyze-strategy \
      -H "Content-Type: application/json" \
      -d '{"case_id": "ev"}'
"""
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from benchmark import run
from cases import CASES, list_cases

app = FastAPI(
    title="ASI Platform POC API",
    description=(
        "Real ingestion, retrieval, generation, and citation-guardrail "
        "pipeline behind the ASI Platform pitch -- not a mock."
    ),
    version="0.1.0",
)

# Local-dev convenience: lets a browser-based frontend on a different port
# call this API directly during a demo. Tighten this before any real deploy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    case_id: str
    question: Optional[str] = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/v1/cases")
def get_cases():
    """List available case corpora -- no API key required, no cost."""
    return {"cases": list_cases()}


@app.post("/api/v1/analyze-strategy")
def analyze_strategy(req: AnalyzeRequest):
    """Run the full pipeline for one case: ingest, retrieve, generate, verify.

    Ingestion and retrieval always execute. Generation and the citation
    guardrail only execute -- and only bill -- if the server has a real
    ANTHROPIC_API_KEY; otherwise the response's `live_pass_skipped_reason`
    explains why, and everything else in the report is still real.
    """
    if req.case_id not in CASES:
        raise HTTPException(
            status_code=404,
            detail=f"unknown case_id {req.case_id!r} -- see GET /api/v1/cases for valid ids",
        )
    return run(req.case_id, req.question)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
