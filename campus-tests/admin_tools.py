"""Admin-only data lifecycle helpers: DB backup/restore and scoped cleanup
of Drive/Round/Candidate/Attempt data. Question banks (coding_questions,
questions, interview_questions) are managed separately on the Question Bank
page and are left untouched by wipe_scope() - only the explicit "Everything
+ clear banks" cleanup path calls wipe_question_banks() as well.
"""

import shutil
from datetime import datetime, timezone
from pathlib import Path

from models import (
    DB_PATH, Attempt, Candidate, CodingAttemptQuestion, CodingQuestion, CodingTestCase, Drive, FormAnswer,
    InterviewAttemptQuestion, InterviewQuestion, Question, Round, engine,
)

BACKUP_DIR = DB_PATH.parent / "backups"


def list_backups() -> list[dict]:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(BACKUP_DIR.glob("*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [
        {
            "name": f.name,
            "size_kb": round(f.stat().st_size / 1024, 1),
            "modified": datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        }
        for f in files
    ]


def create_backup(label: str = "manual") -> str:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    dest = BACKUP_DIR / f"campus-{stamp}-{label}.db"
    shutil.copy(DB_PATH, dest)
    return dest.name


def restore_backup(filename: str) -> None:
    safe_name = Path(filename).name  # strip any directory components - no path traversal
    src = BACKUP_DIR / safe_name
    if not src.is_file():
        raise ValueError(f"Backup not found: {safe_name}")
    create_backup(label="pre-restore")  # safety net: never restore without a snapshot of what it replaced
    shutil.copy(src, DB_PATH)
    engine.dispose()  # drop pooled connections so the next request re-opens the restored file


def wipe_scope(session, drive_ids: list[int]) -> dict:
    """Deletes Drive/Round/Candidate/Attempt data (and dependent
    CodingAttemptQuestion/InterviewAttemptQuestion/FormAnswer rows) for the
    given drive ids. Question banks are untouched. Caller commits."""
    if not drive_ids:
        return {"drives": 0, "rounds": 0, "candidates": 0, "attempts": 0}

    round_ids = [r_id for (r_id,) in session.query(Round.id).filter(Round.drive_id.in_(drive_ids))]
    attempt_ids = [a_id for (a_id,) in session.query(Attempt.id).filter(Attempt.round_id.in_(round_ids))]

    session.query(FormAnswer).filter(FormAnswer.attempt_id.in_(attempt_ids)).delete(synchronize_session=False)
    session.query(CodingAttemptQuestion).filter(CodingAttemptQuestion.attempt_id.in_(attempt_ids)).delete(synchronize_session=False)
    session.query(InterviewAttemptQuestion).filter(InterviewAttemptQuestion.attempt_id.in_(attempt_ids)).delete(synchronize_session=False)

    return {
        "attempts": session.query(Attempt).filter(Attempt.id.in_(attempt_ids)).delete(synchronize_session=False),
        "candidates": session.query(Candidate).filter(Candidate.drive_id.in_(drive_ids)).delete(synchronize_session=False),
        "rounds": session.query(Round).filter(Round.drive_id.in_(drive_ids)).delete(synchronize_session=False),
        "drives": session.query(Drive).filter(Drive.id.in_(drive_ids)).delete(synchronize_session=False),
    }


def wipe_question_banks(session) -> dict:
    """Deletes the MCQ (aptitude/programming), coding, and interview
    question banks entirely. Only call this after wipe_scope() has already
    cleared every Attempt (e.g. as part of an "Everything" cleanup) -
    CodingAttemptQuestion/InterviewAttemptQuestion FKs would otherwise
    block deleting the questions they reference. Caller commits."""
    return {
        "coding_test_cases": session.query(CodingTestCase).delete(synchronize_session=False),
        "coding_questions": session.query(CodingQuestion).delete(synchronize_session=False),
        "interview_questions": session.query(InterviewQuestion).delete(synchronize_session=False),
        "mcq_questions": session.query(Question).delete(synchronize_session=False),
    }
