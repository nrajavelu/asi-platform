"""
Bulk-uploads candidates for a round from a CSV or XLSX file (columns:
name, email) and creates one Attempt per candidate, tracking who's
invited so responses can be matched back to the roster later during
scoring.

Usage:
    python add_candidates.py --round-id 1 --file candidates.csv
    python add_candidates.py --round-id 1 --file candidates.xlsx
"""

import argparse
import csv
import secrets
from pathlib import Path

from openpyxl import load_workbook

from models import Attempt, Candidate, Round, SessionLocal, init_db


def rows_from_file(path: str) -> list[dict]:
    file_path = Path(path)
    if file_path.suffix.lower() == ".csv":
        rows = list(csv.DictReader(file_path.open(newline="", encoding="utf-8")))
    elif file_path.suffix.lower() == ".xlsx":
        ws = load_workbook(file_path, read_only=True, data_only=True).active
        header = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))]
        rows = []
        for raw_row in ws.iter_rows(min_row=2, values_only=True):
            if all(v is None for v in raw_row):
                continue
            rows.append(dict(zip(header, raw_row)))
    else:
        raise ValueError(f"Unsupported file type: {file_path.suffix} (use .csv or .xlsx)")

    # Column names are matched case-insensitively ("Email"/"EMAIL"/"email"
    # all work) since spreadsheet headers are commonly capitalized - rows
    # are normalized to lowercase keys so downstream code can always just
    # use row["email"]/row["name"].
    rows = [{(k.strip().lower() if isinstance(k, str) else k): v for k, v in row.items()} for row in rows]

    found = set(rows[0].keys()) if rows else set()
    missing = {"name", "email"} - found
    if missing:
        hint = ""
        if len(found) == 1 and "," in next(iter(found), ""):
            hint = (
                " It looks like the whole header line is wrapped in one pair of "
                "quotes (e.g. \"name,email\"), so it's being read as a single "
                "column instead of two - remove the surrounding quotes and "
                "re-save as plain comma-separated values."
            )
        raise ValueError(
            f"Missing required column(s) {sorted(missing)} in {path}. "
            f"Found columns: {sorted(found)}.{hint}"
        )
    return rows


def add_candidates_from_file(session, round_: Round, file_path: str) -> int:
    created = 0
    for row in rows_from_file(file_path):
        email = str(row["email"]).strip().lower()
        name = str(row["name"]).strip()

        candidate = (
            session.query(Candidate)
            .filter_by(drive_id=round_.drive_id, email=email)
            .first()
        )
        if candidate is None:
            candidate = Candidate(drive_id=round_.drive_id, email=email, name=name)
            session.add(candidate)
            session.flush()

        existing = (
            session.query(Attempt)
            .filter_by(candidate_id=candidate.id, round_id=round_.id)
            .first()
        )
        if existing is not None:
            continue

        session.add(
            Attempt(
                candidate_id=candidate.id,
                round_id=round_.id,
                token=secrets.token_urlsafe(24),
                status="invited",
            )
        )
        created += 1

    session.commit()
    return created


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--round-id", type=int, required=True)
    parser.add_argument("--file", required=True, help="candidates .csv or .xlsx")
    args = parser.parse_args()

    init_db()
    session = SessionLocal()
    round_ = session.get(Round, args.round_id)
    if round_ is None:
        raise SystemExit(f"No round with id {args.round_id}")

    try:
        created = add_candidates_from_file(session, round_, args.file)
    except ValueError as e:
        raise SystemExit(str(e))
    print(f"Created {created} attempt(s) for round #{round_.id}")


if __name__ == "__main__":
    main()
