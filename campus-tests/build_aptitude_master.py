"""
Assembles the 150-question pre-CAT aptitude master bank from the four
category-cluster data files into aptitude_master_150.xlsx (Aptitude +
Answer Key sheets, same schema as build_initial_bank.py).

Usage:
    python build_aptitude_master.py
"""

import importlib.util
from pathlib import Path

from openpyxl import Workbook

from build_initial_bank import build_answer_key_sheet, build_question_sheet

DATA_DIR = Path(__file__).parent / "aptitude_master" / "data"
OUT_PATH = Path(__file__).parent / "aptitude_master_150.xlsx"


def load_rows(module_name: str) -> list[tuple]:
    path = DATA_DIR / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ROWS


def main() -> None:
    all_rows = []
    for module_name in ["a", "b", "c", "d"]:
        rows = load_rows(module_name)
        print(f"{module_name}.py: {len(rows)} questions")
        all_rows.extend(rows)

    print(f"Total: {len(all_rows)} questions")

    wb = Workbook()
    wb.remove(wb.active)
    build_question_sheet(wb, "Aptitude", all_rows)
    build_answer_key_sheet(wb, all_rows)
    wb.save(OUT_PATH)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
