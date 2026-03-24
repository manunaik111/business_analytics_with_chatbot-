# report_generator.py  (reportlab rewrite — professional styling)
# Generates a polished PDF sales report from raw data dicts.

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate

# ── Brand palette ────────────────────────────────────────────────────────────
PURPLE      = colors.HexColor("#4A235A")
PURPLE_LIGHT= colors.HexColor("#7D3C98")
PURPLE_BG   = colors.HexColor("#F5EEF8")
PURPLE_ROW  = colors.HexColor("#EBD5F5")
WHITE       = colors.white
GREY_TEXT   = colors.HexColor("#555555")
GREY_LIGHT  = colors.HexColor("#F9F9F9")
GREY_BORDER = colors.HexColor("#CCCCCC")
GREEN       = colors.HexColor("#1E8449")
RED         = colors.HexColor("#C0392B")
BLACK       = colors.black

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm


# ── Header / Footer via canvas ────────────────────────────────────────────────
def _header_footer(canvas, doc):
    canvas.saveState()
    w, h = A4

    # Header bar
    canvas.setFillColor(PURPLE)
    canvas.rect(0, h - 22*mm, w, 22*mm, fill=1, stroke=0)

    # Title in header
    canvas.setFont("Helvetica-Bold", 14)
    canvas.setFillColor(WHITE)
    canvas.drawCentredString(w / 2, h - 13*mm, "AI Sales Analytics Dashboard")

    # Subtitle
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#D7BDE2"))
    canvas.drawCentredString(w / 2, h - 18*mm, "Sales Performance Report")

    # Thin accent line below header
    canvas.setStrokeColor(PURPLE_LIGHT)
    canvas.setLineWidth(1.5)
    canvas.line(MARGIN, h - 23*mm, w - MARGIN, h - 23*mm)

    # Footer bar
    canvas.setFillColor(PURPLE)
    canvas.rect(0, 0, w, 12*mm, fill=1, stroke=0)
    canvas.setFont("Helvetica-Oblique", 8)
    canvas.setFillColor(colors.HexColor("#D7BDE2"))
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    canvas.drawString(MARGIN, 4*mm, f"Generated on {generated}")
    canvas.drawRightString(w - MARGIN, 4*mm, f"Page {doc.page}")

    canvas.restoreState()


# ── Styles ────────────────────────────────────────────────────────────────────
def _styles():
    base = getSampleStyleSheet()
    return {
        "section": ParagraphStyle(
            "section",
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=WHITE,
            backColor=PURPLE,
            leading=18,
            leftIndent=6,
            spaceAfter=0,
        ),
        "kpi_label": ParagraphStyle(
            "kpi_label",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=PURPLE,
            leading=14,
        ),
        "kpi_value": ParagraphStyle(
            "kpi_value",
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=BLACK,
            leading=18,
            alignment=TA_RIGHT,
        ),
        "note": ParagraphStyle(
            "note",
            fontName="Helvetica-Oblique",
            fontSize=7.5,
            textColor=GREY_TEXT,
            leading=10,
        ),
    }


# ── Section title block ───────────────────────────────────────────────────────
def _section_title(title, styles):
    p = Paragraph(f"&nbsp;&nbsp;{title}", styles["section"])
    return [p, Spacer(1, 3*mm)]


# ── KPI cards (2-column grid) ─────────────────────────────────────────────────
def _kpi_section(kpis, styles):
    """kpis: list of (label, value) tuples"""
    rows = []
    for i in range(0, len(kpis), 2):
        pair = kpis[i: i + 2]
        cells = []
        for label, value in pair:
            inner = Table(
                [[Paragraph(label, styles["kpi_label"])],
                 [Paragraph(value, styles["kpi_value"])]],
                colWidths=["100%"],
            )
            inner.setStyle(TableStyle([
                ("BACKGROUND",  (0, 0), (-1, -1), PURPLE_BG),
                ("TOPPADDING",  (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING",  (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("ROUNDEDCORNERS", [4]),
            ]))
            cells.append(inner)
        if len(cells) == 1:
            cells.append("")       # pad odd count
        rows.append(cells)

    avail = PAGE_W - 2 * MARGIN
    col_w = (avail - 6*mm) / 2

    t = Table(rows, colWidths=[col_w, col_w], spaceBefore=0)
    t.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ("COLPADDING",   (0, 0), (-1, -1), 3),
    ]))
    return [t, Spacer(1, 6*mm)]


# ── Generic data table ────────────────────────────────────────────────────────
def _data_table(headers, rows, col_widths=None):
    avail = PAGE_W - 2 * MARGIN
    n = len(headers)

    if col_widths is None:
        col_widths = [avail / n] * n

    style_cells = ParagraphStyle(
        "tc", fontName="Helvetica", fontSize=8.5,
        textColor=BLACK, leading=11, wordWrap="CJK"
    )
    style_header = ParagraphStyle(
        "th", fontName="Helvetica-Bold", fontSize=8.5,
        textColor=WHITE, leading=11
    )

    header_row = [Paragraph(h, style_header) for h in headers]
    data_rows = []
    for row in rows:
        data_rows.append([Paragraph(str(c), style_cells) for c in row])

    table_data = [header_row] + data_rows

    t = Table(table_data, colWidths=col_widths, repeatRows=1)

    row_styles = [
        ("BACKGROUND",   (0, 0), (-1, 0),  PURPLE),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, PURPLE_BG]),
        ("GRID",         (0, 0), (-1, -1), 0.4, GREY_BORDER),
        ("LINEBELOW",    (0, 0), (-1, 0),  1.2, PURPLE_LIGHT),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ]
    t.setStyle(TableStyle(row_styles))
    return [t, Spacer(1, 6*mm)]


# ── Main generator ────────────────────────────────────────────────────────────
def generate_pdf_report_rl(data: dict) -> bytes:
    """
    data keys expected:
      kpis          : list of (label, value)
      region_rows   : list of [region, sales, profit, orders]
      category_rows : list of [category, sales, profit, orders]
      product_rows  : list of [name, sales, profit]
      monthly_rows  : list of [month, sales, orders]
    """
    buf = io.BytesIO()

    doc = BaseDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=27*mm,
        bottomMargin=16*mm,
    )

    frame = Frame(
        MARGIN, 16*mm,
        PAGE_W - 2*MARGIN, PAGE_H - 27*mm - 16*mm,
        id="main"
    )
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame],
                                       onPage=_header_footer)])

    styles = _styles()
    story  = []

    # ── KPI ──────────────────────────────────────────────────────────────────
    story += _section_title("Key Performance Indicators", styles)
    story += _kpi_section(data["kpis"], styles)

    # ── Sales by Region ───────────────────────────────────────────────────────
    story += _section_title("Sales by Region", styles)
    story += _data_table(
        ["Region", "Total Sales", "Total Profit", "Orders"],
        data["region_rows"],
        col_widths=[55*mm, 45*mm, 45*mm, 30*mm],
    )

    # ── Sales by Category ─────────────────────────────────────────────────────
    story += _section_title("Sales by Category", styles)
    story += _data_table(
        ["Category", "Total Sales", "Total Profit", "Orders"],
        data["category_rows"],
        col_widths=[60*mm, 45*mm, 45*mm, 25*mm],
    )

    # ── Top 10 Products ───────────────────────────────────────────────────────
    story += _section_title("Top 10 Products by Sales", styles)
    story += _data_table(
        ["Product Name", "Total Sales", "Total Profit"],
        data["product_rows"],
        col_widths=[115*mm, 38*mm, 22*mm],
    )

    # ── Monthly Trend ─────────────────────────────────────────────────────────
    if data.get("monthly_rows"):
        story += _section_title("Monthly Sales Trend", styles)
        story += _data_table(
            ["Month", "Total Sales", "Orders"],
            data["monthly_rows"],
            col_widths=[58*mm, 58*mm, 59*mm],
        )

    doc.build(story)
    return buf.getvalue()


# ── Standalone demo (uses hardcoded data from the uploaded report) ─────────────
if __name__ == "__main__":
    demo_data = {
        "kpis": [
            ("Total Sales",          "$2,297,200.86"),
            ("Total Profit",         "$286,397.02"),
            ("Total Orders",         "9,994"),
            ("Average Order Value",  "$229.86"),
            ("Overall Profit Margin","12.5%"),
        ],
        "region_rows": [
            ["West",    "$725,458", "$108,418", "3,203"],
            ["East",    "$678,781", "$91,523",  "2,848"],
            ["Central", "$501,240", "$39,706",  "2,323"],
            ["South",   "$391,722", "$46,749",  "1,620"],
        ],
        "category_rows": [
            ["Technology",     "$836,154", "$145,455", "1,847"],
            ["Furniture",      "$742,000", "$18,451",  "2,121"],
            ["Office Supplies","$719,047", "$122,491", "6,026"],
        ],
        "product_rows": [
            ["Canon imageCLASS 2200 Advanced Copier",                    "$61,600",  "$25,200"],
            ["Fellowes PB500 Electric Punch Plastic Comb Binding Machine","$27,453",  "$7,753"],
            ["Cisco TelePresence System EX90 Videoconferencing Unit",    "$22,638",  "-$1,811"],
            ["HON 5400 Series Task Chairs for Big and Tall",             "$21,871",  "$0"],
            ["GBC DocuBind TL300 Electric Binding System",               "$19,823",  "$2,234"],
            ["GBC Ibimaster 500 Manual ProClick Binding System",         "$19,024",  "$761"],
            ["Hewlett Packard LaserJet 3310 Copier",                     "$18,840",  "$6,984"],
            ["HP Designjet T520 Inkjet Large Format Printer",            "$18,375",  "$4,095"],
            ["GBC DocuBind P400 Electric Binding System",                "$17,965",  "-$1,878"],
            ["High Speed Automatic Electric Letter Opener",              "$17,030",  "-$262"],
        ],
        "monthly_rows": [
            ["2019-01", "$47,961", "206"],
            ["2019-02", "$44,950", "199"],
            ["2019-03", "$44,704", "210"],
            ["2019-04", "$47,600", "202"],
            ["2019-05", "$66,415", "239"],
            ["2019-06", "$52,509", "197"],
            ["2019-07", "$44,217", "234"],
            ["2019-08", "$52,786", "205"],
            ["2019-09", "$47,374", "179"],
            ["2019-10", "$58,836", "252"],
            ["2019-11", "$51,559", "215"],
            ["2019-12", "$48,016", "222"],
        ],
    }

    pdf_bytes = generate_pdf_report_rl(demo_data)
    out_path = "/mnt/user-data/outputs/sales_report_fixed.pdf"
    with open(out_path, "wb") as f:
        f.write(pdf_bytes)
    print(f"Saved → {out_path}  ({len(pdf_bytes):,} bytes)")
