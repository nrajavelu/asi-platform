"""
Local web UI for the campus test system, styled with Aizentify branding.
Wraps the same functions the CLI scripts and console.py use, so every
interface stays in sync. Binds to 127.0.0.1 only - never reachable by
anyone off this machine.

Usage:
    python webui.py
    -> open http://127.0.0.1:8787
"""

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote

import uvicorn
from fastapi import FastAPI, Form, Request, UploadFile
from fastapi.responses import RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from add_candidates import add_candidates_from_file
from build_form import build_coding_round, build_round, build_technical_discussion_round, promote_shortlisted
from final_conclusion_pdf import generate_final_conclusion_pdf
from google_auth import forms_service, gmail_service
from interview_session import assign_interview_questions
from invite import send_invites
from load_coding_questions import clear_bank as clear_coding_bank, load_question_file
from load_questions import load_bank
from models import (
    Attempt, Candidate, CodingAttemptQuestion, CodingQuestion, Drive, FormAnswer, InterviewAttemptQuestion,
    InterviewQuestion, Question, Round, SessionLocal, init_db,
)
from results import coding_question_analytics, detect_bounces, filter_attempts, ingest_results, kpi_summary, shortlist, top_n_attempts

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

init_db()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def render(request: Request, name: str, context: dict):
    return templates.TemplateResponse(request, name, context)


def flash_redirect(path: str, message: str, error: bool = False) -> RedirectResponse:
    sep = "&" if "?" in path else "?"
    q = f"{sep}flash={quote(message)}" + ("&err=1" if error else "")
    return RedirectResponse(url=path + q, status_code=303)


def flash_from_request(request: Request) -> tuple[str | None, bool]:
    flash = request.query_params.get("flash")
    return (unquote(flash) if flash else None, request.query_params.get("err") == "1")


async def save_upload(file: UploadFile) -> str:
    dest = UPLOAD_DIR / file.filename
    dest.write_bytes(await file.read())
    return str(dest)


@app.get("/")
def home(request: Request):
    session = SessionLocal()
    rounds = session.query(Round).order_by(Round.id).all()
    for r in rounds:
        r.attempt_count = session.query(Attempt).filter_by(round_id=r.id).count()
    flash, err = flash_from_request(request)
    return render(
        request,
        "index.html",
        {
            "active": "home",
            "flash": flash,
            "flash_error": err,
            "question_count": session.query(Question).count(),
            "drive_count": session.query(Drive).count(),
            "round_count": len(rounds),
            "candidate_count": session.query(Candidate).count(),
            "rounds": rounds,
        },
    )


@app.get("/bank")
def bank_page(request: Request):
    session = SessionLocal()
    flash, err = flash_from_request(request)
    return render(
        request,
        "bank.html",
        {
            "active": "bank",
            "flash": flash,
            "flash_error": err,
            "question_count": session.query(Question).count(),
            "coding_question_count": session.query(CodingQuestion).count(),
        },
    )


@app.post("/bank/upload")
async def bank_upload(file: UploadFile):
    path = await save_upload(file)
    try:
        count = load_bank(path)
    except Exception as e:
        return flash_redirect("/bank", str(e), error=True)
    return flash_redirect("/bank", f"Loaded {count} questions from {file.filename}")


@app.post("/bank/upload-coding")
async def bank_upload_coding(files: list[UploadFile], replace: bool = Form(False)):
    session = SessionLocal()
    loaded = []
    try:
        cleared = clear_coding_bank(session) if replace else 0
        for file in files:
            path = await save_upload(file)
            loaded.append(load_question_file(session, Path(path)))
        session.commit()
    except Exception as e:
        session.rollback()
        return flash_redirect("/bank", str(e), error=True)
    prefix = f"Cleared {cleared} existing question(s). " if replace else ""
    return flash_redirect("/bank", f"{prefix}Loaded {len(loaded)} coding question(s): {', '.join(loaded)}")


@app.get("/rounds/new")
def build_round_page(request: Request):
    flash, err = flash_from_request(request)
    session = SessionLocal()
    drives = session.query(Drive).order_by(Drive.name).all()
    return render(request, "build_round.html", {"active": "build", "flash": flash, "flash_error": err, "result": None, "drives": drives})


@app.post("/rounds/new")
def build_round_submit(
    request: Request,
    round_type: str = Form(...),
    count: int = Form(...),
    campus: str = Form(""),
    drive_name: str = Form(""),
    existing_drive_id: str = Form(""),
    title: str = Form(""),
    topics: str = Form(""),
    duration_minutes: str = Form(""),
    section_plan: str = Form(""),
):
    session = SessionLocal()
    parsed_duration = int(duration_minutes) if duration_minutes.strip() else None
    drives = session.query(Drive).order_by(Drive.name).all()

    if round_type == "coding":
        if not campus.strip() or not drive_name.strip():
            return render(request, "build_round.html", {"active": "build", "flash": "Campus name and Drive name are required.", "flash_error": True, "result": None, "drives": drives})

        parsed_plan = None
        if section_plan.strip():
            parsed_plan = []
            for line in section_plan.strip().splitlines():
                line = line.strip()
                if not line:
                    continue
                if ":" not in line:
                    return render(request, "build_round.html", {"active": "build", "flash": f"Bad section plan line (expected 'topic:count'): {line!r}", "flash_error": True, "result": None, "drives": drives})
                topic, _, n = line.partition(":")
                try:
                    parsed_plan.append((topic.strip(), int(n.strip())))
                except ValueError:
                    return render(request, "build_round.html", {"active": "build", "flash": f"Bad section plan count (expected an integer): {line!r}", "flash_error": True, "result": None, "drives": drives})

        try:
            round_ = build_coding_round(
                session, campus, drive_name, count,
                duration_minutes=parsed_duration, section_plan=parsed_plan,
            )
        except Exception as e:
            return render(request, "build_round.html", {"active": "build", "flash": str(e), "flash_error": True, "result": None, "drives": drives})

        result = {
            "id": round_.id,
            "kind": "coding",
            "coding_question_count": round_.coding_question_count,
            "duration_minutes": round_.duration_minutes,
            "section_plan": parsed_plan,
            "duration_was_auto": duration_minutes.strip() == "",
        }
        return render(request, "build_round.html", {"active": "build", "flash": None, "flash_error": False, "result": result, "drives": drives})

    if round_type == "technical_discussion":
        if not existing_drive_id.strip():
            return render(request, "build_round.html", {"active": "build", "flash": "Pick an existing drive - Technical Discussion always attaches to a drive that already has a scored round to promote candidates from.", "flash_error": True, "result": None, "drives": drives})

        try:
            round_ = build_technical_discussion_round(session, int(existing_drive_id), count)
        except Exception as e:
            return render(request, "build_round.html", {"active": "build", "flash": str(e), "flash_error": True, "result": None, "drives": drives})

        result = {
            "id": round_.id,
            "kind": "technical_discussion",
            "interview_question_count": round_.interview_question_count,
            "drive_name": round_.drive.name,
        }
        return render(request, "build_round.html", {"active": "build", "flash": None, "flash_error": False, "result": result, "drives": drives})

    if not campus.strip() or not drive_name.strip():
        return render(request, "build_round.html", {"active": "build", "flash": "Campus name and Drive name are required.", "flash_error": True, "result": None, "drives": drives})

    final_title = title.strip() or f"{campus} - {round_type.title()} Test"
    topic_list = [t.strip() for t in topics.split(",")] if topics.strip() else None

    try:
        service = forms_service()
        round_ = build_round(
            session, service, campus, drive_name, round_type, count, final_title, topic_list,
            duration_minutes=parsed_duration or 45,
        )
    except Exception as e:
        return render(request, "build_round.html", {"active": "build", "flash": str(e), "flash_error": True, "result": None, "drives": drives})

    result = {
        "id": round_.id,
        "kind": "forms",
        "edit_url": f"https://docs.google.com/forms/d/{round_.form_id}/edit",
        "responder_uri": round_.responder_uri,
        "timer_path": round_.timer_path,
    }
    return render(request, "build_round.html", {"active": "build", "flash": None, "flash_error": False, "result": result, "drives": drives})


@app.get("/candidates")
def candidates_page(request: Request):
    session = SessionLocal()
    flash, err = flash_from_request(request)
    rounds = session.query(Round).order_by(Round.id).all()
    return render(request, "candidates.html", {"active": "candidates", "flash": flash, "flash_error": err, "rounds": rounds})


@app.post("/candidates/upload")
async def candidates_upload(round_id: int = Form(...), file: UploadFile = None):
    session = SessionLocal()
    round_ = session.get(Round, round_id)
    if round_ is None:
        return flash_redirect("/candidates", f"No round with id {round_id}", error=True)

    path = await save_upload(file)
    try:
        created = add_candidates_from_file(session, round_, path)
    except Exception as e:
        return flash_redirect("/candidates", str(e), error=True)
    return flash_redirect("/candidates", f"Added {created} candidate(s) to round #{round_.id}")


@app.get("/invites")
def invites_page(request: Request):
    session = SessionLocal()
    flash, err = flash_from_request(request)
    rounds = session.query(Round).order_by(Round.id).all()
    return render(
        request,
        "invites.html",
        {"active": "invites", "flash": flash, "flash_error": err, "rounds": rounds, "results": None, "bounced": None},
    )


@app.post("/invites/send")
def invites_send(
    request: Request,
    round_id: int = Form(...),
    mode: str = Form(...),
    base_url: str = Form(""),
    seb_template: str = Form(""),
):
    session = SessionLocal()
    round_ = session.get(Round, round_id)
    rounds = session.query(Round).order_by(Round.id).all()
    if round_ is None:
        return render(
            request,
            "invites.html",
            {"active": "invites", "flash": f"No round with id {round_id}", "flash_error": True, "rounds": rounds, "results": None, "bounced": None},
        )

    try:
        results = send_invites(
            session,
            round_,
            base_url=base_url.strip() or None,
            seb_template_path=seb_template.strip() or None,
            dry_run=(mode != "send"),
        )
    except Exception as e:
        return render(
            request,
            "invites.html",
            {"active": "invites", "flash": str(e), "flash_error": True, "rounds": rounds, "results": None, "bounced": None},
        )

    return render(
        request,
        "invites.html",
        {"active": "invites", "flash": None, "flash_error": False, "rounds": rounds, "results": results, "bounced": None},
    )


@app.post("/invites/check-bounces")
def invites_check_bounces(request: Request, round_id: int = Form(...)):
    session = SessionLocal()
    round_ = session.get(Round, round_id)
    rounds = session.query(Round).order_by(Round.id).all()
    if round_ is None:
        return render(
            request,
            "invites.html",
            {"active": "invites", "flash": f"No round with id {round_id}", "flash_error": True, "rounds": rounds, "results": None, "bounced": None},
        )

    attempts = session.query(Attempt).filter_by(round_id=round_.id).all()
    emails = [session.get(Candidate, a.candidate_id).email for a in attempts]
    try:
        bounced = detect_bounces(gmail_service(), emails)
    except Exception as e:
        return render(
            request,
            "invites.html",
            {"active": "invites", "flash": str(e), "flash_error": True, "rounds": rounds, "results": None, "bounced": None},
        )

    return render(
        request,
        "invites.html",
        {"active": "invites", "flash": None, "flash_error": False, "rounds": rounds, "results": None, "bounced": bounced},
    )


def _results_context(session, round_id: int | None, status_filter: str | None):
    rounds = session.query(Round).order_by(Round.id).all()
    round_ = session.get(Round, round_id) if round_id else None
    kpis = kpi_summary(session, round_) if round_ else None
    attempts = filter_attempts(session, round_, status_filter) if round_ else []
    coding_analytics = (
        coding_question_analytics(session, round_) if round_ and round_.round_type == "coding" else None
    )
    return {
        "active": "results",
        "flash": None,
        "flash_error": False,
        "rounds": rounds,
        "round_": round_,
        "kpis": kpis,
        "attempts": attempts,
        "status_filter": status_filter,
        "bench_pct": None,
        "borderline_pct": None,
        "shortlist_bands": None,
        "top_n_value": None,
        "top_n_results": None,
        "coding_analytics": coding_analytics,
    }


@app.get("/results")
def results_page(request: Request, round_id: int | None = None, status: str | None = None):
    session = SessionLocal()
    ctx = _results_context(session, round_id, status)
    flash, err = flash_from_request(request)
    ctx["flash"], ctx["flash_error"] = flash, err
    return render(request, "results.html", ctx)


@app.post("/results/process")
def results_process(request: Request, round_id: int = Form(...)):
    session = SessionLocal()
    round_ = session.get(Round, round_id)
    ctx = _results_context(session, round_id, None)
    if round_ is None:
        ctx["flash"], ctx["flash_error"] = f"No round with id {round_id}", True
        return render(request, "results.html", ctx)

    if round_.round_type == "coding":
        ctx = _results_context(session, round_id, None)
        ctx["flash"] = "Coding round scores are written live as candidates submit - nothing to pull."
        return render(request, "results.html", ctx)

    try:
        summary = ingest_results(session, round_, forms_service())
    except Exception as e:
        ctx["flash"], ctx["flash_error"] = str(e), True
        return render(request, "results.html", ctx)

    ctx = _results_context(session, round_id, None)
    ctx["flash"] = (
        f"Pulled {summary['form_responses']} response(s), "
        f"matched {summary['matched_to_roster']} to the roster."
    )
    return render(request, "results.html", ctx)


@app.post("/results/shortlist")
def results_shortlist(
    request: Request,
    round_id: int = Form(...),
    bench_pct: int = Form(...),
    borderline_pct: int = Form(...),
):
    session = SessionLocal()
    round_ = session.get(Round, round_id)
    ctx = _results_context(session, round_id, None)
    if round_ is None:
        ctx["flash"], ctx["flash_error"] = f"No round with id {round_id}", True
        return render(request, "results.html", ctx)

    ctx["shortlist_bands"] = shortlist(session, round_, bench_pct, borderline_pct)
    ctx["bench_pct"] = bench_pct
    ctx["borderline_pct"] = borderline_pct
    return render(request, "results.html", ctx)


@app.post("/results/top-n")
def results_top_n(request: Request, round_id: int = Form(...), n: int = Form(...)):
    session = SessionLocal()
    round_ = session.get(Round, round_id)
    ctx = _results_context(session, round_id, None)
    if round_ is None:
        ctx["flash"], ctx["flash_error"] = f"No round with id {round_id}", True
        return render(request, "results.html", ctx)

    ctx["top_n_results"] = top_n_attempts(session, round_, n)
    ctx["top_n_value"] = n
    return render(request, "results.html", ctx)


def _previous_round_scores(session, candidate: Candidate, drive_id: int, exclude_round_id: int) -> list[dict]:
    """Every other round this candidate has an attempt in, for the same
    drive - shown to the interviewer as track-record context."""
    attempts = (
        session.query(Attempt)
        .join(Round, Attempt.round_id == Round.id)
        .filter(Attempt.candidate_id == candidate.id, Round.drive_id == drive_id, Round.id != exclude_round_id)
        .order_by(Round.id)
        .all()
    )
    out = []
    for a in attempts:
        round_ = session.get(Round, a.round_id)
        review_url = None
        if a.status == "submitted":
            if round_.round_type == "coding":
                review_url = f"/results/coding-review/{a.id}?embed=1"
            elif round_.round_type in ("aptitude", "programming"):
                review_url = f"/results/mcq-review/{a.id}?embed=1"
        out.append({
            "round_type": round_.round_type,
            "status": a.status,
            "score": a.score,
            "max_score": a.max_score,
            "percent": a.percent,
            "band": a.band,
            "review_url": review_url,
        })
    return out


@app.get("/technical-discussion")
def technical_discussion_page(request: Request, round_id: int | None = None):
    session = SessionLocal()
    flash, err = flash_from_request(request)
    rounds = session.query(Round).filter_by(round_type="technical_discussion").order_by(Round.id).all()
    round_ = session.get(Round, round_id) if round_id else None

    source_rounds, attempts_view = [], []
    if round_ is not None:
        source_rounds = (
            session.query(Round)
            .filter(Round.drive_id == round_.drive_id, Round.round_type != "technical_discussion")
            .order_by(Round.id)
            .all()
        )
        attempts = session.query(Attempt).filter_by(round_id=round_.id).order_by(Attempt.id).all()
        for a in attempts:
            candidate = session.get(Candidate, a.candidate_id)
            attempts_view.append({
                "attempt": a,
                "candidate": candidate,
                "interview_url": f"/interview/{a.token}",
            })

    return render(
        request,
        "technical_discussion.html",
        {
            "active": "technical_discussion", "flash": flash, "flash_error": err,
            "rounds": rounds, "round_": round_, "source_rounds": source_rounds, "attempts_view": attempts_view,
        },
    )


@app.post("/technical-discussion/promote")
def technical_discussion_promote(
    request: Request,
    target_round_id: int = Form(...),
    source_round_id: int = Form(...),
    band: str = Form("shortlisted"),
):
    session = SessionLocal()
    target = session.get(Round, target_round_id)
    source = session.get(Round, source_round_id)
    if target is None or source is None:
        return flash_redirect("/technical-discussion", "Round not found", error=True)

    count = promote_shortlisted(session, source, target, band=band)
    return flash_redirect(
        f"/technical-discussion?round_id={target_round_id}",
        f"Promoted {count} candidate(s) from round #{source_round_id} ({band}) into this Technical Discussion round.",
    )


@app.post("/technical-discussion/override-decision")
def technical_discussion_override(
    request: Request,
    attempt_id: int = Form(...),
    decision: str = Form(...),
    admin_name: str = Form(...),
    round_id: int = Form(...),
):
    session = SessionLocal()
    attempt = session.get(Attempt, attempt_id)
    if attempt is None:
        return flash_redirect(f"/technical-discussion?round_id={round_id}", "Attempt not found", error=True)

    attempt.decision = decision
    attempt.decision_by = f"{admin_name} (override)"
    attempt.decision_at = datetime.now(timezone.utc).isoformat()
    session.commit()
    return flash_redirect(f"/technical-discussion?round_id={round_id}", f"Decision updated to '{decision}'.")


@app.get("/interview/{token}")
def interview_session_page(request: Request, token: str):
    session = SessionLocal()
    attempt = session.query(Attempt).filter_by(token=token).first()
    if attempt is None:
        return Response("Invalid interview link.", status_code=404)
    round_ = session.get(Round, attempt.round_id)
    if round_ is None or round_.round_type != "technical_discussion":
        return Response("This link is not a Technical Discussion session.", status_code=404)
    candidate = session.get(Candidate, attempt.candidate_id)

    assigned = assign_interview_questions(session, attempt, round_.interview_question_count)
    rows = (
        session.query(InterviewAttemptQuestion)
        .filter_by(attempt_id=attempt.id)
        .order_by(InterviewAttemptQuestion.assigned_order)
        .all()
    )
    questions = []
    for row in rows:
        q = session.get(InterviewQuestion, row.question_id)
        questions.append({
            "attempt_question_id": row.id,
            "area": q.area,
            "question": q.question,
            "rubric_guide": q.rubric_guide,
            "max_score": q.max_score,
            "score": row.score,
            "notes": row.notes or "",
        })

    return render(
        request,
        "interview_session.html",
        {
            "active": "technical_discussion",
            "token": token,
            "candidate": candidate,
            "round_": round_,
            "questions": questions,
            "previous_scores": _previous_round_scores(session, candidate, round_.drive_id, round_.id),
            "decision": attempt.decision,
            "interviewer_name": attempt.decision_by or "",
        },
    )


@app.post("/interview/{token}/submit")
async def interview_session_submit(request: Request, token: str):
    session = SessionLocal()
    attempt = session.query(Attempt).filter_by(token=token).first()
    if attempt is None:
        return Response("Invalid interview link.", status_code=404)
    round_ = session.get(Round, attempt.round_id)
    if round_ is None or round_.round_type != "technical_discussion":
        return Response("This link is not a Technical Discussion session.", status_code=404)

    form = await request.form()
    rows = session.query(InterviewAttemptQuestion).filter_by(attempt_id=attempt.id).all()

    total_score, total_max = 0, 0
    for row in rows:
        q = session.get(InterviewQuestion, row.question_id)
        raw_score = form.get(f"score_{row.id}")
        score = int(raw_score) if raw_score else 0
        score = max(0, min(score, q.max_score))
        row.score = score
        row.notes = form.get(f"notes_{row.id}", "")
        total_score += score
        total_max += q.max_score

    attempt.score = total_score
    attempt.max_score = total_max
    attempt.percent = round(100 * total_score / total_max) if total_max else 0
    attempt.status = "submitted"
    attempt.decision = form.get("decision", "hold")
    attempt.decision_by = form.get("interviewer_name", "").strip() or "Unknown interviewer"
    attempt.decision_at = datetime.now(timezone.utc).isoformat()
    session.commit()

    return flash_redirect(
        f"/technical-discussion?round_id={round_.id}",
        f"Recorded technical discussion for this candidate - decision: {attempt.decision}.",
    )


@app.get("/results/coding-review/{attempt_id}")
def coding_review_page(request: Request, attempt_id: int, embed: bool = False):
    session = SessionLocal()
    attempt = session.get(Attempt, attempt_id)
    if attempt is None or attempt.round.round_type != "coding":
        return Response("Not a coding-round attempt.", status_code=404)

    candidate = session.get(Candidate, attempt.candidate_id)
    rows = (
        session.query(CodingAttemptQuestion)
        .filter_by(attempt_id=attempt.id)
        .order_by(CodingAttemptQuestion.assigned_order)
        .all()
    )
    questions = []
    for row in rows:
        q = session.get(CodingQuestion, row.question_id)
        questions.append({
            "title": q.title,
            "topic": q.topic,
            "points": q.points,
            "best_score": row.best_score,
            "status": row.status,
            "submitted_code": row.last_submitted_code,
            "submitted_at": row.submitted_at,
        })

    return render(
        request,
        "coding_review.html",
        {"active": "results", "attempt": attempt, "candidate": candidate, "round_": attempt.round, "questions": questions, "embed": embed},
    )


@app.get("/results/mcq-review/{attempt_id}")
def mcq_review_page(request: Request, attempt_id: int, embed: bool = False):
    session = SessionLocal()
    attempt = session.get(Attempt, attempt_id)
    if attempt is None or attempt.round.round_type not in ("aptitude", "programming"):
        return Response("Not an MCQ-round attempt.", status_code=404)

    candidate = session.get(Candidate, attempt.candidate_id)
    answers = session.query(FormAnswer).filter_by(attempt_id=attempt.id).order_by(FormAnswer.id).all()

    return render(
        request,
        "mcq_review.html",
        {"active": "results", "attempt": attempt, "candidate": candidate, "round_": attempt.round, "answers": answers, "embed": embed},
    )


@app.get("/final-conclusion")
def final_conclusion_page(request: Request, round_id: int | None = None):
    session = SessionLocal()
    rounds = session.query(Round).filter_by(round_type="technical_discussion").order_by(Round.id).all()
    round_ = session.get(Round, round_id) if round_id else None

    selected = []
    if round_ is not None:
        attempts = session.query(Attempt).filter_by(round_id=round_.id, decision="selected").order_by(Attempt.id).all()
        for a in attempts:
            candidate = session.get(Candidate, a.candidate_id)
            selected.append({"candidate": candidate, "attempt": a})

    return render(
        request,
        "final_conclusion.html",
        {"active": "final_conclusion", "rounds": rounds, "round_": round_, "selected": selected},
    )


@app.get("/final-conclusion/pdf")
def final_conclusion_pdf(round_id: int):
    session = SessionLocal()
    round_ = session.get(Round, round_id)
    if round_ is None:
        return Response("Round not found", status_code=404)

    attempts = session.query(Attempt).filter_by(round_id=round_.id, decision="selected").order_by(Attempt.id).all()
    rows = []
    for a in attempts:
        candidate = session.get(Candidate, a.candidate_id)
        decided = a.decision_at.split("T")[0] if a.decision_at else None
        rows.append({"name": candidate.name, "email": candidate.email, "decision_at": decided})

    pdf_bytes = generate_final_conclusion_pdf(rows, round_.drive.name)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="final-conclusion-round-{round_id}.pdf"'},
    )


if __name__ == "__main__":
    print("Aizentify Campus Console running at http://127.0.0.1:8787")
    uvicorn.run(app, host="127.0.0.1", port=8787)
