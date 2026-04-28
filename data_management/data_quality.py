import pandas as pd
import numpy as np
import io
import re
from datetime import datetime

# ── Optional: plotting (Streamlit UI functions only) ─────────────────────────
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import seaborn as sns
    HAS_PLOTTING = True
except ImportError:
    plt = None          # type: ignore[assignment]
    mpatches = None     # type: ignore[assignment]
    sns = None          # type: ignore[assignment]
    HAS_PLOTTING = False

# ── Optional: Streamlit (data_quality_section UI) ────────────────────────────
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    st = None           # type: ignore[assignment]
    HAS_STREAMLIT = False

# ── Optional: ReportLab (PDF report generation) ──────────────────────────────
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                     TableStyle, HRFlowable, PageBreak)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    HAS_REPORTLAB = True
except ImportError:
    A4 = SimpleDocTemplate = Paragraph = Spacer = Table = None  # type: ignore
    TableStyle = HRFlowable = PageBreak = None                  # type: ignore
    getSampleStyleSheet = ParagraphStyle = colors = cm = None   # type: ignore
    HAS_REPORTLAB = False

# ─────────────────────────────────────────────────────────────
#  1. DUPLICATE ROW DETECTION
# ─────────────────────────────────────────────────────────────

def check_duplicates(df):
    """
    Detect duplicate rows in the DataFrame.
    Returns a dict with count, percentage, and the duplicate rows themselves.
    """
    total_rows   = len(df)
    dup_mask     = df.duplicated(keep=False)       # mark ALL copies
    dup_count    = df.duplicated(keep="first").sum()  # count extra copies
    dup_pct      = round((dup_count / total_rows) * 100, 2) if total_rows else 0
    dup_rows     = df[dup_mask]

    return {
        "count"      : int(dup_count),
        "percentage" : dup_pct,
        "dup_rows"   : dup_rows,
        "has_dupes"  : dup_count > 0,
    }


# ─────────────────────────────────────────────────────────────
#  2. MISSING VALUE ASSESSMENT
# ─────────────────────────────────────────────────────────────

def check_missing_values(df):
    """
    Evaluate missing values per column.
    Returns a DataFrame with count, percentage, and severity label.
    """
    total = len(df)
    missing_counts = df.isnull().sum()
    missing_pct    = (missing_counts / total * 100).round(2)

    def severity(pct):
        if pct == 0:
            return "✅ None"
        elif pct <= 5:
            return "🟢 Low"
        elif pct <= 20:
            return "🟡 Moderate"
        elif pct <= 50:
            return "🟠 High"
        else:
            return "🔴 Critical"

    report = pd.DataFrame({
        "Column"       : df.columns,
        "Missing Count": missing_counts.values,
        "Missing %"    : missing_pct.values,
        "Severity"     : [severity(p) for p in missing_pct.values],
    })
    report = report[report["Missing Count"] > 0].reset_index(drop=True)
    return report


# ─────────────────────────────────────────────────────────────
#  3. OUTLIER DETECTION  (IQR Method)
# ─────────────────────────────────────────────────────────────

def check_outliers(df):
    """
    Apply IQR method to all numeric columns.
    Returns a DataFrame summarising outlier counts per column,
    plus a dict of {col: outlier_indices} for drill-down.
    """
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    rows = []
    outlier_indices = {}

    for col in numeric_cols:
        series = df[col].dropna()
        Q1     = series.quantile(0.25)
        Q3     = series.quantile(0.75)
        IQR    = Q3 - Q1
        lower  = Q1 - 1.5 * IQR
        upper  = Q3 + 1.5 * IQR

        mask    = (df[col] < lower) | (df[col] > upper)
        count   = mask.sum()
        pct     = round(count / len(df) * 100, 2)
        indices = df.index[mask].tolist()
        outlier_indices[col] = indices

        rows.append({
            "Column"        : col,
            "Q1"            : round(Q1, 4),
            "Q3"            : round(Q3, 4),
            "IQR"           : round(IQR, 4),
            "Lower Bound"   : round(lower, 4),
            "Upper Bound"   : round(upper, 4),
            "Outlier Count" : int(count),
            "Outlier %"     : pct,
        })

    report = pd.DataFrame(rows)
    return report, outlier_indices


# ─────────────────────────────────────────────────────────────
#  4. INCONSISTENCY DETECTION
# ─────────────────────────────────────────────────────────────

def check_inconsistencies(df):
    """
    Check for:
      - Mixed data types within object columns
      - Columns that look like dates but are stored as strings
      - Whitespace / casing inconsistencies in categorical columns
      - Columns with suspicious constant or near-constant values
    Returns a list of issue dicts.
    """
    issues = []

    for col in df.columns:
        series = df[col].dropna()
        if series.empty:
            continue

        # ── Mixed numeric + non-numeric in object columns ──
        if df[col].dtype == object:
            numeric_like = pd.to_numeric(series, errors="coerce").notna().sum()
            non_numeric  = series.shape[0] - numeric_like
            if 0 < numeric_like < series.shape[0] and non_numeric > 0:
                issues.append({
                    "Column" : col,
                    "Issue"  : "Mixed Types",
                    "Detail" : f"{numeric_like} numeric-like & {non_numeric} non-numeric values coexist.",
                    "Suggestion": "Standardise column to a single type or split into two columns.",
                })

        # ── Date-like strings stored as object ──
        if df[col].dtype == object:
            sample = series.head(50)
            try:
                parsed = pd.to_datetime(sample, infer_datetime_format=True, errors="coerce")
                hit_rate = parsed.notna().mean()
                if hit_rate >= 0.7 and not pd.api.types.is_datetime64_any_dtype(df[col]):
                    issues.append({
                        "Column" : col,
                        "Issue"  : "Date Stored as String",
                        "Detail" : f"~{round(hit_rate*100)}% of values parse as dates but column type is object.",
                        "Suggestion": "Convert with pd.to_datetime() for proper date operations.",
                    })
            except Exception:
                pass

        # ── Leading / trailing whitespace ──
        if df[col].dtype == object:
            has_ws = series.str.contains(r"^\s|\s$", regex=True, na=False).sum()
            if has_ws > 0:
                issues.append({
                    "Column" : col,
                    "Issue"  : "Whitespace Padding",
                    "Detail" : f"{has_ws} value(s) have leading or trailing spaces.",
                    "Suggestion": "Apply df[col].str.strip() to clean whitespace.",
                })

        # ── Inconsistent casing (e.g. 'Yes', 'yes', 'YES') ──
        if df[col].dtype == object:
            unique_vals  = series.unique()
            lower_unique = pd.Series(unique_vals).str.lower().nunique()
            if lower_unique < len(unique_vals):
                issues.append({
                    "Column" : col,
                    "Issue"  : "Inconsistent Casing",
                    "Detail" : f"Same value appears in multiple cases (e.g. 'Yes' / 'yes' / 'YES').",
                    "Suggestion": "Normalise with df[col].str.lower() or .str.title().",
                })

        # ── Near-constant columns (>= 95% same value) ──
        if series.shape[0] > 0:
            top_freq = series.value_counts(normalize=True).iloc[0]
            if top_freq >= 0.95:
                issues.append({
                    "Column" : col,
                    "Issue"  : "Near-Constant Column",
                    "Detail" : f"'{series.value_counts().index[0]}' makes up {round(top_freq*100, 1)}% of non-null values.",
                    "Suggestion": "Consider dropping this column — low variance adds little analytical value.",
                })

    return issues


# ─────────────────────────────────────────────────────────────
#  5. OVERALL QUALITY SCORE
# ─────────────────────────────────────────────────────────────

def compute_quality_score(df, dup_result, missing_report, outlier_report, inconsistencies):
    """
    Compute a 0–100 quality score from four weighted dimensions.
    """
    total_rows  = len(df)
    total_cells = df.shape[0] * df.shape[1]

    # Completeness (30 pts): penalise missing cells
    missing_cells = df.isnull().sum().sum()
    completeness_score = max(0, 30 * (1 - missing_cells / total_cells)) if total_cells else 30

    # Uniqueness (25 pts): penalise duplicate rows
    dup_pct = dup_result["percentage"]
    uniqueness_score = max(0, 25 * (1 - dup_pct / 100))

    # Consistency (25 pts): penalise each inconsistency issue
    issue_penalty = min(25, len(inconsistencies) * 4)
    consistency_score = 25 - issue_penalty

    # Accuracy (20 pts): penalise outlier-heavy columns
    if not outlier_report.empty:
        avg_outlier_pct = outlier_report["Outlier %"].mean()
        accuracy_score  = max(0, 20 * (1 - avg_outlier_pct / 100))
    else:
        accuracy_score = 20

    total = completeness_score + uniqueness_score + consistency_score + accuracy_score

    return {
        "total"        : round(total, 1),
        "completeness" : round(completeness_score, 1),
        "uniqueness"   : round(uniqueness_score, 1),
        "consistency"  : round(consistency_score, 1),
        "accuracy"     : round(accuracy_score, 1),
    }


def score_label(score):
    if score >= 85:
        return "Excellent", "#34A853"
    elif score >= 70:
        return "Good", "#1A73E8"
    elif score >= 50:
        return "Fair", "#FBBC04"
    elif score >= 30:
        return "Poor", "#EA8600"
    else:
        return "Critical", "#EA4335"


# ─────────────────────────────────────────────────────────────
#  6. VISUALISATIONS
# ─────────────────────────────────────────────────────────────

def plot_quality_gauge(score):
    """Render a semicircular gauge chart for the quality score."""
    fig, ax = plt.subplots(figsize=(5, 3), subplot_kw=dict(aspect="equal"))
    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-0.3, 1.3)
    ax.axis("off")

    # Background arc
    theta = np.linspace(np.pi, 0, 300)
    ax.plot(np.cos(theta), np.sin(theta), color="#E8EAED", linewidth=18, solid_capstyle="round")

    # Coloured arc proportional to score
    fill_theta = np.linspace(np.pi, np.pi - (score / 100) * np.pi, 300)
    _, color = score_label(score)
    ax.plot(np.cos(fill_theta), np.sin(fill_theta), color=color, linewidth=18, solid_capstyle="round")

    # Score text
    ax.text(0, 0.18, f"{score}", ha="center", va="center",
            fontsize=36, fontweight="bold", color=color)
    ax.text(0, -0.08, "/100", ha="center", va="center",
            fontsize=13, color="#666666")
    label, _ = score_label(score)
    ax.text(0, -0.22, label, ha="center", va="center",
            fontsize=13, fontweight="bold", color=color)

    plt.tight_layout()
    return fig


def plot_dimension_bars(scores):
    """Horizontal bar chart for the four quality dimensions."""
    dims   = ["Completeness", "Uniqueness", "Consistency", "Accuracy"]
    vals   = [scores["completeness"], scores["uniqueness"],
              scores["consistency"],  scores["accuracy"]]
    maxes  = [30, 25, 25, 20]
    colors = ["#34A853", "#1A73E8", "#FBBC04", "#EA4335"]

    fig, ax = plt.subplots(figsize=(7, 3))
    y = np.arange(len(dims))

    # Background bars (max possible)
    ax.barh(y, maxes, color="#F1F3F4", height=0.5, zorder=1)
    # Score bars
    ax.barh(y, vals, color=colors, height=0.5, zorder=2)

    ax.set_yticks(y)
    ax.set_yticklabels(dims, fontsize=10)
    ax.set_xlim(0, 32)
    ax.set_xlabel("Score (out of max)", fontsize=9)
    ax.set_title("Quality Dimensions Breakdown", fontsize=11, fontweight="bold", pad=8)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)

    for i, (v, m) in enumerate(zip(vals, maxes)):
        ax.text(v + 0.3, i, f"{v}/{m}", va="center", fontsize=9, color="#333")

    plt.tight_layout()
    return fig


def plot_outlier_boxplots(df, outlier_report):
    """Box plots for numeric columns highlighting outliers."""
    cols_with_outliers = outlier_report[outlier_report["Outlier Count"] > 0]["Column"].tolist()
    if not cols_with_outliers:
        return None

    n  = len(cols_with_outliers)
    nc = min(3, n)
    nr = (n + nc - 1) // nc
    fig, axes = plt.subplots(nr, nc, figsize=(5 * nc, 3.5 * nr))
    axes = np.array(axes).flatten()

    for i, col in enumerate(cols_with_outliers):
        bp = axes[i].boxplot(
            df[col].dropna(),
            vert=True, patch_artist=True,
            boxprops=dict(facecolor="#D2E3FC", color="#1A73E8"),
            medianprops=dict(color="#EA4335", linewidth=2),
            flierprops=dict(marker="o", color="#EA4335", alpha=0.5, markersize=4),
            whiskerprops=dict(color="#1A73E8"),
            capprops=dict(color="#1A73E8"),
        )
        axes[i].set_title(col, fontsize=10, fontweight="bold")
        axes[i].set_ylabel("Value", fontsize=8)
        axes[i].tick_params(axis="x", which="both", bottom=False, labelbottom=False)

    for j in range(n, len(axes)):
        axes[j].set_visible(False)

    plt.suptitle("Outlier Distribution — Box Plots (IQR Method)", fontsize=13,
                 fontweight="bold", y=1.01)
    plt.tight_layout()
    return fig


# ─────────────────────────────────────────────────────────────
#  7. WARNINGS & SUGGESTIONS GENERATOR
# ─────────────────────────────────────────────────────────────

def generate_warnings(dup_result, missing_report, outlier_report, inconsistencies, scores):
    """
    Compile a prioritised list of warnings and actionable suggestions.
    Returns list of dicts: {level, icon, warning, suggestion}
    """
    warnings = []

    # Duplicates
    if dup_result["has_dupes"]:
        level = "🔴 Critical" if dup_result["percentage"] > 10 else "🟠 Warning"
        warnings.append({
            "level"     : level,
            "warning"   : f"{dup_result['count']} duplicate rows detected ({dup_result['percentage']}% of dataset).",
            "suggestion": "Remove duplicates with df.drop_duplicates(). Investigate why they exist before dropping.",
        })

    # Missing values
    if not missing_report.empty:
        critical_missing = missing_report[missing_report["Missing %"] > 50]
        high_missing     = missing_report[(missing_report["Missing %"] > 20) & (missing_report["Missing %"] <= 50)]
        moderate_missing = missing_report[(missing_report["Missing %"] > 5)  & (missing_report["Missing %"] <= 20)]

        for _, row in critical_missing.iterrows():
            warnings.append({
                "level"     : "🔴 Critical",
                "warning"   : f"Column '{row['Column']}' has {row['Missing %']}% missing values.",
                "suggestion": "Consider dropping this column or using domain knowledge to impute values.",
            })
        for _, row in high_missing.iterrows():
            warnings.append({
                "level"     : "🟠 Warning",
                "warning"   : f"Column '{row['Column']}' has {row['Missing %']}% missing values.",
                "suggestion": "Use mean/median imputation for numeric, or mode/constant for categorical.",
            })
        for _, row in moderate_missing.iterrows():
            warnings.append({
                "level"     : "🟡 Notice",
                "warning"   : f"Column '{row['Column']}' has {row['Missing %']}% missing values.",
                "suggestion": "Evaluate whether to impute or flag these rows separately.",
            })

    # Outliers
    if not outlier_report.empty:
        severe_outlier_cols = outlier_report[outlier_report["Outlier %"] > 10]["Column"].tolist()
        mild_outlier_cols   = outlier_report[(outlier_report["Outlier %"] > 2) &
                                              (outlier_report["Outlier %"] <= 10)]["Column"].tolist()
        if severe_outlier_cols:
            warnings.append({
                "level"     : "🟠 Warning",
                "warning"   : f"Severe outliers (>10%) found in: {', '.join(severe_outlier_cols)}.",
                "suggestion": "Investigate these outliers — apply capping (Winsorization) or remove if erroneous.",
            })
        if mild_outlier_cols:
            warnings.append({
                "level"     : "🟡 Notice",
                "warning"   : f"Mild outliers found in: {', '.join(mild_outlier_cols)}.",
                "suggestion": "Review outlier rows — they may be valid extreme values or data entry errors.",
            })

    # Inconsistencies
    for issue in inconsistencies:
        level = "🟠 Warning" if issue["Issue"] in ("Mixed Types", "Date Stored as String") else "🟡 Notice"
        warnings.append({
            "level"     : level,
            "warning"   : f"[{issue['Column']}] {issue['Issue']}: {issue['Detail']}",
            "suggestion": issue["Suggestion"],
        })

    # Overall score
    if scores["total"] < 50:
        warnings.append({
            "level"     : "🔴 Critical",
            "warning"   : f"Overall data quality score is very low ({scores['total']}/100).",
            "suggestion": "Address all critical issues above before using this dataset for analysis.",
        })

    return warnings


# ─────────────────────────────────────────────────────────────
#  8. REPORT DOWNLOAD
# ─────────────────────────────────────────────────────────────

def build_text_report(df, dup_result, missing_report, outlier_report,
                      inconsistencies, warnings, scores):
    """Build a plain-text quality report for download."""
    lines = []
    lines.append("=" * 65)
    lines.append("       AUTOMATED DATA QUALITY ASSESSMENT REPORT")
    lines.append(f"       Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 65)
    lines.append(f"\nDataset Shape : {df.shape[0]} rows × {df.shape[1]} columns")
    lines.append(f"Overall Score : {scores['total']} / 100  ({score_label(scores['total'])[0]})")
    lines.append(f"  Completeness : {scores['completeness']} / 30")
    lines.append(f"  Uniqueness   : {scores['uniqueness']}  / 25")
    lines.append(f"  Consistency  : {scores['consistency']}  / 25")
    lines.append(f"  Accuracy     : {scores['accuracy']}  / 20")

    lines.append("\n" + "─" * 65)
    lines.append("1. DUPLICATE ROWS")
    lines.append("─" * 65)
    lines.append(f"  Duplicate count  : {dup_result['count']}")
    lines.append(f"  Duplicate %      : {dup_result['percentage']}%")

    lines.append("\n" + "─" * 65)
    lines.append("2. MISSING VALUES")
    lines.append("─" * 65)
    if missing_report.empty:
        lines.append("  No missing values detected. ✅")
    else:
        for _, row in missing_report.iterrows():
            lines.append(f"  {row['Column']:30s}  {row['Missing Count']:>5} missing  "
                         f"({row['Missing %']}%)  {row['Severity']}")

    lines.append("\n" + "─" * 65)
    lines.append("3. OUTLIERS  (IQR Method)")
    lines.append("─" * 65)
    if outlier_report.empty:
        lines.append("  No numeric columns found.")
    else:
        for _, row in outlier_report.iterrows():
            lines.append(f"  {row['Column']:30s}  {row['Outlier Count']:>5} outliers  "
                         f"({row['Outlier %']}%)")

    lines.append("\n" + "─" * 65)
    lines.append("4. INCONSISTENCIES")
    lines.append("─" * 65)
    if not inconsistencies:
        lines.append("  No inconsistencies detected. ✅")
    else:
        for issue in inconsistencies:
            lines.append(f"  [{issue['Issue']}]  Column: {issue['Column']}")
            lines.append(f"    Detail     : {issue['Detail']}")
            lines.append(f"    Suggestion : {issue['Suggestion']}")
            lines.append("")

    lines.append("─" * 65)
    lines.append("5. WARNINGS & SUGGESTIONS")
    lines.append("─" * 65)
    if not warnings:
        lines.append("  No warnings. Dataset quality looks good! ✅")
    else:
        for i, w in enumerate(warnings, 1):
            lines.append(f"  {i}. {w['level']}")
            lines.append(f"     ⚠  {w['warning']}")
            lines.append(f"     ➜  {w['suggestion']}")
            lines.append("")

    lines.append("=" * 65)
    lines.append("               END OF REPORT")
    lines.append("=" * 65)
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
#  8b. PDF REPORT GENERATOR
# ─────────────────────────────────────────────────────────────

def generate_pdf_report(df, dup_result, missing_report, outlier_report,
                        inconsistencies, warnings, scores):
    """Generate a styled PDF quality report using ReportLab."""

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    label, _ = score_label(scores["total"])

    # ── Custom styles ──────────────────────────────────────────
    BLUE   = colors.HexColor("#1A73E8")
    GREEN  = colors.HexColor("#34A853")
    RED    = colors.HexColor("#EA4335")
    ORANGE = colors.HexColor("#EA8600")
    YELLOW = colors.HexColor("#FBBC04")
    LGREY  = colors.HexColor("#F1F3F4")
    DGREY  = colors.HexColor("#444444")

    title_style = ParagraphStyle("ReportTitle", parent=styles["Title"],
                                 fontSize=22, textColor=BLUE,
                                 spaceAfter=4, alignment=1)
    subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"],
                                    fontSize=10, textColor=DGREY,
                                    alignment=1, spaceAfter=2)
    h2_style = ParagraphStyle("H2", parent=styles["Heading2"],
                               fontSize=13, textColor=BLUE,
                               spaceBefore=14, spaceAfter=6)
    body_style = ParagraphStyle("Body", parent=styles["Normal"],
                                fontSize=9, leading=14, textColor=DGREY)
    warn_style  = ParagraphStyle("Warn",  parent=body_style, leftIndent=10)
    sugg_style  = ParagraphStyle("Sugg",  parent=body_style, leftIndent=10,
                                 textColor=colors.HexColor("#1B5E20"), fontName="Helvetica-Oblique")

    def hr():
        return HRFlowable(width="100%", thickness=0.5,
                          color=colors.HexColor("#DADCE0"), spaceAfter=8, spaceBefore=4)

    def section_title(text):
        return Paragraph(text, h2_style)

    # ── Score colour ───────────────────────────────────────────
    score_color_map = {
        "Excellent": GREEN,
        "Good"     : BLUE,
        "Fair"     : YELLOW,
        "Poor"     : ORANGE,
        "Critical" : RED,
    }
    sc = score_color_map.get(label, BLUE)

    story = []

    # ── Header ─────────────────────────────────────────────────
    story.append(Paragraph("Automated Data Quality Assessment Report", title_style))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  |  "
        f"Dataset: {df.shape[0]:,} rows x {df.shape[1]} columns",
        subtitle_style))
    story.append(Spacer(1, 6))
    story.append(hr())

    # ── Score summary table ────────────────────────────────────
    score_data = [
        ["Overall Score", "Completeness", "Uniqueness", "Consistency", "Accuracy"],
        [
            Paragraph(f'<font color="#{sc.hexval()[2:]}"><b>{scores["total"]}/100 ({label})</b></font>', body_style),
            f'{scores["completeness"]}/30',
            f'{scores["uniqueness"]}/25',
            f'{scores["consistency"]}/25',
            f'{scores["accuracy"]}/20',
        ]
    ]
    score_table = Table(score_data, colWidths=[3.8*cm, 3*cm, 3*cm, 3*cm, 3*cm])
    score_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 9),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [LGREY, colors.white]),
        ("GRID",          (0, 0), (-1, -1), 0.4, colors.HexColor("#DADCE0")),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 12))

    # ── 1. Duplicates ──────────────────────────────────────────
    story.append(section_title("1. Duplicate Row Detection"))
    story.append(hr())
    dup_data = [
        ["Metric", "Value"],
        ["Duplicate Count", str(dup_result["count"])],
        ["Duplicate %",     f"{dup_result['percentage']}%"],
        ["Status",          "No duplicates found" if not dup_result["has_dupes"] else "Duplicates detected!"],
    ]
    dup_table = Table(dup_data, colWidths=[8*cm, 8.6*cm])
    dup_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [LGREY, colors.white]),
        ("GRID",          (0, 0), (-1, -1), 0.4, colors.HexColor("#DADCE0")),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(dup_table)
    story.append(Spacer(1, 10))

    # ── 2. Missing Values ──────────────────────────────────────
    story.append(section_title("2. Missing Value Assessment"))
    story.append(hr())
    if missing_report.empty:
        story.append(Paragraph("No missing values detected in any column.", body_style))
    else:
        mv_data = [["Column", "Missing Count", "Missing %", "Severity"]]
        for _, row in missing_report.iterrows():
            mv_data.append([row["Column"], str(row["Missing Count"]),
                            f"{row['Missing %']}%", row["Severity"]])
        mv_table = Table(mv_data, colWidths=[6*cm, 4*cm, 4*cm, 4.6*cm])
        mv_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), BLUE),
            ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [LGREY, colors.white]),
            ("GRID",          (0, 0), (-1, -1), 0.4, colors.HexColor("#DADCE0")),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(mv_table)
    story.append(Spacer(1, 10))

    # ── 3. Outliers ────────────────────────────────────────────
    story.append(section_title("3. Outlier Detection (IQR Method)"))
    story.append(hr())
    if outlier_report.empty:
        story.append(Paragraph("No numeric columns found for outlier analysis.", body_style))
    else:
        out_data = [["Column", "Lower Bound", "Upper Bound", "Outlier Count", "Outlier %"]]
        for _, row in outlier_report.iterrows():
            out_data.append([
                row["Column"], str(row["Lower Bound"]), str(row["Upper Bound"]),
                str(row["Outlier Count"]), f"{row['Outlier %']}%"
            ])
        out_table = Table(out_data, colWidths=[5*cm, 3.2*cm, 3.2*cm, 3.2*cm, 3*cm])
        out_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), BLUE),
            ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [LGREY, colors.white]),
            ("GRID",          (0, 0), (-1, -1), 0.4, colors.HexColor("#DADCE0")),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(out_table)
    story.append(Spacer(1, 10))

    # ── 4. Inconsistencies ─────────────────────────────────────
    story.append(section_title("4. Data Inconsistency Detection"))
    story.append(hr())
    if not inconsistencies:
        story.append(Paragraph("No inconsistencies detected.", body_style))
    else:
        inc_data = [["Column", "Issue Type", "Detail"]]
        for issue in inconsistencies:
            inc_data.append([
                issue["Column"], issue["Issue"],
                Paragraph(issue["Detail"], body_style)
            ])
        inc_table = Table(inc_data, colWidths=[4*cm, 4.5*cm, 8.1*cm])
        inc_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), BLUE),
            ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [LGREY, colors.white]),
            ("GRID",          (0, 0), (-1, -1), 0.4, colors.HexColor("#DADCE0")),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(inc_table)
    story.append(Spacer(1, 10))

    # ── 5. Warnings ────────────────────────────────────────────
    story.append(PageBreak())
    story.append(section_title("5. Warnings and Actionable Suggestions"))
    story.append(hr())
    if not warnings:
        story.append(Paragraph("No warnings. Dataset quality looks good!", body_style))
    else:
        for i, w in enumerate(warnings, 1):
            story.append(Paragraph(f"<b>{i}. {w['level']}</b>", warn_style))
            story.append(Paragraph(f"Warning: {w['warning']}", warn_style))
            story.append(Paragraph(f"Suggestion: {w['suggestion']}", sugg_style))
            story.append(Spacer(1, 6))

    doc.build(story)
    buf.seek(0)
    return buf.read()


# ─────────────────────────────────────────────────────────────
#  9. MAIN SECTION  (called from app.py)
# ─────────────────────────────────────────────────────────────

def data_quality_section(df):
    """
    Main function to render the Automated Data Quality Assessment UI.
    Accepts a Pandas DataFrame from st.session_state['uploaded_df'].
    """

    # ── Page Header ─────────────────────────────────────────
    st.title("🔍 Automated Data Quality Assessment")
    st.markdown(
        "Comprehensive quality checks on your dataset — duplicates, missing values, "
        "outliers, and inconsistencies — with an overall quality score and actionable suggestions."
    )
    st.divider()

    # ── Run All Checks ───────────────────────────────────────
    with st.spinner("Running quality checks…"):
        dup_result      = check_duplicates(df)
        missing_report  = check_missing_values(df)
        outlier_report, outlier_indices = check_outliers(df)
        inconsistencies = check_inconsistencies(df)
        scores          = compute_quality_score(df, dup_result, missing_report,
                                                outlier_report, inconsistencies)
        warnings        = generate_warnings(dup_result, missing_report,
                                            outlier_report, inconsistencies, scores)

    # ── Overall Quality Score ────────────────────────────────
    st.subheader("🏆 Overall Data Quality Score")
    label, color = score_label(scores["total"])

    col_gauge, col_dims = st.columns([1, 1.6])

    with col_gauge:
        st.pyplot(plot_quality_gauge(scores["total"]))

    with col_dims:
        st.markdown("<br>", unsafe_allow_html=True)
        st.pyplot(plot_dimension_bars(scores))

    st.divider()

    # ── Quick Stats Banner ───────────────────────────────────
    st.subheader("📋 Quick Summary")
    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Duplicate Rows",
        f"{dup_result['count']}",
        delta=f"{dup_result['percentage']}% of data",
        delta_color="inverse",
    )
    c2.metric(
        "Columns w/ Missing",
        f"{len(missing_report)}",
        delta=f"out of {df.shape[1]} columns",
        delta_color="inverse",
    )
    outlier_cols = int((outlier_report["Outlier Count"] > 0).sum()) if not outlier_report.empty else 0
    c3.metric(
        "Columns w/ Outliers",
        f"{outlier_cols}",
        delta=f"IQR method",
        delta_color="inverse",
    )
    c4.metric(
        "Inconsistency Issues",
        f"{len(inconsistencies)}",
        delta="format & type checks",
        delta_color="inverse",
    )

    st.divider()

    # ── Check 1: Duplicates ──────────────────────────────────
    st.subheader("1️⃣ Duplicate Row Detection")

    if not dup_result["has_dupes"]:
        st.success("✅ No duplicate rows found in this dataset.")
    else:
        st.error(
            f"⚠️ **{dup_result['count']} duplicate rows** detected "
            f"({dup_result['percentage']}% of the dataset)."
        )
        with st.expander("🔎 View Duplicate Rows", expanded=False):
            st.dataframe(dup_result["dup_rows"], use_container_width=True)
        st.info("💡 **Suggestion:** Use `df.drop_duplicates()` to remove extra copies. "
                "Verify whether duplicates are data errors or valid repeated entries.")

    st.divider()

    # ── Check 2: Missing Values ──────────────────────────────
    st.subheader("2️⃣ Missing Value Assessment")

    if missing_report.empty:
        st.success("✅ No missing values found across all columns.")
    else:
        st.warning(f"⚠️ **{len(missing_report)} column(s)** contain missing values.")

        # Colour-code by severity
        def highlight_severity(val):
            colors = {
                "🔴 Critical" : "background-color:#ffcccc",
                "🟠 High"     : "background-color:#ffe0b2",
                "🟡 Moderate" : "background-color:#fff9c4",
                "🟢 Low"      : "background-color:#e8f5e9",
                "✅ None"     : "",
            }
            return colors.get(val, "")

        styled_missing = missing_report.style.map(
            highlight_severity, subset=["Severity"]
        ).format({"Missing %": "{:.2f}%"})

        st.dataframe(styled_missing, use_container_width=True)
        st.caption("🔴 Critical (>50%)  |  🟠 High (20–50%)  |  🟡 Moderate (5–20%)  |  🟢 Low (≤5%)")

    st.divider()

    # ── Check 3: Outliers ────────────────────────────────────
    st.subheader("3️⃣ Outlier Detection (IQR Method)")

    if outlier_report.empty:
        st.info("ℹ️ No numeric columns found for outlier analysis.")
    else:
        has_outliers = outlier_report["Outlier Count"].sum() > 0

        if not has_outliers:
            st.success("✅ No outliers detected in any numeric column.")
        else:
            st.warning(
                f"⚠️ Outliers found in **{outlier_cols} column(s)**. "
                "Review the table and box plots below."
            )

        def highlight_outlier_pct(val):
            try:
                v = float(val)
                if v > 10: return "background-color:#ffcccc"
                elif v > 2: return "background-color:#fff9c4"
                else:       return ""
            except Exception:
                return ""

        styled_outliers = outlier_report.style.map(
            highlight_outlier_pct, subset=["Outlier %"]
        )
        st.dataframe(styled_outliers, use_container_width=True)
        st.caption("🔴 >10% outliers  |  🟡 2–10%  |  ⬜ ≤2%")

        # Box plots
        fig_box = plot_outlier_boxplots(df, outlier_report)
        if fig_box:
            with st.expander("📦 View Box Plots for Columns with Outliers", expanded=True):
                st.pyplot(fig_box)

        st.info("💡 **Suggestion:** Use Winsorization (capping at bounds) or Z-score filtering "
                "to handle severe outliers. Always verify if extreme values are genuine before removing.")

    st.divider()

    # ── Check 4: Inconsistencies ─────────────────────────────
    st.subheader("4️⃣ Data Inconsistency Detection")

    if not inconsistencies:
        st.success("✅ No format or type inconsistencies detected.")
    else:
        st.warning(f"⚠️ **{len(inconsistencies)} inconsistency issue(s)** found.")
        inc_df = pd.DataFrame(inconsistencies)
        st.dataframe(inc_df, use_container_width=True)

    st.divider()

    # ── Warnings & Suggestions Panel ─────────────────────────
    st.subheader("⚠️ Warnings & Actionable Suggestions")

    if not warnings:
        st.success("🎉 No warnings! Your dataset has good quality.")
    else:
        for w in warnings:
            level = w["level"]
            if "Critical" in level:
                st.error(f"**{level}**\n\n{w['warning']}\n\n➜ *{w['suggestion']}*")
            elif "Warning" in level:
                st.warning(f"**{level}**\n\n{w['warning']}\n\n➜ *{w['suggestion']}*")
            else:
                st.info(f"**{level}**\n\n{w['warning']}\n\n➜ *{w['suggestion']}*")

    st.divider()

    # ── Download Report ──────────────────────────────────────
    st.subheader("⬇️ Download Quality Report")

    report_text = build_text_report(
        df, dup_result, missing_report, outlier_report,
        inconsistencies, warnings, scores
    )

    col_dl1, col_dl2, col_dl3 = st.columns(3)

    with col_dl1:
        st.download_button(
            label="📥 Download Full Report (.txt)",
            data=report_text,
            file_name="data_quality_report.txt",
            mime="text/plain",
        )

    with col_dl2:
        pdf_bytes = generate_pdf_report(
            df, dup_result, missing_report, outlier_report,
            inconsistencies, warnings, scores
        )
        st.download_button(
            label="📄 Download Full Report (.pdf)",
            data=pdf_bytes,
            file_name="data_quality_report.pdf",
            mime="application/pdf",
        )

    with col_dl3:
        # CSV of missing report
        if not missing_report.empty:
            csv_buf = io.StringIO()
            missing_report.to_csv(csv_buf, index=False)
            st.download_button(
                label="📥 Download Missing Values (.csv)",
                data=csv_buf.getvalue(),
                file_name="missing_values_summary.csv",
                mime="text/csv",
            )