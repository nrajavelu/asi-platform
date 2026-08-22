"""Registry of case corpora available to the POC.

Each entry names a real file in corpus/ and the default question the
Socratic prompt is asked. Adding a new case for a pilot is: drop a .txt
file in corpus/, add one entry here -- nothing else changes.
"""
from pathlib import Path

CORPUS_DIR = Path(__file__).parent / "corpus"

CASES = {
    "ev": {
        "name": "EV Motor Co.",
        "tag": "Automotive / EV",
        "file": "ev_motor_co.txt",
        "question": "Analyze EV Motor Co. using PESTLE mapped directly into SWOT based on the provided context.",
    },
    "nw": {
        "name": "Northwind Retail",
        "tag": "Retail / Consumer",
        "file": "northwind_retail.txt",
        "question": "Analyze Northwind Retail using PESTLE mapped directly into SWOT based on the provided context.",
    },
    "mh": {
        "name": "Meridian Health",
        "tag": "Healthcare / Telehealth",
        "file": "meridian_health.txt",
        "question": "Analyze Meridian Health using PESTLE mapped directly into SWOT based on the provided context.",
    },
    "vx": {
        "name": "Vertex SaaS",
        "tag": "B2B / SaaS",
        "file": "vertex_saas.txt",
        "question": "Analyze Vertex SaaS using PESTLE mapped directly into SWOT based on the provided context.",
    },
    "cu": {
        "name": "Crestwood University",
        "tag": "Higher Education",
        "file": "crestwood_university.txt",
        "question": "Analyze Crestwood University using PESTLE mapped directly into SWOT based on the provided context.",
    },
}


def case_text(case_id: str) -> str:
    if case_id not in CASES:
        raise KeyError(f"unknown case_id {case_id!r}; available: {sorted(CASES)}")
    return (CORPUS_DIR / CASES[case_id]["file"]).read_text()


def list_cases() -> list[dict]:
    return [{"id": cid, **{k: v for k, v in meta.items() if k != "file"}} for cid, meta in CASES.items()]
