"""Local web UI for reviewing Aizentify application exports.

Upload the Tally form export (CSV or XLSX) and it becomes a dated report:
state + AI-relevance ranking are computed once at upload time and written
to that report's candidates.csv, which is also where reviewer ratings and
Round 1 / Round 2 shortlist marks get persisted. Binds to 127.0.0.1 only.

Usage:
    python webapp.py
    -> open http://127.0.0.1:8790
"""

import csv
import json
import threading
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import ranking

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = DATA_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

FIELDNAMES = [
    "uid", "name", "email", "mobile", "city", "state", "role", "tier",
    "exp_raw", "exp_years", "employer", "cert_text", "ai_score",
    "claude_mentioned", "matched_keywords", "final_score", "resume",
    "submitted_at", "rating", "round1", "round2",
]

_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()


def _lock_for(report_id: str) -> threading.Lock:
    with _locks_guard:
        if report_id not in _locks:
            _locks[report_id] = threading.Lock()
        return _locks[report_id]


def report_dir(report_id: str) -> Path:
    d = REPORTS_DIR / report_id
    if not d.is_dir():
        raise HTTPException(404, f"No report '{report_id}'")
    return d


def read_meta(report_id: str) -> dict:
    d = report_dir(report_id)
    return json.loads((d / "meta.json").read_text())


def list_reports() -> list[dict]:
    reports = []
    for d in REPORTS_DIR.iterdir():
        meta_path = d / "meta.json"
        if meta_path.exists():
            reports.append(json.loads(meta_path.read_text()))
    reports.sort(key=lambda m: m["uploaded_at"], reverse=True)
    return reports


def read_candidates(report_id: str) -> list[dict]:
    path = report_dir(report_id) / "candidates.csv"
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row["exp_years"] = float(row["exp_years"])
        row["ai_score"] = int(row["ai_score"])
        row["final_score"] = float(row["final_score"])
        row["claude_mentioned"] = row["claude_mentioned"] == "True"
        row["matched_keywords"] = row["matched_keywords"].split(";") if row["matched_keywords"] else []
        row["rating"] = int(row["rating"]) if row["rating"] else 0
        row["round1"] = row["round1"] == "True"
        row["round2"] = row["round2"] == "True"
    return rows


def write_candidates(report_id: str, rows: list[dict]) -> None:
    d = report_dir(report_id)
    path = d / "candidates.csv"
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            out = dict(row)
            out["matched_keywords"] = ";".join(row["matched_keywords"])
            out["claude_mentioned"] = str(row["claude_mentioned"])
            out["round1"] = str(row["round1"])
            out["round2"] = str(row["round2"])
            writer.writerow(out)
    tmp.replace(path)


def summarize(candidates: list[dict]) -> dict:
    intern = sorted((c for c in candidates if c["tier"] == "Intern"), key=lambda c: -c["final_score"])
    experienced = sorted((c for c in candidates if c["tier"] == "Experienced"), key=lambda c: -c["final_score"])
    other = [c for c in candidates if c["tier"] == "Other"]
    return {
        "intern": intern,
        "experienced": experienced,
        "other": other,
        "intern_total": len(intern),
        "experienced_total": len(experienced),
        "other_total": len(other),
        "claude_total": sum(1 for c in candidates if c["claude_mentioned"]),
        "states": sorted({c["state"] for c in candidates}),
    }


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {"reports": list_reports()})


@app.post("/reports/upload")
async def upload_report(file: UploadFile):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".csv", ".xlsx", ".xlsm"):
        return RedirectResponse(url="/?error=Unsupported+file+type", status_code=303)

    report_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    d = REPORTS_DIR / report_id
    d.mkdir(parents=True, exist_ok=True)

    source_path = d / f"source{suffix}"
    source_path.write_bytes(await file.read())

    try:
        result = ranking.build_report(source_path)
    except Exception as e:
        return RedirectResponse(url=f"/?error={e}", status_code=303)

    write_candidates(report_id, result["candidates"])
    summary = summarize(result["candidates"])
    meta = {
        "id": report_id,
        "original_filename": file.filename,
        "uploaded_at": datetime.now().isoformat(timespec="seconds"),
        "total_submissions": result["total_submissions"],
        "relocate_yes": result["relocate_yes"],
        "relocate_no": result["relocate_no"],
        "intern_total": summary["intern_total"],
        "experienced_total": summary["experienced_total"],
        "other_total": summary["other_total"],
    }
    (d / "meta.json").write_text(json.dumps(meta, indent=2))

    return RedirectResponse(url=f"/reports/{report_id}", status_code=303)


@app.get("/reports/{report_id}")
def view_report(report_id: str, request: Request):
    meta = read_meta(report_id)
    candidates = read_candidates(report_id)
    summary = summarize(candidates)
    return templates.TemplateResponse(
        request,
        "report.html",
        {
            "meta": meta,
            "summary": summary,
            "candidates_json": json.dumps(candidates).replace("</", "<\\/"),
        },
    )


class UpdatePayload(BaseModel):
    rating: int | None = None
    round1: bool | None = None
    round2: bool | None = None


@app.post("/reports/{report_id}/candidates/{uid}/update")
def update_candidate(report_id: str, uid: str, payload: UpdatePayload):
    lock = _lock_for(report_id)
    with lock:
        rows = read_candidates(report_id)
        target = next((r for r in rows if r["uid"] == uid), None)
        if target is None:
            raise HTTPException(404, f"No candidate '{uid}' in report '{report_id}'")

        if payload.rating is not None:
            if not (0 <= payload.rating <= 5):
                raise HTTPException(400, "rating must be between 0 and 5")
            target["rating"] = payload.rating
        if payload.round1 is not None:
            target["round1"] = payload.round1
        if payload.round2 is not None:
            target["round2"] = payload.round2

        write_candidates(report_id, rows)
    return target


if __name__ == "__main__":
    print("Interview Shortlist running at http://127.0.0.1:8790")
    uvicorn.run(app, host="127.0.0.1", port=8790)
