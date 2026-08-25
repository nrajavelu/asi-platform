"""
Candidate-facing gate - run this only during a live test window, on the
same network as the candidates. Marks each attempt "started" the moment a
candidate opens their link, then either redirects into a Google Form
(round_type="aptitude"/"programming") or serves the local AICodeStudio
coding session (round_type="coding").

This is a separate process from webui.py (the admin dashboard, which stays
on 127.0.0.1 only). This one binds to 0.0.0.0 so lab machines can reach it -
your Mac must stay on and connected to the same network as the candidates
for the whole test window. For coding rounds, Judge0 must also be running
(docker compose up -d in judge0/judge0-v1.13.1/).

Usage:
    python app.py
    -> prints the LAN URL to give to invite.py as --base-url
"""

import json
import socket
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from coding_session import assign_coding_questions, assign_sectioned_coding_questions
from judge0_client import run_against_test_cases
from models import Attempt, CodingAttemptQuestion, CodingQuestion, CodingTestCase, Round, SessionLocal, init_db
from css_grader import run_css_submission
from react_grader import run_react_submission
from seb_config import personalized_seb_bytes, seb_template_for_round_type
from sql_grader import run_sql_submission


def _candidate_safe_status(status: str) -> str:
    """The candidate never sees a correctness verdict, not even via a
    status pill - passed/partial/failed all collapse to 'submitted' here.
    The real status stays untouched in the DB for admin/analytics use."""
    if status in ("passed", "partial", "failed"):
        return "submitted"
    return status


def _candidate_safe_run_result(r: dict) -> dict:
    """Strips the correctness verdict from a grader result before it goes
    to the candidate's browser - passed/status/expected_output are never
    sent, even for sample cases. Only raw output/errors are - the
    candidate judges correctness themselves against the stated example."""
    safe = {"stdout": r.get("stdout"), "stderr": r.get("stderr")}
    if r.get("compile_output"):
        safe["compile_output"] = r["compile_output"]
    return safe


def _grade(question: CodingQuestion, code: str, cases: list) -> list[dict]:
    """Dispatches to the right execution backend by question_type. Every
    backend returns the same {passed, weight, stdout, stderr, ...}-shaped
    list, so everything downstream (scoring, status, analytics) is
    identical regardless of which one ran."""
    if question.question_type == "sql":
        return run_sql_submission(question, code, cases)
    if question.question_type == "react":
        return run_react_submission(question, code, cases)
    if question.question_type == "css":
        return run_css_submission(question, code, cases)
    return run_against_test_cases(code, question.language_id, cases)

PORT = 8788
BASE_DIR = Path(__file__).parent

app = FastAPI()
init_db()

templates = Jinja2Templates(directory=str(BASE_DIR / "coding_templates"))
monaco_dir = BASE_DIR / "coding_static" / "vendor"
if monaco_dir.exists():
    app.mount("/coding-assets", StaticFiles(directory=str(monaco_dir)), name="coding-assets")


def get_lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def _deadline(round_: Round, session_started_at: str) -> datetime:
    started = datetime.fromisoformat(session_started_at)
    return started + timedelta(minutes=round_.duration_minutes)


@app.get("/start/{token}")
def start(token: str):
    with SessionLocal() as session:
        attempt = session.query(Attempt).filter_by(token=token).first()
        if attempt is None:
            raise HTTPException(status_code=404, detail="Invalid or unknown access link")
        if attempt.status not in ("invited", "started"):
            raise HTTPException(
                status_code=403,
                detail=f"This link has already been used (status: {attempt.status})",
            )

        round_ = session.get(Round, attempt.round_id)
        if round_ is None:
            raise HTTPException(status_code=500, detail="Round not found")

        if attempt.status == "invited":
            attempt.status = "started"
            attempt.started_at = datetime.now(timezone.utc).isoformat()
            session.commit()

        if round_.round_type == "coding":
            return RedirectResponse(url=f"/coding/{token}", status_code=302)

        if not round_.responder_uri:
            raise HTTPException(status_code=500, detail="Round is not linked to a form yet")
        return RedirectResponse(url=round_.responder_uri, status_code=302)


@app.get("/seb/{token}")
def download_seb(request: Request, token: str):
    """Builds a personalized .seb file on the fly, rather than one written
    to disk at invite-send time - keeps the LAN IP baked into startURL as
    fresh as possible (built from this actual request, via request.base_url,
    not a separately-detected IP that could differ), and sidesteps mail
    gateways that strip .seb attachments since invite.py can link here
    instead of attaching the file directly."""
    with SessionLocal() as session:
        attempt = session.query(Attempt).filter_by(token=token).first()
        if attempt is None:
            raise HTTPException(status_code=404, detail="Invalid or unknown access link")
        round_ = session.get(Round, attempt.round_id)
        if round_ is None:
            raise HTTPException(status_code=404, detail="Round not found")

        try:
            template_path = seb_template_for_round_type(round_.round_type)
        except ValueError as e:
            raise HTTPException(status_code=500, detail=str(e))
        if not template_path.exists():
            raise HTTPException(
                status_code=500,
                detail=f"No SEB template at {template_path} for round type {round_.round_type!r} yet.",
            )

        start_url = f"{str(request.base_url).rstrip('/')}/start/{token}"
        content = personalized_seb_bytes(template_path, start_url)
        return Response(
            content=content,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{token}.seb"'},
        )


def _ensure_session_initialized(session, attempt: Attempt, round_: Round) -> None:
    """Idempotent: safe to call from any route that touches a coding
    session, not just the page load - a direct hit, bookmark, or refresh
    must never find an uninitialized session."""
    if not attempt.session_started_at:
        attempt.session_started_at = datetime.now(timezone.utc).isoformat()
        session.commit()
    if round_.section_plan:
        assign_sectioned_coding_questions(session, attempt, json.loads(round_.section_plan))
    else:
        assign_coding_questions(session, attempt, count=round_.coding_question_count)


@app.get("/coding/{token}")
def coding_page(request: Request, token: str):
    with SessionLocal() as session:
        attempt = session.query(Attempt).filter_by(token=token).first()
        if attempt is None:
            raise HTTPException(status_code=404, detail="Invalid or unknown access link")
        if attempt.status == "submitted":
            return templates.TemplateResponse(request, "finished.html", {})

        round_ = session.get(Round, attempt.round_id)
        if round_ is None or round_.round_type != "coding":
            raise HTTPException(status_code=404, detail="This link is not a coding round")

        try:
            _ensure_session_initialized(session, attempt, round_)
        except ValueError as e:
            raise HTTPException(status_code=500, detail=str(e))

        return templates.TemplateResponse(request, "session.html", {"token": token})


@app.get("/coding/{token}/api/session")
def session_state(token: str):
    with SessionLocal() as session:
        attempt = session.query(Attempt).filter_by(token=token).first()
        if attempt is None:
            raise HTTPException(status_code=404, detail="Invalid token")
        round_ = session.get(Round, attempt.round_id)
        if round_ is None or round_.round_type != "coding":
            raise HTTPException(status_code=404, detail="This link is not a coding round")
        if attempt.status == "submitted":
            remaining_seconds = 0
        else:
            try:
                _ensure_session_initialized(session, attempt, round_)
            except ValueError as e:
                raise HTTPException(status_code=500, detail=str(e))
            deadline = _deadline(round_, attempt.session_started_at)
            remaining_seconds = max(0, int((deadline - datetime.now(timezone.utc)).total_seconds()))
            if remaining_seconds == 0:
                _finish_attempt(session, attempt)

        assigned = (
            session.query(CodingAttemptQuestion)
            .filter_by(attempt_id=attempt.id)
            .order_by(CodingAttemptQuestion.assigned_order)
            .all()
        )
        questions = []
        for row in assigned:
            q = session.get(CodingQuestion, row.question_id)
            samples = session.query(CodingTestCase).filter_by(question_id=q.id, is_sample=True).all()
            questions.append({
                "question_id": q.id,
                "title": q.title,
                "topic": q.topic,
                "statement": q.statement,
                "starter_code": row.last_submitted_code or q.starter_code or "",
                "language_id": q.language_id,
                "question_type": q.question_type,
                "harness_fixture": q.harness_fixture if q.question_type == "css" else None,
                "hints": q.hints.split("\n") if q.hints else [],
                "points": q.points,
                "status": _candidate_safe_status(row.status),
                "sample_test_cases": [{"stdin": t.stdin, "expected_output": t.expected_output} for t in samples],
            })

        return JSONResponse({
            "remaining_seconds": remaining_seconds,
            "duration_minutes": round_.duration_minutes,
            "attempt_status": attempt.status,
            "questions": questions,
        })


@app.post("/coding/{token}/api/run")
def run_code(token: str, question_id: int = Form(...), code: str = Form(...)):
    with SessionLocal() as session:
        attempt = session.query(Attempt).filter_by(token=token).first()
        if attempt is None:
            raise HTTPException(status_code=404, detail="Invalid token")
        round_ = session.get(Round, attempt.round_id)
        _reject_if_expired(session, round_, attempt)

        question = session.get(CodingQuestion, question_id)
        samples = session.query(CodingTestCase).filter_by(question_id=question_id, is_sample=True).all()
        results = _grade(question, code, samples)

        # Run never affects best_score (it's a sandbox preview against
        # samples only), but it's a real analytics signal: distinguishes
        # "opened and tried" from "never touched" for questions that never
        # reach Submit.
        row = (
            session.query(CodingAttemptQuestion)
            .filter_by(attempt_id=attempt.id, question_id=question_id)
            .first()
        )
        if row.status == "not_attempted":
            row.status = "attempted"
            session.commit()

        # Candidate sees raw output/errors only - never a pass/fail verdict.
        # They judge correctness themselves against the stated example.
        safe_results = [_candidate_safe_run_result(r) for r in results]
        return JSONResponse({"results": safe_results})


@app.post("/coding/{token}/api/submit")
def submit_code(token: str, question_id: int = Form(...), code: str = Form(...)):
    with SessionLocal() as session:
        attempt = session.query(Attempt).filter_by(token=token).first()
        if attempt is None:
            raise HTTPException(status_code=404, detail="Invalid token")
        round_ = session.get(Round, attempt.round_id)
        _reject_if_expired(session, round_, attempt)

        question = session.get(CodingQuestion, question_id)
        all_cases = session.query(CodingTestCase).filter_by(question_id=question_id).all()
        results = _grade(question, code, all_cases)

        total_weight = sum(tc.weight for tc in all_cases)
        passed_weight = sum(r["weight"] for r in results if r["passed"])
        score = round(question.points * passed_weight / total_weight) if total_weight else 0

        row = (
            session.query(CodingAttemptQuestion)
            .filter_by(attempt_id=attempt.id, question_id=question_id)
            .first()
        )
        row.last_submitted_code = code
        row.submitted_at = datetime.now(timezone.utc).isoformat()
        row.best_score = max(row.best_score, score)
        # status reflects the best-ever submission for this question, not
        # just the latest one - a later wrong resubmission must not erase
        # an earlier fully-correct result.
        if row.best_score >= question.points:
            row.status = "passed"
        elif row.best_score > 0:
            row.status = "partial"
        else:
            row.status = "failed"
        session.commit()

        # The candidate only ever sees a submission confirmation - no
        # score, no pass/fail, not even indirectly via which test cases
        # "failed". The real score/status are stored above for grading/
        # analytics; nothing about correctness leaves this response.
        return JSONResponse({"submitted": True})


@app.post("/coding/{token}/api/finish")
def finish_session(token: str):
    with SessionLocal() as session:
        attempt = session.query(Attempt).filter_by(token=token).first()
        if attempt is None:
            raise HTTPException(status_code=404, detail="Invalid token")
        _finish_attempt(session, attempt)
        return JSONResponse({"status": "submitted"})


def _reject_if_expired(session, round_: Round, attempt: Attempt) -> None:
    if attempt.status == "submitted":
        raise HTTPException(status_code=403, detail="This session has already ended")
    try:
        _ensure_session_initialized(session, attempt, round_)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    deadline = _deadline(round_, attempt.session_started_at)
    if datetime.now(timezone.utc) > deadline:
        with SessionLocal() as session:
            a = session.query(Attempt).filter_by(id=attempt.id).first()
            _finish_attempt(session, a)
        raise HTTPException(status_code=403, detail="Time is up - this session has ended")


def _finish_attempt(session, attempt: Attempt) -> None:
    if attempt.status == "submitted":
        return
    rows = session.query(CodingAttemptQuestion).filter_by(attempt_id=attempt.id).all()
    total_score = sum(r.best_score for r in rows)
    max_score = 0
    for r in rows:
        q = session.get(CodingQuestion, r.question_id)
        max_score += q.points
    attempt.score = total_score
    attempt.max_score = max_score
    attempt.percent = round(total_score / max_score * 100) if max_score else 0
    attempt.status = "submitted"
    attempt.submitted_at = datetime.now(timezone.utc).isoformat()
    session.commit()


if __name__ == "__main__":
    import uvicorn

    lan_ip = get_lan_ip()
    print(f"Candidate start-gate running on the LAN at http://{lan_ip}:{PORT}")
    print(f"Use this as invite.py's --base-url: http://{lan_ip}:{PORT}")
    print("For coding rounds, Judge0 must also be running (docker compose up -d")
    print("in judge0/judge0-v1.13.1/).")
    print("Keep this window open for the entire test window.\n")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
