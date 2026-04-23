"""
email_scheduler/pdf_generator.py
Generates the scheduled email PDF using the same real report_generator.py
that powers the dashboard download button — same charts, same KPIs, same data.
"""

import os
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

REPORT_OUTPUT_DIR = Path("reports/output")
REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REPORT_TYPES = {
    "summary":     "Executive Summary Report",
    "insights":    "Data Insights Report",
    "dashboard":   "Dashboard Overview Report",
    "performance": "Performance Metrics Report",
    "full":        "Full Analytics Report",
}


class PDFReportGenerator:
    """
    Generates PDF reports for scheduled email delivery.
    Uses the same generate_report_pdf() as the dashboard download button
    so the emailed report is identical to what users can download manually.
    """

    def generate(self, report_type: str, schedule_id: int = None,
                 df: pd.DataFrame = None) -> str:
        """
        Generate a PDF report and return the file path.

        Args:
            report_type:  One of REPORT_TYPES keys
            schedule_id:  Associated schedule ID (for filename)
            df:           The active dataset DataFrame. If None, loads the
                          default CSV so the report always has real data.

        Returns:
            Absolute path to the generated PDF file
        """
        timestamp = datetime.utcnow()
        filename  = f"report_{report_type}_{timestamp.strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = REPORT_OUTPUT_DIR / filename

        # ── Load dataset ──────────────────────────────────────────────────
        if df is None or df.empty:
            df = self._load_default_df()

        # ── Build report inputs (same as api.py _prepare_report_inputs) ──
        try:
            from report_generator import generate_report_pdf
            kpis, ml_results, forecast_data, insights, charts = \
                self._prepare_inputs(df)

            pdf_bytes = generate_report_pdf(
                df, kpis, ml_results, forecast_data, insights, charts
            )

            with open(output_path, "wb") as f:
                f.write(pdf_bytes)

            logger.info(f"PDF generated using real data: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.exception(f"Real report generation failed, using fallback: {e}")
            return self._generate_fallback(report_type, schedule_id, output_path)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _load_default_df(self) -> pd.DataFrame:
        """Load the default sales CSV as a fallback data source."""
        csv_path = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'SALES_DATA_SETT.csv'
        )
        try:
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
            df["Order Date"] = pd.to_datetime(df["Order Date"], dayfirst=True, errors="coerce")
            df["Ship Date"]  = pd.to_datetime(df["Ship Date"],  dayfirst=True, errors="coerce")
            if "shipping_delay_days" not in df.columns:
                df["shipping_delay_days"] = (
                    df["Ship Date"] - df["Order Date"]
                ).dt.days.fillna(0)
            return df
        except Exception as e:
            logger.warning(f"Could not load default CSV: {e}")
            return pd.DataFrame()

    def _prepare_inputs(self, df: pd.DataFrame):
        """
        Mirror api.py's _prepare_report_inputs() so the email PDF
        is built with the exact same logic as the download button.
        """
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

        from dashboard.data_analysis import get_column_types
        from dashboard.kpi_generator import generate_kpis

        col_types = get_column_types(df)
        raw_kpis  = generate_kpis(df, col_types)
        # generate_kpis returns list of tuples (label, value, sub)
        kpis = raw_kpis if raw_kpis else []

        # Forecast — only for sales datasets
        forecast_data = None
        try:
            from analytics.predictive_engine import SalesPredictiveEngine
            if "Sales" in df.columns and "Order Date" in df.columns:
                engine = SalesPredictiveEngine(df=df.copy())
                import contextlib, io as _io
                with contextlib.redirect_stdout(_io.StringIO()):
                    raw = engine.run_full_forecast()
                linear = raw.get("linear_forecast", pd.DataFrame())
                if isinstance(linear, pd.DataFrame) and not linear.empty:
                    report_df = linear.reset_index().rename(columns={
                        "Period": "ds",
                        "Predicted Sales": "yhat",
                        "Lower Bound (95%)": "yhat_lower",
                        "Upper Bound (95%)": "yhat_upper",
                    })
                    forecast_data = {
                        "model": "Linear trend + seasonal adjustment",
                        "forecast_df": report_df,
                    }
        except Exception:
            forecast_data = None

        # Insights
        insights_list = self._build_insights(df)
        insights = "\n".join(insights_list) if insights_list else "No insights available."

        # Charts dict (report_generator builds its own from df, but pass anyway)
        charts = {}

        return kpis, None, forecast_data, insights, charts

    def _build_insights(self, df: pd.DataFrame) -> list:
        """Generate insights from the dataset."""
        try:
            from analytics.insights import generate_ai_insights
            if "Sales" in df.columns:
                kpis_dict = {
                    "total_sales":    float(df["Sales"].sum()),
                    "total_profit":   float(df["Profit"].sum()) if "Profit" in df.columns else 0,
                    "total_orders":   int(df["Order ID"].nunique()) if "Order ID" in df.columns else len(df),
                    "total_quantity": int(df["Quantity"].sum()) if "Quantity" in df.columns else 0,
                    "unique_customers": int(df["Customer ID"].nunique()) if "Customer ID" in df.columns else 0,
                    "avg_order_value": float(df["Sales"].sum()) / max(1, int(df["Order ID"].nunique()) if "Order ID" in df.columns else len(df)),
                    "avg_discount":   float(df["Discount"].mean()) if "Discount" in df.columns else 0,
                    "avg_shipping_delay": float(df["shipping_delay_days"].mean()) if "shipping_delay_days" in df.columns else 0,
                }
                return generate_ai_insights(kpis_dict)
        except Exception:
            pass

        # Generic fallback
        insights = [f"Dataset contains {len(df):,} rows and {len(df.columns)} columns."]
        num_cols = df.select_dtypes(include="number").columns.tolist()
        for col in num_cols[:3]:
            try:
                insights.append(
                    f"{col}: total={df[col].sum():,.2f}, avg={df[col].mean():,.2f}"
                )
            except Exception:
                pass
        return insights

    def _generate_fallback(self, report_type: str, schedule_id,
                           output_path: Path) -> str:
        """
        Minimal ReportLab fallback if the main generator fails entirely.
        Still better than fake data — shows an error notice.
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet

            doc    = SimpleDocTemplate(str(output_path), pagesize=A4)
            styles = getSampleStyleSheet()
            story  = [
                Paragraph("Zero Click AI — Scheduled Report", styles["Title"]),
                Spacer(1, 20),
                Paragraph(
                    f"Report Type: {REPORT_TYPES.get(report_type, report_type)}",
                    styles["Normal"]
                ),
                Spacer(1, 10),
                Paragraph(
                    f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
                    styles["Normal"]
                ),
                Spacer(1, 20),
                Paragraph(
                    "The full report could not be generated at this time. "
                    "Please log in to the dashboard to download the report manually.",
                    styles["Normal"]
                ),
            ]
            doc.build(story)
            return str(output_path)
        except Exception as e:
            logger.error(f"Fallback PDF also failed: {e}")
            return str(output_path)
