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

from models import InterviewQuestion, SessionLocal, init_db


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
