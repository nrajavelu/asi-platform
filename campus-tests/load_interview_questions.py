"""
Loads Technical Discussion questions (one JSON file per question) into the
DB. Each file is authoritative for that question_id: re-running this
replaces the question, matched by external_id, without touching others.

Usage:
    python load_interview_questions.py interview_questions/
"""

import argparse
import json
from pathlib import Path

from models import InterviewAttemptQuestion, InterviewQuestion, SessionLocal, init_db


def clear_bank(session) -> int:
    """Deletes every interview question (and any InterviewAttemptQuestion
    rows referencing them). Only call this when you intend to fully replace
    the active interview bank, never mid-drive with live interview data
    still needed."""
    question_ids = [qid for (qid,) in session.query(InterviewQuestion.id).all()]
    if not question_ids:
        return 0
    session.query(InterviewAttemptQuestion).filter(InterviewAttemptQuestion.question_id.in_(question_ids)).delete(synchronize_session=False)
    session.query(InterviewQuestion).filter(InterviewQuestion.id.in_(question_ids)).delete(synchronize_session=False)
    return len(question_ids)


def load_question_file(session, path: Path) -> str:
    data = json.loads(path.read_text())

    question = session.query(InterviewQuestion).filter_by(external_id=data["id"]).first()
    if question is None:
        question = InterviewQuestion(external_id=data["id"])
        session.add(question)

    question.area = data["area"]
    question.question = data["question"]
    question.rubric_guide = data["rubric_guide"]
    question.max_score = data.get("max_score", 5)

    return data["id"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", help="folder of *.json interview question files")
    args = parser.parse_args()

    init_db()
    session = SessionLocal()
    loaded = []
    for path in sorted(Path(args.directory).glob("*.json")):
        loaded.append(load_question_file(session, path))
    session.commit()

    print(f"Loaded {len(loaded)} interview question(s): {', '.join(loaded)}")


if __name__ == "__main__":
    main()
