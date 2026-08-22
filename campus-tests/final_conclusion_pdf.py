"""
Generates the Final Conclusion PDF: every candidate whose Technical
Discussion decision is "selected", tabulated with name, email, drive, and
decision date.

Usage (as a library, called from webui.py):
    from final_conclusion_pdf import generate_final_conclusion_pdf
    pdf_bytes = generate_final_conclusion_pdf(rows, drive_name)
"""

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

ACCENT = colors.HexColor("#1a7ee8")
INK = colors.HexColor("#12151c")
INK_SOFT = colors.HexColor("#545b68")
ROW_ALT = colors.HexColor("#f5f8fc")
LINE = colors.HexColor("#dde5f0")


def generate_final_conclusion_pdf(rows: list[dict], drive_name: str) -> bytes:
    """rows: list of {name, email, round_name, decision_at}"""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=24 * mm, bottomMargin=20 * mm, leftMargin=20 * mm, rightMargin=20 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Title"], textColor=INK, fontSize=18, spaceAfter=4)
    sub_style = ParagraphStyle("Sub", parent=styles["Normal"], textColor=INK_SOFT, fontSize=10, spaceAfter=18)

    story = [
        Paragraph("Aizentify Campus Console — Final Conclusion", title_style),
        Paragraph(f"Drive: {drive_name} &nbsp;&middot;&nbsp; Status: Selected", sub_style),
    ]

    if not rows:
        story.append(Paragraph("No candidates marked Selected yet.", styles["Normal"]))
    else:
        table_data = [["#", "Name", "Email", "Decided"]]
        for i, r in enumerate(rows, start=1):
            table_data.append([str(i), r["name"], r["email"], r.get("decision_at") or "—"])

        table = Table(table_data, colWidths=[10 * mm, 55 * mm, 75 * mm, 30 * mm], repeatRows=1)
        style = TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9.5),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 1), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, LINE),
            ("TEXTCOLOR", (0, 1), (-1, -1), INK),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                style.add("BACKGROUND", (0, i), (-1, i), ROW_ALT)
        table.setStyle(style)
        story.append(table)
        story.append(Spacer(1, 16))
        story.append(Paragraph(f"{len(rows)} candidate(s) selected.", sub_style))

    doc.build(story)
    return buf.getvalue()
