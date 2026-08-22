"""
Generates the hands-on coding exam PDFs:
  - One candidate PDF per topic (output/<topic>_exercises.pdf): one exercise
    per front+back page pair, ruled space for handwritten answers.
  - One consolidated evaluator reference PDF (output/evaluator_reference.pdf)
    covering every exercise across all topics, with a table of contents
    indexed by exercise ID, and a CONFIDENTIAL stamp on every page.

Usage:
    python generate_pdfs.py
"""

import importlib.util
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUT_DIR = BASE_DIR / "output"
LOGO_PATH = BASE_DIR.parent / "static" / "brand-logo-header.png"

PAGE_W, PAGE_H = A4
MARGIN_X = 48
CONTENT_W = PAGE_W - 2 * MARGIN_X

INK = (0.11, 0.11, 0.10)
INK_SOFT = (0.42, 0.42, 0.39)
RULE = (0.86, 0.85, 0.80)
ACCENT = (0.102, 0.494, 0.910)
ACCENT_DEEP = (0.078, 0.314, 0.910)
ACCENT_BG = (0.90, 0.95, 0.99)
STAMP = (0.70, 0.15, 0.12)
BADGE_BG = (0.93, 0.93, 0.91)
CODE_BG = (0.96, 0.95, 0.92)
CODE_TEXT = (0.20, 0.20, 0.17)

TOPICS = [
    ("python", "Python", "PY"),
    ("typescript", "TypeScript", "TS"),
    ("react", "React", "RCT"),
    ("css", "CSS", "CSS"),
]


def load_exercises(module_name: str) -> list[dict]:
    path = DATA_DIR / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.EXERCISES


# ---------------------------------------------------------------------------
# low-level drawing helpers
# ---------------------------------------------------------------------------

def wrap_text(c: canvas.Canvas, text: str, font: str, size: float, max_width: float) -> list[str]:
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph:
            lines.append("")
            continue
        words = paragraph.split(" ")
        current = ""
        for w in words:
            trial = (current + " " + w).strip()
            if c.stringWidth(trial, font, size) <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = w
        lines.append(current)
    return lines


def draw_wrapped(c, text, x, y, font, size, max_width, leading, color=INK) -> float:
    c.setFillColorRGB(*color)
    for line in wrap_text(c, text, font, size, max_width):
        c.setFont(font, size)
        c.drawString(x, y, line)
        y -= leading
    return y


def draw_ruled_lines(c, x, y_top, y_bottom, width, gap=22):
    c.setStrokeColorRGB(*RULE)
    c.setLineWidth(0.6)
    y = y_top
    while y > y_bottom:
        c.line(x, y, x + width, y)
        y -= gap


def draw_badge(c, x, y, text, bg, fg) -> float:
    c.setFont("Helvetica-Bold", 8)
    w = c.stringWidth(text, "Helvetica-Bold", 8) + 14
    c.setFillColorRGB(*bg)
    c.roundRect(x, y, w, 15, 2, fill=1, stroke=0)
    c.setFillColorRGB(*fg)
    c.drawString(x + 7, y + 4.5, text)
    return w


def draw_code_block(c, code: str, x, y_top, max_width) -> float:
    lines = code.split("\n")
    block_h = 12 * len(lines) + 16
    c.setFillColorRGB(*CODE_BG)
    c.rect(x, y_top - block_h, max_width, block_h, fill=1, stroke=0)
    c.setFillColorRGB(*ACCENT)
    c.rect(x, y_top - block_h, 2.4, block_h, fill=1, stroke=0)
    c.setFont("Courier", 8)
    c.setFillColorRGB(*CODE_TEXT)
    cy = y_top - 12
    for line in lines:
        c.drawString(x + 10, cy, line[:110])
        cy -= 12
    return y_top - block_h - 10


def draw_header(c, brand_label="AIZENTIFY CAMPUS", name_fields=True) -> float:
    y_top = PAGE_H - 40
    text_x = MARGIN_X
    if LOGO_PATH.exists():
        img = ImageReader(str(LOGO_PATH))
        iw, ih = img.getSize()
        target_h = 16
        target_w = target_h * iw / ih
        c.drawImage(img, MARGIN_X, y_top - 4, width=target_w, height=target_h, mask="auto")
        text_x = MARGIN_X + target_w + 8
    c.setFont("Helvetica-Bold", 9)
    c.setFillColorRGB(*INK_SOFT)
    c.drawString(text_x, y_top, brand_label)

    if name_fields:
        c.setFont("Courier", 8)
        c.setFillColorRGB(*INK_SOFT)
        fx = PAGE_W - MARGIN_X - 170
        c.drawString(fx, y_top + 6, "Name:")
        c.line(fx + 34, y_top + 5, fx + 170, y_top + 5)
        c.drawString(fx, y_top - 6, "Roll No:")
        c.line(fx + 46, y_top - 7, fx + 170, y_top - 7)
        c.drawString(fx, y_top - 18, "Date:")
        c.line(fx + 30, y_top - 19, fx + 170, y_top - 19)

    rule_y = y_top - 30
    c.setStrokeColorRGB(*INK)
    c.setLineWidth(1.2)
    c.line(MARGIN_X, rule_y, PAGE_W - MARGIN_X, rule_y)
    return rule_y - 22


def draw_footer(c, left_text, right_text):
    y = 30
    c.setFont("Courier", 7.5)
    c.setFillColorRGB(*INK_SOFT)
    c.drawString(MARGIN_X, y, left_text)
    c.drawRightString(PAGE_W - MARGIN_X, y, right_text)


# ---------------------------------------------------------------------------
# candidate exercise pages
# ---------------------------------------------------------------------------

def draw_front_page(c, ex, index, total, topic_label):
    y = draw_header(c, name_fields=True)

    bw = draw_badge(c, MARGIN_X, y - 12, topic_label.upper(), ACCENT_BG, ACCENT_DEEP)
    draw_badge(c, MARGIN_X + bw + 8, y - 12, ex["difficulty"].upper(), BADGE_BG, INK_SOFT)
    y -= 34

    c.setFont("Times-Bold", 15)
    c.setFillColorRGB(*INK)
    c.drawString(MARGIN_X, y, ex["title"])
    y -= 20

    y = draw_wrapped(c, ex["scenario"], MARGIN_X, y, "Helvetica", 9.5, CONTENT_W, 13)
    y -= 4

    if ex.get("code_reference"):
        y = draw_code_block(c, ex["code_reference"], MARGIN_X, y, CONTENT_W)

    c.setFont("Helvetica-Bold", 9.5)
    c.setFillColorRGB(*INK)
    c.drawString(MARGIN_X, y, "Your task:")
    y -= 14
    for i, t in enumerate(ex["tasks"], start=1):
        y = draw_wrapped(c, f"{i}. {t}", MARGIN_X, y, "Helvetica", 9.5, CONTENT_W, 13)
    y -= 6

    draw_ruled_lines(c, MARGIN_X, y, 55, CONTENT_W, gap=22)
    draw_footer(c, f"Exercise {index} of {total} - {topic_label}", "Continue on reverse ->")


def draw_back_page(c, ex, topic_label):
    y_top = PAGE_H - 40
    c.setFont("Times-Italic", 11)
    c.setFillColorRGB(*INK_SOFT)
    c.drawString(MARGIN_X, y_top, f"{ex['title']} — continued")
    c.setFont("Courier", 8)
    c.drawRightString(PAGE_W - MARGIN_X, y_top, f"{topic_label} · {ex['difficulty'].upper()}")

    rule_y = y_top - 14
    c.setStrokeColorRGB(*INK)
    c.setLineWidth(1.2)
    c.line(MARGIN_X, rule_y, PAGE_W - MARGIN_X, rule_y)

    draw_ruled_lines(c, MARGIN_X, rule_y - 20, 55, CONTENT_W, gap=22)

    c.setFont("Courier", 7.5)
    c.setFillColorRGB(*INK_SOFT)
    c.drawCentredString(PAGE_W / 2, 30, f"— End of {ex['id']} —")


def generate_topic_pdf(topic_label: str, exercises: list[dict], out_path: Path):
    c = canvas.Canvas(str(out_path), pagesize=A4)
    total = len(exercises)
    for i, ex in enumerate(exercises, start=1):
        draw_front_page(c, ex, i, total, topic_label)
        c.showPage()
        draw_back_page(c, ex, topic_label)
        c.showPage()
    c.save()


# ---------------------------------------------------------------------------
# consolidated evaluator reference PDF
# ---------------------------------------------------------------------------

class RefCursor:
    """Tracks vertical position on the evaluator reference PDF, starting a
    new (stamped, headered) page automatically when content would overflow."""

    def __init__(self, c: canvas.Canvas):
        self.c = c
        self.y = 0
        self.ex = None
        self.topic_label = None

    def new_exercise_page(self, ex, topic_label):
        self.ex = ex
        self.topic_label = topic_label
        self.c.showPage()
        self._draw_page_chrome(continued=False)

    def _draw_page_chrome(self, continued: bool):
        c = self.c
        y_top = PAGE_H - 40
        c.setFont("Helvetica-Bold", 9)
        c.setFillColorRGB(*INK_SOFT)
        c.drawString(MARGIN_X, y_top, "AIZENTIFY CAMPUS · EVALUATOR REFERENCE")

        c.setStrokeColorRGB(*STAMP)
        c.setFillColorRGB(*STAMP)
        c.setLineWidth(1.2)
        stamp_text = "EVALUATOR ONLY"
        c.setFont("Helvetica-Bold", 8)
        sw = c.stringWidth(stamp_text, "Helvetica-Bold", 8)
        c.rect(PAGE_W - MARGIN_X - sw - 14, y_top - 4, sw + 14, 15, fill=0, stroke=1)
        c.drawString(PAGE_W - MARGIN_X - sw - 7, y_top + 0.5, stamp_text)

        rule_y = y_top - 22
        c.setStrokeColorRGB(*INK)
        c.setLineWidth(1.2)
        c.line(MARGIN_X, rule_y, PAGE_W - MARGIN_X, rule_y)

        y = rule_y - 20
        bw = draw_badge(c, MARGIN_X, y - 12, self.topic_label.upper(), ACCENT_BG, ACCENT_DEEP)
        draw_badge(c, MARGIN_X + bw + 8, y - 12, self.ex["difficulty"].upper(), BADGE_BG, INK_SOFT)
        y -= 30

        c.setFont("Times-Bold", 13)
        c.setFillColorRGB(*INK)
        suffix = "  (continued)" if continued else ""
        c.drawString(MARGIN_X, y, f"{self.ex['id']} — {self.ex['title']}{suffix}")
        y -= 18
        self.y = y

    def ensure_space(self, needed: float):
        if self.y - needed < 60:
            self.c.showPage()
            self._draw_page_chrome(continued=True)

    def section_title(self, text):
        self.ensure_space(24)
        self.c.setFont("Helvetica-Bold", 9.5)
        self.c.setFillColorRGB(*ACCENT_DEEP)
        self.c.drawString(MARGIN_X, self.y, text.upper())
        self.y -= 14

    def paragraph(self, text):
        est_lines = max(1, len(text) // 95 + 1)
        self.ensure_space(est_lines * 12 + 6)
        self.y = draw_wrapped(self.c, text, MARGIN_X, self.y, "Helvetica", 9.5, CONTENT_W, 12.5)
        self.y -= 4

    def code(self, code_text):
        """Draws a code block, splitting it across pages if it's taller
        than a single page's remaining (or full) content area."""
        line_h = 12
        lines = code_text.split("\n")
        i = 0
        while i < len(lines):
            available = self.y - 60
            max_lines_here = max(1, int((available - 16) / line_h))
            if available < 30:
                self.c.showPage()
                self._draw_page_chrome(continued=True)
                available = self.y - 60
                max_lines_here = max(1, int((available - 16) / line_h))
            chunk = lines[i : i + max_lines_here]
            self.y = draw_code_block(self.c, "\n".join(chunk), MARGIN_X, self.y, CONTENT_W)
            i += len(chunk)

    def bullets(self, items):
        for item in items:
            est_lines = max(1, len(item) // 90 + 1)
            self.ensure_space(est_lines * 12 + 4)
            self.y = draw_wrapped(self.c, f"• {item}", MARGIN_X + 2, self.y, "Helvetica", 9.3, CONTENT_W - 6, 12.5)
        self.y -= 4

    def rubric(self, rows):
        self.ensure_space(14 * len(rows) + 10)
        c = self.c
        for label, pct in rows:
            c.setFont("Helvetica", 9.3)
            c.setFillColorRGB(*INK)
            c.drawString(MARGIN_X, self.y, label)
            c.setFont("Courier", 9.3)
            c.setFillColorRGB(*INK_SOFT)
            c.drawRightString(MARGIN_X + CONTENT_W, self.y, f"{pct}%")
            c.setStrokeColorRGB(*RULE)
            c.setLineWidth(0.5)
            c.line(MARGIN_X, self.y - 4, MARGIN_X + CONTENT_W, self.y - 4)
            self.y -= 16


def draw_toc(c, entries: list[tuple]):
    """entries: list of (id, title, topic_label) in final page order."""
    c.setFont("Times-Bold", 18)
    c.setFillColorRGB(*INK)
    c.drawString(MARGIN_X, PAGE_H - 60, "Evaluator Reference — Contents")
    c.setFont("Helvetica", 9.5)
    c.setFillColorRGB(*INK_SOFT)
    c.drawString(MARGIN_X, PAGE_H - 78, "Confidential — lookup by exercise ID, matches the ID printed on each candidate page.")

    y = PAGE_H - 110
    col_x = [MARGIN_X, MARGIN_X + CONTENT_W / 2 + 10]
    col = 0
    rows_per_col = 34
    row_in_col = 0

    for eid, title, topic_label in entries:
        if row_in_col >= rows_per_col:
            col += 1
            row_in_col = 0
            if col > 1:
                c.showPage()
                c.setFont("Times-Bold", 13)
                c.setFillColorRGB(*INK)
                c.drawString(MARGIN_X, PAGE_H - 50, "Evaluator Reference — Contents (cont'd)")
                y = PAGE_H - 80
                col = 0
        x = col_x[col]
        c.setFont("Courier", 8.5)
        c.setFillColorRGB(*ACCENT_DEEP)
        c.drawString(x, y, eid)
        c.setFont("Helvetica", 8.5)
        c.setFillColorRGB(*INK)
        c.drawString(x + 48, y, title[:38])
        y -= 15
        row_in_col += 1


def generate_reference_pdf(topic_sets: list[tuple], out_path: Path):
    """topic_sets: list of (topic_label, exercises)"""
    c = canvas.Canvas(str(out_path), pagesize=A4)

    toc_entries = [
        (ex["id"], ex["title"], label)
        for label, exercises in topic_sets
        for ex in exercises
    ]
    draw_toc(c, toc_entries)

    cursor = RefCursor(c)
    for topic_label, exercises in topic_sets:
        for ex in exercises:
            cursor.new_exercise_page(ex, topic_label)
            cursor.section_title("Expected approach")
            cursor.code(ex["reference_solution_code"])
            cursor.section_title("What to check")
            cursor.bullets(ex["check_points"])
            cursor.section_title("Common mistakes")
            cursor.bullets(ex["common_mistakes"])
            cursor.section_title("Suggested scoring")
            cursor.rubric(ex["rubric"])

    c.save()


def main():
    OUT_DIR.mkdir(exist_ok=True)
    topic_sets = []
    for module_name, label, _prefix in TOPICS:
        exercises = load_exercises(module_name)
        out_path = OUT_DIR / f"{module_name}_exercises.pdf"
        generate_topic_pdf(label, exercises, out_path)
        print(f"Wrote {out_path} ({len(exercises)} exercises, {len(exercises) * 2} pages)")
        topic_sets.append((label, exercises))

    ref_path = OUT_DIR / "evaluator_reference.pdf"
    generate_reference_pdf(topic_sets, ref_path)
    print(f"Wrote {ref_path}")


if __name__ == "__main__":
    main()
