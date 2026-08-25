"""
Local web UI for the campus test system, styled with Aizentify branding.
Wraps the same functions the CLI scripts and console.py use, so every
interface stays in sync. Listens on every interface, but LAN access is
closed by default - see lan_access_gate() below and the Network access
section on the Admin page to open it up temporarily.

Usage:
    python webui.py
    -> open http://127.0.0.1:8787
"""

import hashlib
import io
import plistlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote, unquote

import httpx
import uvicorn
from fastapi import Depends, FastAPI, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from openpyxl import Workbook

from add_candidates import add_candidates_from_file
from admin_tools import create_backup, list_backups, restore_backup, wipe_question_banks, wipe_scope
from build_form import build_coding_round, build_round, build_technical_discussion_round, promote_shortlisted
from final_conclusion_pdf import generate_final_conclusion_pdf
from google_auth import forms_service, gmail_service
from interview_session import assign_interview_questions
from invite import send_invites
from load_coding_questions import clear_bank as clear_coding_bank, load_question_file
from load_interview_questions import clear_bank as clear_interview_bank, load_question_file as load_interview_question_file
from load_questions import load_bank
from models import (
    Attempt, Candidate, CodingAttemptQuestion, CodingQuestion, Drive, FormAnswer, InterviewAttemptQuestion,
    InterviewQuestion, Question, Round, Settings, SessionLocal, init_db,
)
from proc_utils import MONITOR_TOKEN_FILE, get_lan_ip
from seb_config import SEB_TEMPLATE_DIR
from results import (
    coding_question_analytics, detect_bounces, filter_attempts, ingest_results, kpi_summary, list_drives,
    round_label, rounds_for_drive, shortlist, top_n_attempts,
)

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

init_db()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

LOCALHOST_CLIENTS = {"127.0.0.1", "::1", "testclient"}  # "testclient" = starlette's TestClient
UNLOCK_COOKIE = "lan_unlock"
ALWAYS_ALLOWED_PREFIXES = ("/static/", "/network/unlock")

# The two physical SEB template files invite.py's seb_attach/seb_download
# modes resolve by round type (see seb_config.SEB_TEMPLATES_BY_ROUND_TYPE) -
# aptitude/programming share "forms", coding gets its own stricter one.
SEB_SLOTS = {"forms": "Aptitude / Programming", "coding": "Coding"}


def get_or_create_settings(session) -> Settings:
    settings = session.get(Settings, 1)
    if settings is None:
        settings = Settings(id=1, lan_access_enabled=False, access_code_hash=None)
        session.add(settings)
        session.commit()
    return settings


def hash_code(code: str) -> str:
    return hashlib.sha256(code.strip().encode("utf-8")).hexdigest()


@app.middleware("http")
async def lan_access_gate(request: Request, call_next):
    """Loopback requests (the admin sitting at this machine) always pass
    straight through. Everything else - i.e. every request that only
    reaches this process because WEBUI_HOST=0.0.0.0 exposed it to the LAN -
    is blocked unless an admin has explicitly turned LAN access on AND the
    visitor has entered the current access code (checked via a cookie
    holding the code's hash, so changing the code invalidates old cookies
    automatically without any extra bookkeeping)."""
    client_host = request.client.host if request.client else None
    if client_host in LOCALHOST_CLIENTS:
        return await call_next(request)

    path = request.url.path
    session = SessionLocal()
    try:
        settings = get_or_create_settings(session)
        if not settings.lan_access_enabled:
            return Response("LAN access is currently disabled by the admin.", status_code=403)
        if path.startswith(ALWAYS_ALLOWED_PREFIXES):
            return await call_next(request)
        if settings.access_code_hash and request.cookies.get(UNLOCK_COOKIE) == settings.access_code_hash:
            return await call_next(request)
        return RedirectResponse(url=f"/network/unlock?next={quote(path)}")
    finally:
        session.close()


@app.get("/network/unlock")
def network_unlock_page(next: str = "/"):
    return HTMLResponse(f"""
    <html><head><title>Enter access code</title></head>
    <body style="font-family: sans-serif; max-width: 400px; margin: 80px auto; text-align: center;">
      <h2>Campus Test Console</h2>
      <p>Ask the admin for the LAN access code.</p>
      <form action="/network/unlock" method="post">
        <input type="hidden" name="next" value="{next}">
        <input type="password" name="code" placeholder="Access code" autofocus
               style="padding:10px; font-size:16px; width:100%; box-sizing:border-box;">
        <button type="submit" style="margin-top:12px; padding:10px 20px; font-size:16px;">Enter</button>
      </form>
    </body></html>
    """)


@app.post("/network/unlock")
def network_unlock_submit(code: str = Form(...), next: str = Form("/")):
    session = SessionLocal()
    try:
        settings = get_or_create_settings(session)
        if not settings.access_code_hash or hash_code(code) != settings.access_code_hash:
            return HTMLResponse(
                '<p style="font-family:sans-serif; text-align:center; margin-top:80px;">'
                'Wrong code. <a href="javascript:history.back()">Try again</a></p>',
                status_code=403,
            )
        response = RedirectResponse(url=next or "/", status_code=303)
        response.set_cookie(UNLOCK_COOKIE, settings.access_code_hash, max_age=60 * 60 * 24 * 7, httponly=True)
        return response
    finally:
        session.close()


def get_session():
    # Every route used to call SessionLocal() directly and never close it,
    # leaking a pooled connection per request - with a default pool of 5 +
    # 10 overflow, that exhausts after ~15 requests and every request after
    # that queues for up to 30s before timing out. Routes now take this as
    # a dependency instead, which guarantees close() via the finally block
    # no matter which of a handler's return points is hit.
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


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
def home(request: Request, session=Depends(get_session)):
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
def bank_page(request: Request, session=Depends(get_session)):
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
            "interview_question_count": session.query(InterviewQuestion).count(),
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
async def bank_upload_coding(files: list[UploadFile], replace: bool = Form(False), session=Depends(get_session)):
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


@app.post("/bank/upload-interview")
async def bank_upload_interview(files: list[UploadFile], replace: bool = Form(False), session=Depends(get_session)):
    loaded = []
    try:
        cleared = clear_interview_bank(session) if replace else 0
        for file in files:
            path = await save_upload(file)
            loaded.append(load_interview_question_file(session, Path(path)))
        session.commit()
    except Exception as e:
        session.rollback()
        return flash_redirect("/bank", str(e), error=True)
    prefix = f"Cleared {cleared} existing question(s). " if replace else ""
    return flash_redirect("/bank", f"{prefix}Loaded {len(loaded)} interview question(s): {', '.join(loaded)}")


@app.get("/rounds/new")
def build_round_page(request: Request, session=Depends(get_session)):
    flash, err = flash_from_request(request)
    drives = session.query(Drive).order_by(Drive.name).all()
    return render(request, "build_round.html", {"active": "build", "flash": flash, "flash_error": err, "result": None, "drives": drives})


@app.post("/rounds/new")
def build_round_submit(
    request: Request,
    round_type: str = Form(...),
    count: int = Form(...),
    drive_mode: str = Form("new"),
    campus: str = Form(""),
    drive_name: str = Form(""),
    existing_drive_id: str = Form(""),
    title: str = Form(""),
    topics: str = Form(""),
    duration_minutes: str = Form(""),
    section_plan: str = Form(""),
    session=Depends(get_session),
):
    parsed_duration = int(duration_minutes) if duration_minutes.strip() else None
    drives = session.query(Drive).order_by(Drive.name).all()

    # Technical Discussion always forces "existing drive" mode client-side
    # (its toggle is hidden), regardless of the drive_mode radio's stale
    # default value. For every other round type, drive_mode is the single
    # source of truth for whether to use existing_drive_id - if the admin is
    # in "new drive" mode, existing_drive_id is ignored even if a stale
    # value is present (e.g. left over from an earlier "existing drive"
    # selection in the same page load), so a leftover hidden-field value can
    # never silently attach a new round to the wrong drive.
    effective_mode = "existing" if round_type == "technical_discussion" else drive_mode
    parsed_drive_id = int(existing_drive_id) if effective_mode == "existing" and existing_drive_id.strip() else None
    if round_type != "technical_discussion" and parsed_drive_id is None and (not campus.strip() or not drive_name.strip()):
        return render(request, "build_round.html", {"active": "build", "flash": "Pick an existing drive, or enter a Campus name and Drive name to create a new one.", "flash_error": True, "result": None, "drives": drives})

    if round_type == "coding":
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
                session, campus or None, drive_name or None, count,
                duration_minutes=parsed_duration, section_plan=parsed_plan, drive_id=parsed_drive_id,
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
        if parsed_drive_id is None:
            return render(request, "build_round.html", {"active": "build", "flash": "Pick an existing drive - Technical Discussion always attaches to a drive that already has a scored round to promote candidates from.", "flash_error": True, "result": None, "drives": drives})

        try:
            round_ = build_technical_discussion_round(session, parsed_drive_id, count)
        except Exception as e:
            return render(request, "build_round.html", {"active": "build", "flash": str(e), "flash_error": True, "result": None, "drives": drives})

        result = {
            "id": round_.id,
            "kind": "technical_discussion",
            "interview_question_count": round_.interview_question_count,
            "drive_name": round_.drive.name,
        }
        return render(request, "build_round.html", {"active": "build", "flash": None, "flash_error": False, "result": result, "drives": drives})

    title_campus = campus.strip() or next((d.campus for d in drives if d.id == parsed_drive_id), "")
    final_title = title.strip() or f"{title_campus} - {round_type.title()} Test"
    topic_list = [t.strip() for t in topics.split(",")] if topics.strip() else None

    try:
        service = forms_service()
        round_ = build_round(
            session, service, campus or None, drive_name or None, round_type, count, final_title, topic_list,
            duration_minutes=parsed_duration or 45, drive_id=parsed_drive_id,
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
def candidates_page(request: Request, drive_id: int | None = None, session=Depends(get_session)):
    flash, err = flash_from_request(request)
    drives = list_drives(session)
    drive_ = session.get(Drive, drive_id) if drive_id else None
    rounds = rounds_for_drive(session, drive_id) if drive_ else []
    return render(request, "candidates.html", {
        "active": "candidates", "flash": flash, "flash_error": err,
        "drives": drives, "drive_": drive_, "rounds": rounds, "round_label": round_label,
    })


@app.get("/candidates/template.xlsx")
def candidates_template():
    wb = Workbook()
    ws = wb.active
    ws.title = "Candidates"
    ws.append([
        "Name", "Email", "Reg No.", "Gender", "Degree", "Stream",
        "Resume", "GitHub Profile URL", "Portfolio URL",
    ])
    ws.append([
        "Jane Doe", "jane.doe@gmail.com", "REG123", "Female", "BTECH",
        "Computer Science and Engineering",
        "https://drive.google.com/...", "https://github.com/janedoe", "https://janedoe.dev",
    ])
    for col, width in zip("ABCDEFGHI", (20, 26, 14, 10, 10, 32, 34, 30, 26)):
        ws.column_dimensions[col].width = width

    buf = io.BytesIO()
    wb.save(buf)
    return Response(
        content=buf.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="candidates-template.xlsx"'},
    )


@app.post("/candidates/upload")
async def candidates_upload(round_id: int = Form(...), file: UploadFile = None, session=Depends(get_session)):
    round_ = session.get(Round, round_id)
    if round_ is None:
        return flash_redirect("/candidates", f"No round with id {round_id}", error=True)

    back_url = f"/candidates?drive_id={round_.drive_id}"
    path = await save_upload(file)
    try:
        created, already_invited = add_candidates_from_file(session, round_, path)
    except Exception as e:
        return flash_redirect(back_url, str(e), error=True)
    msg = f"Added {created} new candidate(s) to round #{round_.id}"
    if already_invited:
        msg += f" ({already_invited} already invited to this round - no duplicate invite created, profile data refreshed)"
    return flash_redirect(back_url, msg)


def _invites_context(session, drive_id: int | None):
    drives = list_drives(session)
    drive_ = session.get(Drive, drive_id) if drive_id else None
    rounds = rounds_for_drive(session, drive_id) if drive_ else []
    return {
        "active": "invites", "flash": None, "flash_error": False,
        "drives": drives, "drive_": drive_, "rounds": rounds, "round_label": round_label,
        "results": None, "bounced": None,
    }


@app.get("/invites")
def invites_page(request: Request, drive_id: int | None = None, session=Depends(get_session)):
    flash, err = flash_from_request(request)
    ctx = _invites_context(session, drive_id)
    ctx["flash"], ctx["flash_error"] = flash, err
    return render(request, "invites.html", ctx)


@app.post("/invites/send")
def invites_send(
    request: Request,
    drive_id: int = Form(...),
    round_id: int = Form(...),
    mode: str = Form(...),
    base_url: str = Form(""),
    delivery_mode: str = Form("direct"),
    seb_template: str = Form(""),
    session=Depends(get_session),
):
    round_ = session.get(Round, round_id)
    ctx = _invites_context(session, drive_id)
    if round_ is None:
        ctx["flash"], ctx["flash_error"] = f"No round with id {round_id}", True
        return render(request, "invites.html", ctx)

    try:
        results = send_invites(
            session,
            round_,
            base_url=base_url.strip() or None,
            delivery_mode=delivery_mode,
            seb_template_path=seb_template.strip() or None,
            dry_run=(mode != "send"),
        )
    except Exception as e:
        ctx["flash"], ctx["flash_error"] = str(e), True
        return render(request, "invites.html", ctx)

    ctx["results"] = results
    return render(request, "invites.html", ctx)


@app.post("/invites/check-bounces")
def invites_check_bounces(request: Request, drive_id: int = Form(...), round_id: int = Form(...), session=Depends(get_session)):
    round_ = session.get(Round, round_id)
    ctx = _invites_context(session, drive_id)
    if round_ is None:
        ctx["flash"], ctx["flash_error"] = f"No round with id {round_id}", True
        return render(request, "invites.html", ctx)

    attempts = session.query(Attempt).filter_by(round_id=round_.id).all()
    emails = [session.get(Candidate, a.candidate_id).email for a in attempts]
    try:
        bounced = detect_bounces(gmail_service(), emails)
    except Exception as e:
        ctx["flash"], ctx["flash_error"] = str(e), True
        return render(request, "invites.html", ctx)

    ctx["bounced"] = bounced
    return render(request, "invites.html", ctx)


def _results_context(session, drive_id: int | None, round_id: int | None, status_filter: str | None):
    drives = list_drives(session)
    drive_ = session.get(Drive, drive_id) if drive_id else None
    # A link can arrive with just round_id and no drive_id (e.g. "back to
    # Results" from the coding/MCQ review pages) - resolve drive_ from the
    # round in that case too, so every form on the page still gets a real
    # drive_id instead of silently rendering an empty hidden field that
    # 422s on submit.
    round_ = session.get(Round, round_id) if round_id else None
    if round_ and drive_ is None:
        drive_ = round_.drive
    rounds = rounds_for_drive(session, drive_.id) if drive_ else []
    # default to the first round in the drive so picking a drive shows
    # something immediately, without a required second click into a tab
    if round_ is None:
        round_ = rounds[0] if rounds else None
    kpis = kpi_summary(session, round_) if round_ else None
    attempts = filter_attempts(session, round_, status_filter) if round_ else []
    coding_analytics = (
        coding_question_analytics(session, round_) if round_ and round_.round_type == "coding" else None
    )
    return {
        "active": "results",
        "flash": None,
        "flash_error": False,
        "drives": drives,
        "drive_": drive_,
        "rounds": rounds,
        "round_": round_,
        "round_label": round_label,
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
def results_page(request: Request, drive_id: int | None = None, round_id: int | None = None, status: str | None = None, session=Depends(get_session)):
    ctx = _results_context(session, drive_id, round_id, status)
    flash, err = flash_from_request(request)
    ctx["flash"], ctx["flash_error"] = flash, err
    return render(request, "results.html", ctx)


@app.post("/results/process")
def results_process(request: Request, drive_id: int = Form(...), round_id: int = Form(...), session=Depends(get_session)):
    round_ = session.get(Round, round_id)
    ctx = _results_context(session, drive_id, round_id, None)
    if round_ is None:
        ctx["flash"], ctx["flash_error"] = f"No round with id {round_id}", True
        return render(request, "results.html", ctx)

    if round_.round_type == "coding":
        ctx["flash"] = "Coding round scores are written live as candidates submit - nothing to pull."
        return render(request, "results.html", ctx)

    try:
        summary = ingest_results(session, round_, forms_service())
    except Exception as e:
        ctx["flash"], ctx["flash_error"] = str(e), True
        return render(request, "results.html", ctx)

    ctx = _results_context(session, drive_id, round_id, None)
    ctx["flash"] = (
        f"Pulled {summary['form_responses']} response(s), "
        f"matched {summary['matched_to_roster']} to the roster."
    )
    if summary["flagged_unstarted"]:
        ctx["flash"] += (
            f" {summary['flagged_unstarted']} response(s) matched a candidate's email but that candidate's "
            f"own invite link was never opened - not credited, needs manual review."
        )
        ctx["flash_error"] = True
    return render(request, "results.html", ctx)


@app.post("/results/shortlist")
def results_shortlist(
    request: Request,
    drive_id: int = Form(...),
    round_id: int = Form(...),
    bench_pct: int = Form(...),
    borderline_pct: int = Form(...),
    session=Depends(get_session),
):
    round_ = session.get(Round, round_id)
    ctx = _results_context(session, drive_id, round_id, None)
    if round_ is None:
        ctx["flash"], ctx["flash_error"] = f"No round with id {round_id}", True
        return render(request, "results.html", ctx)

    ctx["shortlist_bands"] = shortlist(session, round_, bench_pct, borderline_pct)
    ctx["bench_pct"] = bench_pct
    ctx["borderline_pct"] = borderline_pct
    return render(request, "results.html", ctx)


@app.post("/results/top-n")
def results_top_n(request: Request, drive_id: int = Form(...), round_id: int = Form(...), n: int = Form(...), session=Depends(get_session)):
    round_ = session.get(Round, round_id)
    ctx = _results_context(session, drive_id, round_id, None)
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
def technical_discussion_page(request: Request, drive_id: int | None = None, round_id: int | None = None, session=Depends(get_session)):
    flash, err = flash_from_request(request)
    drives = list_drives(session)
    drive_ = session.get(Drive, drive_id) if drive_id else None
    rounds = [r for r in rounds_for_drive(session, drive_id) if r.round_type == "technical_discussion"] if drive_ else []
    round_ = session.get(Round, round_id) if round_id else (rounds[0] if rounds else None)

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
            "drives": drives, "drive_": drive_, "rounds": rounds, "round_": round_, "round_label": round_label,
            "source_rounds": source_rounds, "attempts_view": attempts_view,
        },
    )


@app.post("/technical-discussion/promote")
def technical_discussion_promote(
    request: Request,
    target_round_id: int = Form(...),
    source_round_id: int = Form(...),
    band: str = Form("shortlisted"),
    session=Depends(get_session),
):
    target = session.get(Round, target_round_id)
    source = session.get(Round, source_round_id)
    if target is None or source is None:
        return flash_redirect("/technical-discussion", "Round not found", error=True)

    count = promote_shortlisted(session, source, target, band=band)
    return flash_redirect(
        f"/technical-discussion?drive_id={target.drive_id}&round_id={target_round_id}",
        f"Promoted {count} candidate(s) from round #{source_round_id} ({band}) into this Technical Discussion round.",
    )


@app.post("/technical-discussion/override-decision")
def technical_discussion_override(
    request: Request,
    attempt_id: int = Form(...),
    decision: str = Form(...),
    admin_name: str = Form(...),
    round_id: int = Form(...),
    session=Depends(get_session),
):
    attempt = session.get(Attempt, attempt_id)
    round_ = session.get(Round, round_id)
    if attempt is None or round_ is None:
        return flash_redirect(f"/technical-discussion?round_id={round_id}", "Attempt or round not found", error=True)

    attempt.decision = decision
    attempt.decision_by = f"{admin_name} (override)"
    attempt.decision_at = datetime.now(timezone.utc).isoformat()
    session.commit()
    return flash_redirect(f"/technical-discussion?drive_id={round_.drive_id}&round_id={round_id}", f"Decision updated to '{decision}'.")


@app.get("/interview/{token}")
def interview_session_page(request: Request, token: str, session=Depends(get_session)):
    attempt = session.query(Attempt).filter_by(token=token).first()
    if attempt is None:
        return Response("Invalid interview link.", status_code=404)
    round_ = session.get(Round, attempt.round_id)
    if round_ is None or round_.round_type != "technical_discussion":
        return Response("This link is not a Technical Discussion session.", status_code=404)
    candidate = session.get(Candidate, attempt.candidate_id)

    try:
        assigned = assign_interview_questions(session, attempt, round_.interview_question_count)
    except ValueError as e:
        return Response(str(e), status_code=400)
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
async def interview_session_submit(request: Request, token: str, session=Depends(get_session)):
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
        f"/technical-discussion?drive_id={round_.drive_id}&round_id={round_.id}",
        f"Recorded technical discussion for this candidate - decision: {attempt.decision}.",
    )


@app.get("/results/coding-review/{attempt_id}")
def coding_review_page(request: Request, attempt_id: int, embed: bool = False, session=Depends(get_session)):
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
def mcq_review_page(request: Request, attempt_id: int, embed: bool = False, session=Depends(get_session)):
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
def final_conclusion_page(request: Request, round_id: int | None = None, session=Depends(get_session)):
    rounds = session.query(Round).filter_by(round_type="technical_discussion").order_by(Round.id).all()
    round_ = session.get(Round, round_id) if round_id else None

    final_list = []
    if round_ is not None:
        # Hold is included alongside Selected - it's the waitlist reference
        # for filling seats if the initially-selected candidates don't all
        # join, so it needs to stay in the same downloadable list, not be
        # dropped from it.
        attempts = (
            session.query(Attempt)
            .filter(Attempt.round_id == round_.id, Attempt.decision.in_(["selected", "hold"]))
            .order_by(Attempt.decision, Attempt.id)
            .all()
        )
        for a in attempts:
            candidate = session.get(Candidate, a.candidate_id)
            final_list.append({"candidate": candidate, "attempt": a})

    return render(
        request,
        "final_conclusion.html",
        {"active": "final_conclusion", "rounds": rounds, "round_": round_, "final_list": final_list},
    )


@app.get("/final-conclusion/pdf")
def final_conclusion_pdf(round_id: int, session=Depends(get_session)):
    round_ = session.get(Round, round_id)
    if round_ is None:
        return Response("Round not found", status_code=404)

    attempts = (
        session.query(Attempt)
        .filter(Attempt.round_id == round_.id, Attempt.decision.in_(["selected", "hold"]))
        .order_by(Attempt.decision, Attempt.id)
        .all()
    )
    rows = []
    for a in attempts:
        candidate = session.get(Candidate, a.candidate_id)
        decided = a.decision_at.split("T")[0] if a.decision_at else None
        rows.append({
            "reg_no": candidate.reg_no or "—",
            "name": candidate.name,
            "gender": candidate.gender or "—",
            "degree": candidate.degree or "—",
            "stream": candidate.stream or "—",
            "email": candidate.email,
            "status": "Selected" if a.decision == "selected" else "Hold",
            "decision_at": decided,
        })

    pdf_bytes = generate_final_conclusion_pdf(rows, round_.drive.campus, round_.drive.name)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="final-conclusion-round-{round_id}.pdf"'},
    )


def _coding_sessions(session) -> dict:
    """Candidates who have opened a coding session - in progress or
    completed - sourced straight from the DB (not app.py), so it's always
    accurate even if app.py's own process is down. In-progress rows are
    shown regardless of age (a stuck/abandoned session is exactly what an
    admin needs to notice); completed rows are capped to the last 24h so
    old drives don't clutter a live view."""
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(hours=24)).isoformat()
    attempts = (
        session.query(Attempt)
        .join(Round, Attempt.round_id == Round.id)
        .filter(
            Round.round_type == "coding",
            Attempt.session_started_at.isnot(None),
            (Attempt.status == "started") | ((Attempt.status == "submitted") & (Attempt.submitted_at >= cutoff)),
        )
        .all()
    )
    rows = []
    for a in attempts:
        round_ = a.round
        candidate = a.candidate
        started = datetime.fromisoformat(a.session_started_at)
        deadline = started + timedelta(minutes=round_.duration_minutes)
        cqs = session.query(CodingAttemptQuestion).filter_by(attempt_id=a.id).all()

        if a.status == "submitted":
            submitted = datetime.fromisoformat(a.submitted_at) if a.submitted_at else None
            on_time = submitted is not None and submitted <= deadline
            flag = "on_time" if on_time else "overdue"
            remaining_s = None
        else:
            remaining_s = (deadline - now).total_seconds()
            flag = "overdue" if remaining_s < 0 else "in_progress"

        rows.append({
            "name": candidate.name,
            "email": candidate.email,
            "drive": f"{round_.drive.campus} / {round_.drive.name}",
            "status": a.status,
            "started_at": a.session_started_at,
            "submitted_at": a.submitted_at,
            "remaining_s": remaining_s,
            "flag": flag,
            # "submitted" = they actually clicked Submit on that question (status
            # passed/partial/failed, submitted_at set) - a bare Run leaves status
            # "attempted" with no submitted_at, so it's deliberately not counted
            # here; that's "opened it" not "handed in an answer".
            "questions_submitted": sum(1 for c in cqs if c.submitted_at is not None),
            "questions_total": len(cqs),
        })
    rows.sort(key=lambda r: r["remaining_s"] if r["remaining_s"] is not None else float("-inf"), reverse=False)
    # in-progress rows (soonest deadline first) ahead of completed rows (most recent first)
    in_progress = sorted((r for r in rows if r["status"] == "started"), key=lambda r: r["remaining_s"])
    completed = sorted((r for r in rows if r["status"] == "submitted"), key=lambda r: r["submitted_at"], reverse=True)
    return {
        "rows": in_progress + completed,
        "kpi": {
            "started": len(rows),
            "in_progress": len(in_progress),
            "completed": len(completed),
        },
    }


def _fetch_system_load() -> dict | None:
    """Proxies app.py's own /monitor-data - reads the per-run token app.py
    wrote to .run/monitor_token.txt at its startup, so nobody has to copy a
    token URL by hand. Returns None if app.py isn't running or hasn't
    started far enough to have written the token yet."""
    if not MONITOR_TOKEN_FILE.exists():
        return None
    token = MONITOR_TOKEN_FILE.read_text().strip()
    if not token:
        return None
    try:
        r = httpx.get(f"http://127.0.0.1:8788/monitor-data/{token}", timeout=2.0)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


@app.get("/live-monitor")
def live_monitor_page(request: Request, session=Depends(get_session)):
    sessions = _coding_sessions(session)
    return render(
        request,
        "live_monitor.html",
        {
            "active": "live_monitor",
            "sessions": sessions["rows"],
            "kpi": sessions["kpi"],
            "system_load": _fetch_system_load(),
        },
    )


@app.get("/live-monitor/data")
def live_monitor_data(session=Depends(get_session)):
    sessions = _coding_sessions(session)
    return JSONResponse({
        "sessions": sessions["rows"],
        "kpi": sessions["kpi"],
        "system_load": _fetch_system_load(),
    })


@app.get("/admin")
def admin_page(request: Request, session=Depends(get_session)):
    flash, err = flash_from_request(request)
    drives = session.query(Drive).order_by(Drive.campus, Drive.name).all()
    campuses = sorted({d.campus for d in drives})
    return render(
        request,
        "admin.html",
        {
            "active": "admin",
            "flash": flash,
            "flash_error": err,
            "drives": drives,
            "campuses": campuses,
            "backups": list_backups(),
            "net_settings": get_or_create_settings(session),
            "lan_ip": get_lan_ip(),
            "seb_slots": SEB_SLOTS,
            "seb_status": {slot: (SEB_TEMPLATE_DIR / f"{slot}.seb").exists() for slot in SEB_SLOTS},
        },
    )


@app.post("/admin/seb-templates/upload")
async def admin_seb_template_upload(slot: str = Form(...), file: UploadFile = None):
    if slot not in SEB_SLOTS:
        return flash_redirect("/admin", "Unknown SEB template slot.", error=True)
    if file is None or not file.filename:
        return flash_redirect("/admin", "Choose a .seb file to upload.", error=True)

    content = await file.read()
    try:
        plistlib.loads(content)
    except Exception:
        return flash_redirect(
            "/admin",
            "That doesn't look like a valid unencrypted .seb file - export as UNENCRYPTED "
            "from the SEB Config Tool (Password protected/encrypted .seb files aren't readable here).",
            error=True,
        )

    SEB_TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    (SEB_TEMPLATE_DIR / f"{slot}.seb").write_bytes(content)
    return flash_redirect("/admin", f"Uploaded {SEB_SLOTS[slot]} SEB template.")


@app.post("/admin/backup")
def admin_backup():
    name = create_backup(label="manual")
    return flash_redirect("/admin", f"Backup created: {name}")


@app.post("/admin/restore")
def admin_restore(filename: str = Form(...)):
    try:
        restore_backup(filename)
    except ValueError as e:
        return flash_redirect("/admin", str(e), error=True)
    return flash_redirect("/admin", f"Restored from {filename}. The pre-restore state was also saved as a backup.")


@app.post("/admin/network/toggle")
def admin_network_toggle(request: Request, enabled: str = Form(""), session=Depends(get_session)):
    # Deliberately not covered by the LAN unlock cookie - only someone at
    # this machine (or already gated out entirely) can flip LAN access,
    # so a guest who has the code can never re-open or further restrict it.
    if request.client.host not in LOCALHOST_CLIENTS:
        return Response("Only available from this machine.", status_code=403)
    settings = get_or_create_settings(session)
    settings.lan_access_enabled = enabled.strip() == "true"
    if settings.lan_access_enabled and not settings.access_code_hash:
        session.commit()
        return flash_redirect("/admin", "Set an access code below before enabling LAN access.", error=True)
    session.commit()
    return flash_redirect("/admin", "LAN access enabled." if settings.lan_access_enabled else "LAN access disabled.")


@app.post("/admin/network/set-code")
def admin_network_set_code(request: Request, code: str = Form(...), session=Depends(get_session)):
    if request.client.host not in LOCALHOST_CLIENTS:
        return Response("Only available from this machine.", status_code=403)
    if not code.strip():
        return flash_redirect("/admin", "Access code can't be blank.", error=True)
    settings = get_or_create_settings(session)
    settings.access_code_hash = hash_code(code)
    session.commit()
    return flash_redirect("/admin", "Access code updated. Anyone previously unlocked will need to re-enter it.")


@app.post("/admin/cleanup")
def admin_cleanup(
    scope: str = Form(...),
    campus: str = Form(""),
    drive_id: str = Form(""),
    confirm_text: str = Form(""),
    clear_banks: str = Form(""),
    session=Depends(get_session),
):
    if confirm_text.strip().upper() != "DELETE":
        return flash_redirect("/admin", "Type DELETE in the confirmation box to proceed.", error=True)

    if scope == "all":
        drive_ids = [d_id for (d_id,) in session.query(Drive.id)]
        label = "everything"
    elif scope == "campus":
        if not campus.strip():
            return flash_redirect("/admin", "Pick a campus.", error=True)
        drive_ids = [d_id for (d_id,) in session.query(Drive.id).filter(Drive.campus == campus)]
        label = f'campus "{campus}"'
    elif scope == "drive":
        if not drive_id.strip():
            return flash_redirect("/admin", "Pick a drive.", error=True)
        drive_ids = [int(drive_id)]
        label = "the selected drive"
    else:
        return flash_redirect("/admin", "Unknown cleanup scope.", error=True)

    also_clear_banks = scope == "all" and clear_banks.strip() == "true"

    if not drive_ids and not also_clear_banks:
        return flash_redirect("/admin", f"Nothing to clean up for {label}.", error=True)

    backup_name = create_backup(label="pre-cleanup")
    counts = wipe_scope(session, drive_ids)
    message = (
        f"Cleaned up {label}: {counts['drives']} drive(s), {counts['rounds']} round(s), "
        f"{counts['candidates']} candidate(s), {counts['attempts']} attempt(s) deleted."
    )
    if also_clear_banks:
        bank_counts = wipe_question_banks(session)
        message += (
            f" Also cleared question banks: {bank_counts['mcq_questions']} MCQ, "
            f"{bank_counts['coding_questions']} coding, {bank_counts['interview_questions']} interview question(s)."
        )
    session.commit()
    message += f" Backup saved as {backup_name} before cleanup."
    return flash_redirect("/admin", message)


if __name__ == "__main__":
    # Always binds to every interface now - lan_access_gate (above) is the
    # actual security boundary, not the socket: non-localhost requests are
    # rejected by default and only get through once an admin enables LAN
    # access AND sets a code from Settings on the Admin page. This lets LAN
    # access be toggled instantly, on whatever network this machine is
    # currently on, without restarting the process.
    print("Aizentify Campus Console running at http://127.0.0.1:8787")
    print("(LAN access is gated by Settings on the Admin page - off by default)")
    uvicorn.run(app, host="0.0.0.0", port=8787)
