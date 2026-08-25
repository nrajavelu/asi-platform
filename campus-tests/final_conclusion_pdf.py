"""
Generates the Final Conclusion letter: a company-letterhead PDF (logo,
date, addressed to the placement coordinator) requesting confirmation of
Selected candidates for internship, noting that any shortfall will be
filled from Hold based on test-round performance and personal discussion,
followed by the Selected + Hold candidate list. Deliberately generic (no
campus/drive/round name) - it's addressed and sent per campus separately,
not auto-labeled with internal naming.

Usage (as a library, called from webui.py):
    from final_conclusion_pdf import generate_final_conclusion_pdf
    pdf_bytes = generate_final_conclusion_pdf(rows)
"""

import io
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT

ACCENT = colors.HexColor("#1a7ee8")
INK = colors.HexColor("#12151c")
INK_SOFT = colors.HexColor("#545b68")
ROW_ALT = colors.HexColor("#f5f8fc")
LINE = colors.HexColor("#dde5f0")
SELECTED_GREEN = colors.HexColor("#1a8a4c")
HOLD_AMBER = colors.HexColor("#a86a00")

LOGO_PATH = Path(__file__).parent / "static" / "brand-logo-header.png"
LOGO_PX_W, LOGO_PX_H = 1332, 218


def generate_final_conclusion_pdf(rows: list[dict]) -> bytes:
    """rows: list of {reg_no, name, gender, degree, stream, email, status, decision_at}"""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        topMargin=16 * mm, bottomMargin=18 * mm, leftMargin=20 * mm, rightMargin=20 * mm,
    )
    styles = getSampleStyleSheet()
    date_style = ParagraphStyle("Date", parent=styles["Normal"], textColor=INK_SOFT, fontSize=10, alignment=TA_RIGHT)
    body_style = ParagraphStyle("Body", parent=styles["Normal"], textColor=INK, fontSize=10.5, leading=15, spaceAfter=8)
    sub_style = ParagraphStyle("Sub", parent=styles["Normal"], textColor=INK_SOFT, fontSize=9.5, spaceAfter=6)
    sign_style = ParagraphStyle("Sign", parent=styles["Normal"], textColor=INK, fontSize=10.5, leading=15)

    story = []
    if LOGO_PATH.exists():
        logo_w = 60 * mm
        logo_h = logo_w * LOGO_PX_H / LOGO_PX_W
        story.append(Image(str(LOGO_PATH), width=logo_w, height=logo_h))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.2, color=ACCENT, spaceAfter=14))

    story.append(Paragraph(datetime.now().strftime("%d %B %Y"), date_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("To,<br/>The Placement Coordinator,", body_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Subject: Confirmation of Selected Candidates — Campus Recruitment Drive</b>", body_style))

    story.append(Paragraph("Dear Placement Coordinator,", body_style))
    story.append(Paragraph(
        "Please find below the list of candidates <b>Shortlisted</b> and placed on <b>Hold</b>, following the "
        "completion of all assessment rounds and personal discussion conducted as part of our campus "
        "recruitment drive for selecting interns.",
        body_style,
    ))
    story.append(Paragraph(
        "We request you to kindly coordinate with the Selected candidates and confirm their acceptance for "
        "internship at the earliest. Should there be any shortfall against our requirement, the vacancy will "
        "be filled from the Hold list, based on the candidates' performance across the test rounds and the "
        "personal discussion.",
        body_style,
    ))
    story.append(Paragraph(
        "Please find the list of Selected and Hold candidates below for your reference and coordination.",
        body_style,
    ))
    story.append(Spacer(1, 6))

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
        story.append(Spacer(1, 10))
        n_selected = sum(1 for r in rows if r["status"] == "Selected")
        n_hold = sum(1 for r in rows if r["status"] == "Hold")
        story.append(Paragraph(f"{n_selected} Selected &middot; {n_hold} Hold ({len(rows)} total).", sub_style))

    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "We look forward to your confirmation and continued coordination for this campus visit.",
        body_style,
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Regards,<br/><b>Aizentify LLP</b>", sign_style))

    doc.build(story)
    return buf.getvalue()
