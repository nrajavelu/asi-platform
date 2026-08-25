"""
Menu-driven console for the campus test system. Wraps the same functions
the CLI scripts (build_form.py, add_candidates.py, invite.py,
load_questions.py, results.py) use internally, so the menu and the raw
--flag scripts never drift apart.

Usage:
    python console.py
"""

from pathlib import Path

from add_candidates import add_candidates_from_file
from build_form import build_coding_round, build_round, print_coding_round_summary, print_round_summary
from google_auth import forms_service, gmail_service
from invite import send_invites
from load_coding_questions import load_question_file
from load_questions import load_bank
from models import Attempt, Candidate, CodingQuestion, Round, SessionLocal, init_db
from results import coding_question_analytics, detect_bounces, filter_attempts, ingest_results, kpi_summary, shortlist, top_n_attempts


def prompt(msg: str, default: str | None = None) -> str | None:
    suffix = f" [{default}]" if default else ""
    val = input(f"{msg}{suffix}: ").strip()
    return val or default


def list_rounds(session) -> Round | None:
    rounds = session.query(Round).order_by(Round.id).all()
    if not rounds:
        print("No rounds yet. Build one first (option 2).")
        return None
    for r in rounds:
        form_status = "form ready" if r.form_id else "no form"
        print(f"  [{r.id}] {r.drive.name} ({r.drive.campus}) - {r.round_type} - {form_status}")
    choice = prompt("Round id")
    if not choice:
        return None
    round_ = session.get(Round, int(choice))
    if round_ is None:
        print("No such round.")
    return round_


def action_load_bank() -> None:
    path = prompt("Question bank file (.xlsx or .csv)", "question_bank_v1.xlsx")
    count = load_bank(path)
    print(f"Loaded {count} questions from {path}")


def action_load_coding_bank() -> None:
    session = SessionLocal()
    directory = prompt("Coding questions folder (one .json per question)", "coding_questions")
    loaded = []
    for path in sorted(Path(directory).glob("*.json")):
        loaded.append(load_question_file(session, path))
    session.commit()
    print(f"Loaded {len(loaded)} coding question(s): {', '.join(loaded) or '(none found)'}")
    print(f"Total in bank now: {session.query(CodingQuestion).count()}")


def action_build_round() -> None:
    session = SessionLocal()
    campus = prompt("Campus name")
    drive_name = prompt("Drive name")
    round_type = prompt("Round type (aptitude/programming/coding)", "aptitude")

    if round_type == "coding":
        count = int(prompt("Questions per candidate", "2"))
        duration = int(prompt("Duration (minutes)", "45"))
        round_ = build_coding_round(session, campus, drive_name, count, duration_minutes=duration)
        print_coding_round_summary(round_)
        return

    count = int(prompt("Number of questions", "25"))
    title = prompt("Form title", f"{campus} - {round_type.title()} Test")
    topics_raw = prompt("Topics filter, comma-separated (blank = all)", "")
    topics = [t.strip() for t in topics_raw.split(",")] if topics_raw else None
    duration = int(prompt("Duration (minutes)", "45"))

    service = forms_service()
    round_ = build_round(
        session, service, campus, drive_name, round_type, count, title, topics, duration_minutes=duration
    )
    print_round_summary(round_)


def action_upload_candidates() -> None:
    session = SessionLocal()
    round_ = list_rounds(session)
    if round_ is None:
        return
    file_path = prompt("Candidates file (.csv or .xlsx, columns: name,email)")
    created, already_invited = add_candidates_from_file(session, round_, file_path)
    print(f"Created {created} attempt(s) for round #{round_.id}", end="")
    print(f" ({already_invited} already invited - profile data refreshed only)" if already_invited else "")


def action_send_invites() -> None:
    session = SessionLocal()
    round_ = list_rounds(session)
    if round_ is None:
        return
    base_url = prompt("Start-gate URL from app.py (blank = direct form link, no started-tracking)", "")
    mode = prompt("Mode: dry-run or send", "dry-run")
    seb_path = prompt("SEB template path (blank = no proctoring)", "")
    send_invites(
        session, round_, base_url=base_url or None, seb_template_path=seb_path or None, dry_run=(mode != "send")
    )


def action_check_bounces() -> None:
    session = SessionLocal()
    round_ = list_rounds(session)
    if round_ is None:
        return
    attempts = session.query(Attempt).filter_by(round_id=round_.id).all()
    emails = [session.get(Candidate, a.candidate_id).email for a in attempts]
    bounced = detect_bounces(gmail_service(), emails)
    if bounced:
        print(f"\n{len(bounced)} invite(s) likely failed to deliver:")
        for email in bounced:
            print(f"  - {email}")
    else:
        print("No delivery failures found (best-effort check).")


def action_view_results() -> None:
    session = SessionLocal()
    round_ = list_rounds(session)
    if round_ is None:
        return
    kpis = kpi_summary(session, round_)
    print(f"\nInvited: {kpis['invited']}  Started: {kpis['started']}  "
          f"Completed: {kpis['completed']}  Not completed: {kpis['not_completed']}")

    status_filter = prompt("Filter by status (invited/started/submitted, blank = all)", "")
    for a in filter_attempts(session, round_, status_filter or None):
        candidate = session.get(Candidate, a.candidate_id)
        score = f"{a.score}/{a.max_score} ({a.percent}%)" if a.percent is not None else "-"
        print(f"  {candidate.name:<20} {candidate.email:<30} {a.status:<10} {score}")

    if round_.round_type == "coding":
        analytics = coding_question_analytics(session, round_)
        if analytics:
            print("\nPer-question analytics (hardest first):")
            for q in analytics:
                print(
                    f"  {q['title']:<30} passed={q['passed']} partial={q['partial']} "
                    f"failed={q['failed']} attempted_only={q['attempted_only']} "
                    f"not_attempted={q['not_attempted']}  pass_rate={q['pass_rate']}%"
                )


def action_process_results() -> None:
    session = SessionLocal()
    round_ = list_rounds(session)
    if round_ is None:
        return
    if round_.round_type == "coding":
        print("Coding round scores are written live as candidates submit - nothing to pull.")
        return
    summary = ingest_results(session, round_, forms_service())
    print(f"Pulled {summary['form_responses']} response(s), "
          f"matched {summary['matched_to_roster']} to the roster "
          f"(out of {summary['total_attempts']} candidates).")


def action_shortlist() -> None:
    session = SessionLocal()
    round_ = list_rounds(session)
    if round_ is None:
        return
    bench = int(prompt("Shortlist bench %", str(round_.cutoff_high)))
    borderline = int(prompt("Borderline floor %", str(round_.cutoff_low)))
    bands = shortlist(session, round_, bench, borderline)
    for band_name in ["shortlisted", "borderline", "rejected"]:
        attempts = bands[band_name]
        print(f"\n{band_name.upper()} ({len(attempts)}):")
        for a in attempts:
            candidate = session.get(Candidate, a.candidate_id)
            print(f"  {candidate.name:<20} {candidate.email:<30} {a.score}/{a.max_score} ({a.percent}%)")


def action_top_n() -> None:
    session = SessionLocal()
    round_ = list_rounds(session)
    if round_ is None:
        return
    n = int(prompt("Show top N", "10"))
    for rank, a in enumerate(top_n_attempts(session, round_, n), start=1):
        candidate = session.get(Candidate, a.candidate_id)
        print(f"  {rank:>2}. {candidate.name:<20} {candidate.email:<30} {a.score}/{a.max_score} ({a.percent}%)")


MENU: dict[str, tuple[str, "callable | None"]] = {
    "1": ("Load/refresh question bank (aptitude/programming)", action_load_bank),
    "2": ("Load/refresh coding question bank (JSON folder)", action_load_coding_bank),
    "3": ("Build a round (aptitude/programming = Google Form, coding = self-hosted)", action_build_round),
    "4": ("Upload candidate list", action_upload_candidates),
    "5": ("Send invites", action_send_invites),
    "6": ("Check for bounced invites", action_check_bounces),
    "7": ("View results (KPIs + candidate list)", action_view_results),
    "8": ("Process results (pull & score from Forms)", action_process_results),
    "9": ("Shortlist (bench % / borderline %)", action_shortlist),
    "10": ("Top N ranking", action_top_n),
    "11": ("Exit", None),
}


def main() -> None:
    init_db()
    while True:
        print("\n===== Aizentify Campus Test Console =====")
        for key, (label, _) in MENU.items():
            print(f"{key}. {label}")
        choice = input("\nChoose an option: ").strip()

        if choice == "11":
            print("Goodbye.")
            break

        entry = MENU.get(choice)
        if entry is None:
            print("Invalid option.")
            continue

        _, action = entry
        try:
            action()
        except SystemExit as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
