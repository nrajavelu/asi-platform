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

ROUND_TYPE_FOCUS = {
    "aptitude": "quantitative reasoning, logical thinking, and problem-solving ability",
    "programming": "programming fundamentals, tools, and AI/LLM working knowledge",
}

# Google Forms can't be told "you may use paper but not a calculator" via
# any setting - this is candidate-facing policy text, not enforceable by
# the form itself. Reviewed and approved as the standard wording for every
# Aptitude/Programming round.
DOS_DONTS = (
    "Do's:\n"
    "• Ensure a stable internet connection before you start\n"
    "• Keep your registered email/ID details ready if asked\n"
    "• Use rough sheets/paper for your own calculations\n"
    "• Answer every question - there is no negative marking\n"
    "• Submit only when you are completely done - it cannot be reopened\n\n"
    "Don'ts:\n"
    "• Don't refresh or close the browser tab once started\n"
    "• Don't switch tabs or windows during the assessment\n"
    "• Don't use a calculator or any external/AI help\n"
    "• Don't share your test link - it is tied to your account only"
)


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


def resolve_drive(session, drive_id: int | None, campus: str | None, drive_name: str | None) -> Drive:
    """Either attaches to an existing drive (drive_id) or creates/reuses one
    by (campus, drive_name) - the two ways every round-builder now offers
    picking a drive. Campus+Drive is unique at the DB level, so a typo'd
    'new' drive name that actually matches an existing one just reuses it
    rather than erroring, same as get_or_create_drive always did."""
    if drive_id is not None:
        drive = session.get(Drive, drive_id)
        if drive is None:
            raise ValueError(f"No drive with id {drive_id}")
        return drive
    if not campus or not drive_name:
        raise ValueError("Either drive_id or both campus and drive_name are required.")
    return get_or_create_drive(session, drive_name, campus)


def pick_questions(session, round_type: str, count: int, topics: list[str] | None):
    query = session.query(Question).filter(Question.round_type == round_type)
    if topics:
        query = query.filter(Question.topic.in_(topics))
    pool = query.all()
    if len(pool) < count:
        raise ValueError(
            f"Only {len(pool)} '{round_type}' questions available "
            f"(topics={topics or 'all'}); requested {count}."
        )
    return random.sample(pool, count)


def build_batch_requests(questions: list[Question], round_type: str, duration_minutes: int) -> list[dict]:
    """Section 1: logo, then the assessment title/description. Section 2:
    Do's and Don'ts. One question per page after that, each on its own
    page break with a running "Question X of Y" header and its own copy of
    the logo - Google Forms has no way to make an image or header persist
    across sections, so both have to repeat once per page rather than
    being set once."""
    total = len(questions)
    focus = ROUND_TYPE_FOCUS.get(round_type, "the areas covered in this round")

    def logo_item(idx: int) -> dict:
        return {
            "createItem": {
                "item": {"imageItem": {"image": {"sourceUri": LOGO_URL, "altText": "Aizentify"}}},
                "location": {"index": idx},
            }
        }

    requests = [
        {
            "updateSettings": {
                # emailCollectionType=VERIFIED attaches the respondent's real,
                # signed-in Google Account email automatically - not a typed
                # field, so a candidate can't submit under someone else's
                # email (RESPONDER_INPUT allowed exactly that: a free-text
                # box anyone could fill with any address). Without email
                # collection at all, responses come back with
                # respondentEmail=None and results.ingest_results() has
                # nothing to match candidates by.
                "settings": {"quizSettings": {"isQuiz": True}, "emailCollectionType": "VERIFIED"},
                "updateMask": "quizSettings.isQuiz,emailCollectionType",
            }
        },
        logo_item(0),
        {
            "createItem": {
                "item": {
                    "title": f"{round_type.title()} Assessment",
                    "description": (
                        f"A timed assessment evaluating {focus}.\n\n"
                        f"{total} questions - {duration_minutes} minutes - one attempt per Google account."
                    ),
                    "textItem": {},
                },
                "location": {"index": 1},
            }
        },
        {
            "createItem": {
                "item": {"title": "Before You Begin", "description": DOS_DONTS, "pageBreakItem": {}},
                "location": {"index": 2},
            }
        },
    ]

    index = 3
    for position, q in enumerate(questions, start=1):
        requests.append(
            {
                "createItem": {
                    "item": {
                        "title": f"{round_type.title()} Test — Question {position} of {total}",
                        "pageBreakItem": {},
                    },
                    "location": {"index": index},
                }
            }
        )
        index += 1
        requests.append(logo_item(index))
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
    campus: str | None,
    drive_name: str | None,
    round_type: str,
    count: int,
    title: str,
    topics: list[str] | None = None,
    duration_minutes: int = 45,
    drive_id: int | None = None,
) -> Round:
    drive = resolve_drive(session, drive_id, campus, drive_name)
    questions = pick_questions(session, round_type, count, topics)

    form = service.forms().create(body={"info": {"title": title}}).execute()
    form_id = form["formId"]

    service.forms().batchUpdate(
        formId=form_id, body={"requests": build_batch_requests(questions, round_type, duration_minutes)}
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
    campus: str | None,
    drive_name: str | None,
    count: int,
    duration_minutes: int | None = 45,
    section_plan: list[tuple[str, int]] | None = None,
    drive_id: int | None = None,
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
    drive = resolve_drive(session, drive_id, campus, drive_name)

    if section_plan:
        total_count = sum(c for _, c in section_plan)
        for topic, topic_count in section_plan:
            available = session.query(CodingQuestion).filter_by(topic=topic).count()
            if available < topic_count:
                raise ValueError(
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
            raise ValueError(
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
    drive_id: int,
    count: int = 4,
) -> Round:
    """Technical Discussion rounds don't use Google Forms or a candidate
    self-test - they're an interviewer-scored session against a shortlisted
    candidate, served from webui.py. Just registers the Round and checks
    the interview question bank has enough questions.

    Takes an EXISTING drive_id, never creates a new drive - a Technical
    Discussion round only makes sense attached to a drive that already has
    a scored round to promote shortlisted candidates from. Building it
    against a fresh drive (the old campus/drive_name free-text behavior)
    silently produced an empty, unusable round with no source rounds to
    promote from - a real, repeated point of confusion."""
    drive = session.get(Drive, drive_id)
    if drive is None:
        raise ValueError(f"No drive with id {drive_id}")

    available = session.query(InterviewQuestion).count()
    if available < count:
        raise ValueError(
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
    try:
        round_ = build_round(
            session, service, args.campus, args.drive_name, args.round_type, args.count, args.title, topics,
            duration_minutes=args.duration_minutes,
        )
    except ValueError as e:
        raise SystemExit(str(e))
    print_round_summary(round_)


if __name__ == "__main__":
    main()
