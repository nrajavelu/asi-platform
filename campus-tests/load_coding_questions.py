"""
Loads coding questions (one JSON file per question) into the DB. Each
file is treated as authoritative for that question_id: re-running this
replaces the question and its test cases, matched by external_id, without
touching other questions in the bank.

Usage:
    python load_coding_questions.py coding_questions/

    # Replace the ENTIRE coding bank with just this folder's questions -
    # use this when switching to a specific fixed set (e.g. one of the
    # SIT Master/Coding/set*_*/ folders), so a coding round's random draw
    # can't reach into a previously-loaded set left over in the DB:
    python load_coding_questions.py --replace "SIT Master/Coding/set1_easy/"
"""

import argparse
import json
from pathlib import Path

from models import CodingAttemptQuestion, CodingQuestion, CodingTestCase, SessionLocal, init_db


def clear_bank(session) -> int:
    """Deletes every coding question (and its test cases / any candidate
    attempt-question rows referencing them). Only call this when you
    intend to fully replace the active coding bank - e.g. switching sets
    between drives, never mid-drive with live candidate data still needed."""
    question_ids = [qid for (qid,) in session.query(CodingQuestion.id).all()]
    if not question_ids:
        return 0
    session.query(CodingAttemptQuestion).filter(CodingAttemptQuestion.question_id.in_(question_ids)).delete(synchronize_session=False)
    session.query(CodingTestCase).filter(CodingTestCase.question_id.in_(question_ids)).delete(synchronize_session=False)
    session.query(CodingQuestion).filter(CodingQuestion.id.in_(question_ids)).delete(synchronize_session=False)
    return len(question_ids)


REQUIRED_FIELDS = ("id", "topic", "difficulty", "title", "statement", "test_cases")


def load_question_file(session, path: Path) -> str:
    data = json.loads(path.read_text())

    for field in REQUIRED_FIELDS:
        if field not in data:
            raise ValueError(
                f"{path.name}: missing required field '{field}' for a coding question. "
                f"If this file has an 'area'/'rubric_guide' field instead, it's a Technical "
                f"Discussion question - upload it to the Interview Question Bank, not here."
            )

    question = session.query(CodingQuestion).filter_by(external_id=data["id"]).first()
    if question is None:
        question = CodingQuestion(external_id=data["id"])
        session.add(question)
    else:
        session.query(CodingTestCase).filter_by(question_id=question.id).delete()

    question.topic = data["topic"]
    question.difficulty = data["difficulty"]
    question.title = data["title"]
    question.statement = data["statement"]
    question.starter_code = data.get("starter_code", "")
    question.language_id = data.get("language_id", 0)  # unused for sql/react/css, Judge0 language for code
    question.hints = "\n".join(data.get("hints", []))
    question.points = data.get("points", 10)
    question.question_type = data.get("question_type", "code")
    question.harness_fixture = data.get("harness_fixture")
    default_minutes = {"easy": 5, "medium": 8, "hard": 12}.get(question.difficulty, 8)
    question.suggested_minutes = data.get("suggested_minutes", default_minutes)
    session.flush()

    for tc in data["test_cases"]:
        session.add(
            CodingTestCase(
                question_id=question.id,
                stdin=tc.get("stdin", ""),
                expected_output=tc.get("expected_output", ""),  # unused for react/css (assertion_script instead)
                is_sample=tc.get("is_sample", False),
                weight=tc.get("weight", 1),
                assertion_script=tc.get("assertion_script"),
                ordered=tc.get("ordered", False),
            )
        )

    return data["id"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", help="folder of *.json coding question files")
    parser.add_argument(
        "--replace", action="store_true",
        help="clear the entire existing coding bank first, so only this folder's questions remain loaded",
    )
    args = parser.parse_args()

    init_db()
    session = SessionLocal()

    if args.replace:
        cleared = clear_bank(session)
        session.commit()
        print(f"Cleared {cleared} existing coding question(s) from the bank.")

    loaded = []
    for path in sorted(Path(args.directory).glob("*.json")):
        loaded.append(load_question_file(session, path))
    session.commit()

    print(f"Loaded {len(loaded)} coding question(s): {', '.join(loaded)}")


if __name__ == "__main__":
    main()
