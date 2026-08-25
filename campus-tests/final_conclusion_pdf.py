"""
Generates the Final Conclusion PDF: every candidate whose Technical
Discussion decision is "selected" or "hold" (Hold stays on the list as
the waitlist reference for filling seats if a Selected candidate doesn't
join), tabulated with their key profile fields for the college to match
against a joining list.

Usage (as a library, called from webui.py):
    from final_conclusion_pdf import generate_final_conclusion_pdf
    pdf_bytes = generate_final_conclusion_pdf(rows, drive_name)
"""

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

ACCENT = colors.HexColor("#1a7ee8")
INK = colors.HexColor("#12151c")
INK_SOFT = colors.HexColor("#545b68")
ROW_ALT = colors.HexColor("#f5f8fc")
LINE = colors.HexColor("#dde5f0")
SELECTED_GREEN = colors.HexColor("#1a8a4c")
HOLD_AMBER = colors.HexColor("#a86a00")


def generate_final_conclusion_pdf(rows: list[dict], drive_name: str) -> bytes:
    """rows: list of {reg_no, name, gender, degree, stream, email, status, decision_at}"""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        topMargin=18 * mm, bottomMargin=16 * mm, leftMargin=16 * mm, rightMargin=16 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Title"], textColor=INK, fontSize=18, spaceAfter=4)
    sub_style = ParagraphStyle("Sub", parent=styles["Normal"], textColor=INK_SOFT, fontSize=10, spaceAfter=18)

    story = [
        Paragraph("Aizentify Campus Console — Final Conclusion", title_style),
        Paragraph(f"Drive: {drive_name} &nbsp;&middot;&nbsp; Status: Selected + Hold", sub_style),
    ]

    if not rows:
        story.append(Paragraph("No candidates marked Selected or Hold yet.", styles["Normal"]))
    else:
        header = ["#", "Reg No.", "Name", "Gender", "Degree", "Stream", "Personal Email ID", "Status", "Decided"]
        table_data = [header]
        for i, r in enumerate(rows, start=1):
            table_data.append([
                str(i), r["reg_no"], r["name"], r["gender"], r["degree"], r["stream"],
                r["email"], r["status"], r.get("decision_at") or "—",
            ])

        col_widths = [8 * mm, 24 * mm, 32 * mm, 16 * mm, 18 * mm, 45 * mm, 55 * mm, 18 * mm, 21 * mm]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        style = TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 1), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.5, LINE),
            ("TEXTCOLOR", (0, 1), (-1, -1), INK),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (7, 1), (7, -1), "Helvetica-Bold"),
        ])
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                style.add("BACKGROUND", (0, i), (-1, i), ROW_ALT)
            status_color = SELECTED_GREEN if table_data[i][7] == "Selected" else HOLD_AMBER
            style.add("TEXTCOLOR", (7, i), (7, i), status_color)
        table.setStyle(style)
        story.append(table)
        story.append(Spacer(1, 16))
        n_selected = sum(1 for r in rows if r["status"] == "Selected")
        n_hold = sum(1 for r in rows if r["status"] == "Hold")
        story.append(Paragraph(f"{n_selected} Selected &middot; {n_hold} Hold ({len(rows)} total).", sub_style))

    doc.build(story)
    return buf.getvalue()
