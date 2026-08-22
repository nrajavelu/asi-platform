"""
Builds a Google Forms quiz from the question bank and registers it as a
Round against a Drive.

Usage:
    python build_form.py --campus "XYZ College" --drive-name "Aug 2026 Drive" \
        --round-type aptitude --count 10 --title "XYZ College - Aptitude Test"

Optional:
    --topics quant,logical   (comma-separated filter; default: all topics for the round type)
"""

import argparse
import json
import random
import re

from sqlalchemy import func

from google_auth import forms_service
from make_timer import generate_timer_html, OUT_DIR as TIMER_OUT_DIR
from models import Attempt, Candidate, CodingQuestion, Drive, InterviewQuestion, Question, Round, SessionLocal, init_db

OPTION_FIELDS = ["option_a", "option_b", "option_c", "option_d"]
OPTION_LABELS = ["A", "B", "C", "D"]
LOGO_URL = "https://aizentify.com/assets/img/brand-logo-header.png"


def sanitize_display_text(text: str) -> str:
    """The Forms API rejects newlines in displayed text (item titles,
    option values) with a 400 error - collapse them to a visible separator
    instead of losing the line-break structure entirely."""
    return re.sub(r"\n+", " — ", text.strip())


def get_or_create_drive(session, name: str, campus: str) -> Drive:
    drive = session.query(Drive).filter_by(name=name, campus=campus).first()
    if drive is None:
        drive = Drive(name=name, campus=campus)
        session.add(drive)
        session.commit()
    return drive


def pick_questions(session, round_type: str, count: int, topics: list[str] | None):
    query = session.query(Question).filter(Question.round_type == round_type)
    if topics:
        query = query.filter(Question.topic.in_(topics))
    pool = query.all()
    if len(pool) < count:
        raise SystemExit(
            f"Only {len(pool)} '{round_type}' questions available "
            f"(topics={topics or 'all'}); requested {count}."
        )
    return random.sample(pool, count)


def build_batch_requests(questions: list[Question], round_type: str) -> list[dict]:
    """One question per page: a page break (carrying a running header) goes
    before every question after the first, and the Aizentify logo opens the
    first page."""
    requests = [
        {
            "updateSettings": {
                "settings": {"quizSettings": {"isQuiz": True}},
                "updateMask": "quizSettings.isQuiz",
            }
        },
        {
            "createItem": {
                "item": {
                    "imageItem": {
                        "image": {"sourceUri": LOGO_URL, "altText": "Aizentify"}
                    }
                },
                "location": {"index": 0},
            }
        },
    ]

    total = len(questions)
    index = 1
    for position, q in enumerate(questions, start=1):
        if position > 1:
            requests.append(
                {
                    "createItem": {
                        "item": {
                            "title": f"{round_type.title()} Test — Question {position} of {total}",
                        },
                        "location": {"index": index},
                    }
                }
            )
            requests[-1]["createItem"]["item"]["pageBreakItem"] = {}
            index += 1

        options = [sanitize_display_text(getattr(q, field)) for field in OPTION_FIELDS]
        correct_value = options[OPTION_LABELS.index(q.correct_option)]
        requests.append(
            {
                "createItem": {
                    "item": {
                        "title": sanitize_display_text(q.text),
                        "questionItem": {
                            "question": {
                                "required": True,
                                "grading": {
                                    "pointValue": q.points,
                                    "correctAnswers": {
                                        "answers": [{"value": correct_value}]
                                    },
                                },
                                "choiceQuestion": {
                                    "type": "RADIO",
                                    "options": [{"value": o} for o in options],
                                    "shuffle": True,
                                },
                            }
                        },
                    },
                    "location": {"index": index},
                }
            }
        )
        index += 1

    return requests


def build_round(
    session,
    service,
    campus: str,
    drive_name: str,
    round_type: str,
    count: int,
    title: str,
    topics: list[str] | None = None,
    duration_minutes: int = 45,
) -> Round:
    drive = get_or_create_drive(session, drive_name, campus)
    questions = pick_questions(session, round_type, count, topics)

    form = service.forms().create(body={"info": {"title": title}}).execute()
    form_id = form["formId"]

    service.forms().batchUpdate(
        formId=form_id, body={"requests": build_batch_requests(questions, round_type)}
    ).execute()

    # Forms created via the API default to unpublished (Google policy change,
    # effective forms created after 2026-06-30) - without this, the form
    # exists but responder_uri is inaccessible to candidates.
    service.forms().setPublishSettings(
        formId=form_id,
        body={
            "publishSettings": {
                "publishState": {
                    "isPublished": True,
                    "isAcceptingResponses": True,
                }
            }
        },
    ).execute()

    form = service.forms().get(formId=form_id).execute()
    responder_uri = form["responderUri"]

    round_ = Round(
        drive_id=drive.id,
        round_type=round_type,
        form_id=form_id,
        responder_uri=responder_uri,
        duration_minutes=duration_minutes,
    )
    session.add(round_)
    session.commit()

    timer_path = TIMER_OUT_DIR / f"round_{round_.id}_timer.html"
    generate_timer_html(round_, timer_path)
    round_.timer_path = str(timer_path)  # not persisted, just for the summary print
    return round_


def _suggested_minutes_for_topic(session, topic: str) -> float:
    avg = session.query(func.avg(CodingQuestion.suggested_minutes)).filter_by(topic=topic).scalar()
    return avg or 8.0


def build_coding_round(
    session,
    campus: str,
    drive_name: str,
    count: int,
    duration_minutes: int | None = 45,
    section_plan: list[tuple[str, int]] | None = None,
) -> Round:
    """Coding rounds don't use Google Forms at all - the candidate UI is
    served directly by app.py (Monaco + Judge0). This just registers the
    Round and checks the coding question bank has enough questions.

    section_plan (optional): an ordered [(topic, count), ...] list - each
    candidate's session groups questions by section in this exact order
    (random within each section), instead of one flat random draw across
    the whole bank. When set, it overrides `count` for assignment purposes
    (coding_question_count is still stored as the total, for display).

    duration_minutes=None auto-computes a suggested total from each
    included question's suggested_minutes (per-topic average, weighted by
    how many questions from that topic will be assigned) - pass an
    explicit int to override with your own duration instead."""
    drive = get_or_create_drive(session, drive_name, campus)

    if section_plan:
        total_count = sum(c for _, c in section_plan)
        for topic, topic_count in section_plan:
            available = session.query(CodingQuestion).filter_by(topic=topic).count()
            if available < topic_count:
                raise SystemExit(
                    f"Only {available} coding question(s) loaded for topic '{topic}'; requested {topic_count}."
                )
        if duration_minutes is None:
            duration_minutes = round(sum(
                topic_count * _suggested_minutes_for_topic(session, topic) for topic, topic_count in section_plan
            ))
    else:
        total_count = count
        available = session.query(CodingQuestion).count()
        if available < count:
            raise SystemExit(
                f"Only {available} coding question(s) loaded (load_coding_questions.py); requested {count}."
            )
        if duration_minutes is None:
            avg = session.query(func.avg(CodingQuestion.suggested_minutes)).scalar() or 8.0
            duration_minutes = round(count * avg)

    round_ = Round(
        drive_id=drive.id,
        round_type="coding",
        coding_question_count=total_count,
        section_plan=json.dumps(section_plan) if section_plan else None,
        duration_minutes=duration_minutes,
    )
    session.add(round_)
    session.commit()
    return round_


def build_technical_discussion_round(
    session,
    campus: str,
    drive_name: str,
    count: int = 4,
) -> Round:
    """Technical Discussion rounds don't use Google Forms or a candidate
    self-test - they're an interviewer-scored session against a shortlisted
    candidate, served from webui.py. Just registers the Round and checks
    the interview question bank has enough questions."""
    drive = get_or_create_drive(session, drive_name, campus)

    available = session.query(InterviewQuestion).count()
    if available < count:
        raise SystemExit(
            f"Only {available} interview question(s) loaded (load_interview_questions.py); requested {count}."
        )

    round_ = Round(
        drive_id=drive.id,
        round_type="technical_discussion",
        interview_question_count=count,
    )
    session.add(round_)
    session.commit()
    return round_


def promote_shortlisted(session, source_round: Round, target_round: Round, band: str = "shortlisted") -> int:
    """Copies every candidate banded `band` in source_round into
    target_round as a fresh Attempt with its own token - the mechanism
    behind "flow from results/shortlisted into Technical Discussion".
    Idempotent: a candidate already promoted (matched by candidate_id) is
    skipped, not duplicated."""
    import secrets

    source_attempts = (
        session.query(Attempt).filter_by(round_id=source_round.id, band=band).all()
    )
    already_promoted = {
        a.candidate_id
        for a in session.query(Attempt).filter_by(round_id=target_round.id).all()
    }

    promoted = 0
    for src in source_attempts:
        if src.candidate_id in already_promoted:
            continue
        session.add(Attempt(
            candidate_id=src.candidate_id,
            round_id=target_round.id,
            token=secrets.token_urlsafe(24),
            status="invited",
        ))
        promoted += 1
    session.commit()
    return promoted


def print_coding_round_summary(round_: Round) -> None:
    print(f"Created coding round #{round_.id} for drive '{round_.drive.name}' ({round_.drive.campus})")
    print(f"Questions per candidate: {round_.coding_question_count}")
    print(f"Duration:                {round_.duration_minutes} minutes")
    print()
    print("Next steps:")
    print("  1. Upload candidates to this round (name,email roster)")
    print("  2. Start app.py so it's reachable on your LAN: python app.py")
    print("     (binds 0.0.0.0:8788 - only run this during a live test window)")
    print("  3. Send invites with base-url set to app.py's LAN URL, e.g.")
    print("     http://<your-laptop-ip>:8788")
    print("     This does a Judge0 pre-flight check before sending any email.")


def print_round_summary(round_: Round) -> None:
    print(f"Created round #{round_.id} for drive '{round_.drive.name}' ({round_.drive.campus})")
    print(f"Form ID:        {round_.form_id}")
    print(f"Edit URL:       https://docs.google.com/forms/d/{round_.form_id}/edit")
    print(f"Responder URL:  {round_.responder_uri}")
    print(f"Duration:       {round_.duration_minutes} minutes")
    print(f"Timer page:     {getattr(round_, 'timer_path', TIMER_OUT_DIR / f'round_{round_.id}_timer.html')}")
    print("  (open in a browser, display on the room's projector/shared screen,")
    print("   click Start when the session begins - Google Forms has no native timer)")
    print()
    print("Manual one-time steps (not exposed via the Forms API - verified against the live")
    print("API schema, these fields genuinely don't exist there): open the Edit URL and set:")
    print("  1. Settings > Responses > 'Collect email addresses' -> Verified")
    print("     (matches responses to candidates; a response submitted before this is on")
    print("     can NEVER be matched retroactively - the candidate must submit again)")
    print("  2. Settings > Responses > 'Limit to 1 response'")
    print("     (blocks a second submission per Google account)")
    print("  3. Settings > Quizzes > 'Release grade' -> Later, after manual review")
    print("     (hides both the score AND correct answers from the candidate immediately")
    print("     after they submit)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--campus", required=True)
    parser.add_argument("--drive-name", required=True)
    parser.add_argument("--round-type", required=True, choices=["aptitude", "programming"])
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--topics", default=None, help="comma-separated topic filter")
    parser.add_argument("--duration-minutes", type=int, default=45, help="admin-defined time limit, shown on the generated timer page")
    args = parser.parse_args()

    topics = [t.strip() for t in args.topics.split(",")] if args.topics else None

    init_db()
    session = SessionLocal()
    service = forms_service()
    round_ = build_round(
        session, service, args.campus, args.drive_name, args.round_type, args.count, args.title, topics,
        duration_minutes=args.duration_minutes,
    )
    print_round_summary(round_)


if __name__ == "__main__":
    main()
