"""
reports/pdf_generator.py
FR 5.3 - Steps 28-29: PDF report generation via ReportLab (Team 4 module).

Generates polished PDF reports from the latest dashboard/insights data.
"""

import os
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

REPORT_OUTPUT_DIR = Path("reports/output")
REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ── Report Type Registry ────────────────────────────────────────────────────────
REPORT_TYPES = {
    "summary":     "Executive Summary Report",
    "insights":    "Data Insights Report",
    "dashboard":   "Dashboard Overview Report",
    "performance": "Performance Metrics Report",
    "full":        "Full Analytics Report",
}


class PDFReportGenerator:
    """
    Generates PDF reports using ReportLab.
    Interfaces with Team 4 Visualization module for chart data.
    """

    def generate(self, report_type: str, schedule_id: int = None) -> str:
        """
        Generate a PDF report and return the file path.

        Args:
            report_type:  One of REPORT_TYPES keys
            schedule_id:  Associated schedule ID (for filename)

        Returns:
            Absolute path to the generated PDF file
        """
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table,
            TableStyle, HRFlowable, KeepTogether
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

        title = REPORT_TYPES.get(report_type, "Analytics Report")
        timestamp = datetime.utcnow()
        filename = f"report_{report_type}_{timestamp.strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = REPORT_OUTPUT_DIR / filename

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=25*mm,
            bottomMargin=20*mm,
        )

        styles = getSampleStyleSheet()
        brand_color = colors.HexColor("#1a1a2e")
        accent_color = colors.HexColor("#e94560")
        light_bg = colors.HexColor("#f4f6fb")

        # Custom styles
        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Title"],
            fontSize=22,
            textColor=brand_color,
            spaceAfter=4,
            fontName="Helvetica-Bold",
        )
        subtitle_style = ParagraphStyle(
            "Subtitle",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#666677"),
            spaceAfter=2,
        )
        section_style = ParagraphStyle(
            "SectionHead",
            parent=styles["Heading2"],
            fontSize=13,
            textColor=brand_color,
            fontName="Helvetica-Bold",
            spaceBefore=14,
            spaceAfter=6,
            borderPad=4,
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=9.5,
            leading=15,
            textColor=colors.HexColor("#333344"),
        )
        kpi_label_style = ParagraphStyle(
            "KPILabel",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#999aaa"),
            fontName="Helvetica",
            alignment=TA_CENTER,
        )
        kpi_value_style = ParagraphStyle(
            "KPIValue",
            parent=styles["Normal"],
            fontSize=20,
            textColor=brand_color,
            fontName="Helvetica-Bold",
            alignment=TA_CENTER,
        )

        story = []

        # ── Cover / Header ──────────────────────────────────────────────────
        story.append(Spacer(1, 8*mm))
        story.append(Paragraph(title, title_style))
        story.append(Paragraph(
            f"Generated: {timestamp.strftime('%B %d, %Y at %H:%M UTC')}  |  "
            f"Schedule ID: {schedule_id or 'N/A'}  |  Type: {report_type.upper()}",
            subtitle_style
        ))
        story.append(HRFlowable(
            width="100%", thickness=2, color=accent_color, spaceAfter=10
        ))

        # ── KPI Summary Cards ───────────────────────────────────────────────
        story.append(Paragraph("Key Performance Indicators", section_style))

        kpi_data = self._fetch_kpi_data(report_type)
        kpi_table_data = []
        row_labels = []
        row_values = []
        for kpi in kpi_data:
            row_labels.append(Paragraph(kpi["label"], kpi_label_style))
            row_values.append(Paragraph(kpi["value"], kpi_value_style))

        kpi_table = Table(
            [row_labels, row_values],
            colWidths=[38*mm] * len(kpi_data),
            rowHeights=[12*mm, 16*mm],
        )
        kpi_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), light_bg),
            ("ROUNDEDCORNERS", [4]),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dde0ee")),
            ("LINEAFTER", (0, 0), (-2, -1), 0.5, colors.HexColor("#dde0ee")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 6*mm))

        # ── Data Table Section ──────────────────────────────────────────────
        story.append(Paragraph("Detailed Metrics", section_style))
        story.append(Paragraph(
            "The following table presents aggregated metrics from the reporting period.",
            body_style
        ))
        story.append(Spacer(1, 3*mm))

        table_data = self._fetch_table_data(report_type)
        if table_data:
            header = table_data[0]
            rows = table_data[1:]

            styled_header = [
                Paragraph(f"<b>{cell}</b>", ParagraphStyle(
                    "TH", parent=styles["Normal"], fontSize=9,
                    textColor=colors.white, fontName="Helvetica-Bold", alignment=TA_CENTER
                )) for cell in header
            ]
            col_w = (170*mm) / len(header)

            t = Table(
                [styled_header] + rows,
                colWidths=[col_w] * len(header),
                repeatRows=1,
            )
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), brand_color),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, light_bg]),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dde0ee")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ]))
            story.append(t)

        story.append(Spacer(1, 6*mm))

        # ── Insights Section ────────────────────────────────────────────────
        story.append(Paragraph("Automated Insights", section_style))
        for insight in self._generate_insights(report_type):
            story.append(Paragraph(f"• {insight}", body_style))
            story.append(Spacer(1, 2*mm))

        # ── Footer ──────────────────────────────────────────────────────────
        story.append(Spacer(1, 10*mm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#ccccdd")))
        story.append(Spacer(1, 2*mm))
        story.append(Paragraph(
            f"<font color='#999aaa' size='8'>This report was automatically generated by the "
            f"Email Report Scheduler system on {timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC. "
            f"Confidential — for internal use only.</font>",
            ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, alignment=TA_CENTER)
        ))

        doc.build(story)
        logger.info(f"PDF generated: {output_path}")
        return str(output_path)

    # ── Data Fetch Stubs (replace with real datasource) ──────────────────────
    def _fetch_kpi_data(self, report_type: str) -> list:
        """Fetch KPIs from dashboard/insights data (Team 4 integration point)."""
        return [
            {"label": "Total Users",      "value": "12,847"},
            {"label": "Active Sessions",  "value": "3,291"},
            {"label": "Conversion Rate",  "value": "4.7%"},
            {"label": "Delivery Rate",    "value": "97.2%"},
        ]

    def _fetch_table_data(self, report_type: str) -> list:
        """Fetch tabular data from the database (Team 4 integration point)."""
        return [
            ["Metric", "Previous Period", "Current Period", "Change", "Status"],
            ["Page Views",    "45,231", "51,880", "+14.7%", "↑ Up"],
            ["Unique Visits", "12,100", "13,450", "+11.2%", "↑ Up"],
            ["Bounce Rate",   "38.4%",  "35.1%",  "−3.3%",  "↑ Better"],
            ["Avg. Duration", "2m 14s", "2m 47s", "+24.4%", "↑ Up"],
            ["Conversions",   "562",    "611",    "+8.7%",  "↑ Up"],
            ["Revenue",       "$9,840", "$11,230", "+14.1%","↑ Up"],
        ]

    def _generate_insights(self, report_type: str) -> list:
        """Auto-generate textual insights (Team 4 integration point)."""
        return [
            "Unique visitor count grew 11.2% compared to the previous reporting period.",
            "Bounce rate improvement of 3.3 percentage points indicates higher content engagement.",
            "Revenue increased by 14.1%, exceeding the 10% quarterly growth target.",
            "Email delivery success rate stands at 97.2%, surpassing the 95% SLA target.",
            "Average session duration increased, suggesting improved user experience.",
        ]
