"""
report_generator.py — PDF + Excel reports matching the reference design image.
Uses ReportLab (PDF) + Matplotlib (charts) + OpenPyXL (Excel).

Reference design features:
  Page 1 : Purple header bar + sub-bar | PERFORMANCE DASHBOARD title |
            6 KPI boxes (2 rows × 3) in multi-colors | AI NARRATED SUMMARY |
            footnote + page stamp
  Page 2 : 6 charts in 2-col grid — Sales by Region (h-bar, cyan),
            Sales by Category (donut, purple), Monthly Sales Trend (area, green),
            Sales vs Profit (scatter, orange), Monthly Orders Trend (bar, blue),
            Seasonality Heatmap (purple gradient)
  Page 3 : Top-16 Products table (purple header, alternating rows, profit green/red)
  Page 4 : ML Insights (icons, green metrics)
  Page 5 : Forecast table (if available)
  Page 6 : Full AI Insights text
  Page 7 : Dataset Sample — first 20 rows

Each chart uses a DIFFERENT accent colour to match the reference visual variety.
"""

import io, os, datetime, warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ── matplotlib ─────────────────────────────────────────────────────────────────
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyBboxPatch
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

# ── ReportLab ──────────────────────────────────────────────────────────────────
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
        Image as RLImage, HRFlowable, PageBreak, KeepTogether,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    HAS_RL = True
except ImportError:
    HAS_RL = False

# ── OpenPyXL ───────────────────────────────────────────────────────────────────
try:
    import openpyxl
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side, GradientFill
    from openpyxl.utils import get_column_letter
    from openpyxl.chart import BarChart, LineChart, PieChart, Reference
    from openpyxl.chart.series import DataPoint
    HAS_OXL = True
except ImportError:
    HAS_OXL = False

NOW = datetime.datetime.now()

# ════════════════════════════════════════════════════════════════════════════════
# COLOUR PALETTE  (reference image uses vibrant, mixed colours)
# ════════════════════════════════════════════════════════════════════════════════
C = {
    # Chart accent colours (each chart gets its own)
    "region":    "#00C9B1",   # teal/cyan
    "category":  "#7C3AED",   # purple
    "trend":     "#22C55E",   # green
    "scatter":   "#F97316",   # orange
    "orders":    "#3B82F6",   # blue
    "heatmap":   "#7C3AED",   # purple
    # Table header
    "hdr":       "#7C3AED",
    "hdr2":      "#5B21B6",
    # KPI box colours (6 different)
    "kpi0": "#06B6D4",   # cyan
    "kpi1": "#22C55E",   # green
    "kpi2": "#3B82F6",   # blue
    "kpi3": "#8B5CF6",   # violet
    "kpi4": "#F59E0B",   # amber
    "kpi5": "#EF4444",   # red (negative demo)
    # UI
    "purple_dark":  "#7C3AED",
    "purple_mid":   "#A78BFA",
    "purple_light": "#EDE9FE",
    "white":        "#FFFFFF",
    "grey":         "#6B7280",
    "bg_alt":       "#F3F0FF",
    "bg_white":     "#FFFFFF",
    "green_pos":    "#16A34A",
    "red_neg":      "#DC2626",
    "row_even":     "#F9F7FF",
    "row_odd":      "#FFFFFF",
}

if HAS_RL:
    def _rc(hex_): return colors.HexColor(hex_)
    RL = {k: _rc(v) for k, v in C.items()}


# ════════════════════════════════════════════════════════════════════════════════
# DATA HELPERS
# ════════════════════════════════════════════════════════════════════════════════
def _col_types(df):
    return {
        "numeric":     df.select_dtypes(include="number").columns.tolist(),
        "categorical": df.select_dtypes(include=["object", "category"]).columns.tolist(),
        "datetime":    df.select_dtypes(include=["datetime64", "datetimetz"]).columns.tolist(),
    }

def _s(df, ct):
    return next((c for c in ct["numeric"] if any(w in c.lower() for w in ["sales","revenue","amount","total"])),
                ct["numeric"][0] if ct["numeric"] else None)

def _p(df, ct):
    return next((c for c in ct["numeric"] if "profit" in c.lower()), None)

def _cat(df, ct):
    return next((c for c in ct["categorical"]
                 if any(w in c.lower() for w in ["categ","type","segment","product"])), None)

def _reg(df, ct):
    return next((c for c in df.columns if "region" in c.lower()), None)

def _group_label(col, fallback):
    return col if col else fallback

def _metric_label(df, ct):
    return _s(df, ct) or "Value"

def _num(x):
    try: return float(x)
    except: return 0.0

def _fmt(v):
    """Format a number for display: $1.23M, $456K, $123"""
    try:
        v = float(v)
        if abs(v) >= 1e6:  return f"${v/1e6:.2f}M"
        if abs(v) >= 1e3:  return f"${v/1e3:.1f}K"
        return f"${v:,.0f}"
    except: return str(v)

def sales_by_region(df, ct):
    rc, sc = _reg(df, ct), _s(df, ct)
    if not rc or not sc:
        return pd.DataFrame({"Region": ["N/A"], "Sales": [0]})
    out = df.groupby(rc)[sc].sum().reset_index().sort_values(sc, ascending=False)
    out.columns = ["Region", "Sales"]
    return out.round(2)

def sales_by_category(df, ct):
    cc, sc = _cat(df, ct), _s(df, ct)
    if not cc or not sc:
        return pd.DataFrame({"Category": ["N/A"], "Sales": [0], "Share %": [100]})
    out = df.groupby(cc)[sc].sum().reset_index().sort_values(sc, ascending=False)
    out.columns = ["Category", "Sales"]
    tot = out["Sales"].sum()
    out["Share %"] = (out["Sales"] / tot * 100).round(1) if tot else 0
    return out.round(2)

def top_products(df, ct, n=16):
    prod = next((c for c in df.columns if "product" in c.lower() and "name" in c.lower()), None)
    if not prod: prod = next((c for c in ct["categorical"] if "product" in c.lower()), None)
    sc, pc = _s(df, ct), _p(df, ct)
    if not prod or not sc:
        return pd.DataFrame({"Product": ["N/A"], "Sales": [0]})
    gcols = [sc] + ([pc] if pc else [])
    out = (df.groupby(prod)[gcols].sum().reset_index()
             .sort_values(sc, ascending=False).head(n))
    if pc:
        tot = out[sc].sum()
        out["Profit Rank %"] = (out[sc] / tot * 100).round(1)
    out.insert(0, "Rank", range(1, len(out) + 1))
    out.columns = (["Rank", "Product", "Sales"] +
                   (["Profit", "Profit Rank %"] if pc else []))
    return out.round(2)

def monthly_trend(df, ct):
    dcs = ct.get("datetime", [])
    sc = _s(df, ct)
    if not dcs or not sc:
        return pd.DataFrame({"Date": [], "Sales": [], "MoM Growth": []})
    dc = dcs[0]
    tmp = df.copy()
    tmp[dc] = pd.to_datetime(tmp[dc], errors="coerce")
    tmp["_p"] = tmp[dc].dt.to_period("M").dt.to_timestamp()
    m = tmp.groupby("_p")[sc].sum().reset_index()
    m.columns = ["Date", "Sales"]
    m["MoM Growth"] = m["Sales"].pct_change().fillna(0).round(4)
    return m.round(2)


# ════════════════════════════════════════════════════════════════════════════════
# MATPLOTLIB CHARTS  — each with its own accent colour
# ════════════════════════════════════════════════════════════════════════════════
def _fig_bytes(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    buf.seek(0)
    plt.close(fig)
    return buf

def _style_ax(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#E5E7EB")
    ax.tick_params(colors="#6B7280", labelsize=7)
    ax.set_facecolor("#FAFAFA")

def chart_region(df, ct):
    rbr = sales_by_region(df, ct)
    if rbr.empty or rbr["Sales"].sum() == 0: return None
    region_label = _group_label(_reg(df, ct), "Region")
    metric_label = _metric_label(df, ct)
    fig, ax = plt.subplots(figsize=(5.2, 2.8))
    n = len(rbr)
    # Gradient of teals
    palette = ["#00C9B1", "#00A896", "#007F6E", "#005F52", "#004845"][:n]
    bars = ax.barh(rbr["Region"].astype(str), rbr["Sales"],
                   color=palette[:n], edgecolor="white", linewidth=0.5, height=0.6)
    # Value labels
    for bar in bars:
        w = bar.get_width()
        ax.text(w * 1.01, bar.get_y() + bar.get_height()/2,
                _fmt(w), va="center", ha="left", fontsize=6.5, color="#374151")
    ax.set_title(f"{metric_label} by {region_label}", fontsize=10, fontweight="bold",
                 color="#00897B", pad=8, loc="left")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: _fmt(x)))
    _style_ax(ax)
    fig.patch.set_facecolor("white")
    plt.tight_layout(pad=0.5)
    return _fig_bytes(fig)

def chart_category(df, ct):
    sbc = sales_by_category(df, ct)
    if sbc.empty or sbc["Sales"].sum() == 0: return None
    category_label = _group_label(_cat(df, ct), "Category")
    metric_label = _metric_label(df, ct)
    fig, ax = plt.subplots(figsize=(5.2, 2.8))
    n = len(sbc)
    purples = plt.cm.Purples(np.linspace(0.38, 0.92, n))
    wedges, texts, autotexts = ax.pie(
        sbc["Sales"],
        labels=sbc["Category"].astype(str).str[:12],
        autopct="%1.1f%%", startangle=140,
        colors=purples,
        wedgeprops=dict(width=0.52, edgecolor="white", linewidth=1.5),
        pctdistance=0.78,
    )
    for t in texts: t.set_fontsize(7); t.set_color("#374151")
    for a in autotexts: a.set_fontsize(6.5); a.set_color("white"); a.set_fontweight("bold")
    ax.set_title(f"{metric_label} by {category_label}", fontsize=10, fontweight="bold",
                 color="#7C3AED", pad=8, loc="left")
    # Legend on right
    ax.legend(sbc["Category"].astype(str).str[:14].tolist(),
              loc="center right", bbox_to_anchor=(1.35, 0.5),
              fontsize=6.5, frameon=False)
    fig.patch.set_facecolor("white")
    plt.tight_layout(pad=0.5)
    return _fig_bytes(fig)

def chart_trend(df, ct):
    mt = monthly_trend(df, ct)
    if mt.empty: return None
    metric_label = _metric_label(df, ct)
    fig, ax = plt.subplots(figsize=(5.2, 2.8))
    x = range(len(mt))
    ax.fill_between(x, mt["Sales"], alpha=0.18, color="#22C55E")
    ax.plot(x, mt["Sales"], color="#22C55E", linewidth=2,
            marker="o", markersize=4, markerfacecolor="white",
            markeredgecolor="#22C55E", markeredgewidth=1.5)
    ax.set_title(f"Monthly {metric_label} Trend", fontsize=10, fontweight="bold",
                 color="#15803D", pad=8, loc="left")
    ax.set_ylabel(metric_label, fontsize=7, color="#6B7280")
    lbls = [str(d)[:7] for d in mt["Date"]]
    step = max(1, len(lbls) // 6)
    ax.set_xticks(range(0, len(lbls), step))
    ax.set_xticklabels([lbls[i] for i in range(0, len(lbls), step)], rotation=30, fontsize=6)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: _fmt(x)))
    _style_ax(ax)
    fig.patch.set_facecolor("white")
    plt.tight_layout(pad=0.5)
    return _fig_bytes(fig)

def chart_scatter(df, ct):
    sc, pc = _s(df, ct), _p(df, ct)
    if not sc or not pc: return None
    samp = df[[sc, pc]].dropna().sample(min(400, len(df)), random_state=42)
    fig, ax = plt.subplots(figsize=(5.2, 2.8))
    ax.scatter(samp[sc], samp[pc], alpha=0.55, color="#F97316",
               s=20, edgecolors="white", linewidths=0.4)
    # Trend line
    try:
        z = np.polyfit(samp[sc], samp[pc], 1)
        p = np.poly1d(z)
        xs = np.linspace(samp[sc].min(), samp[sc].max(), 100)
        ax.plot(xs, p(xs), color="#F97316", linewidth=1.5, alpha=0.6, linestyle="--")
    except: pass
    ax.set_title(f"{sc} vs {pc}", fontsize=10, fontweight="bold",
                 color="#C2410C", pad=8, loc="left")
    ax.set_xlabel(sc, fontsize=7, color="#6B7280")
    ax.set_ylabel(pc, fontsize=7, color="#6B7280")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: _fmt(x)))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: _fmt(x)))
    _style_ax(ax)
    fig.patch.set_facecolor("white")
    plt.tight_layout(pad=0.5)
    return _fig_bytes(fig)

def chart_orders(df, ct):
    dcs = ct.get("datetime", [])
    if not dcs: return None
    dc = dcs[0]
    tmp = df.copy()
    tmp[dc] = pd.to_datetime(tmp[dc], errors="coerce")
    tmp["_p"] = tmp[dc].dt.to_period("M").dt.to_timestamp()
    counts = tmp.groupby("_p").size().reset_index(name="Orders")
    if counts.empty: return None
    fig, ax = plt.subplots(figsize=(5.2, 2.8))
    blues = ["#93C5FD" if i % 2 == 0 else "#3B82F6" for i in range(len(counts))]
    ax.bar(range(len(counts)), counts["Orders"],
           color=blues, edgecolor="white", linewidth=0.5, width=0.7)
    ax.set_title("Monthly Record Count Trend", fontsize=10, fontweight="bold",
                 color="#1D4ED8", pad=8, loc="left")
    ax.set_ylabel("Records", fontsize=7, color="#6B7280")
    lbls = [str(d)[:7] for d in counts["_p"]]
    step = max(1, len(lbls) // 6)
    ax.set_xticks(range(0, len(lbls), step))
    ax.set_xticklabels([lbls[i] for i in range(0, len(lbls), step)], rotation=30, fontsize=6)
    _style_ax(ax)
    fig.patch.set_facecolor("white")
    plt.tight_layout(pad=0.5)
    return _fig_bytes(fig)

def chart_heatmap(df, ct):
    dcs = ct.get("datetime", [])
    sc = _s(df, ct)
    if not dcs or not sc: return None
    dc = dcs[0]
    tmp = df.copy()
    tmp[dc] = pd.to_datetime(tmp[dc], errors="coerce")
    tmp["month"] = tmp[dc].dt.month
    tmp["year"]  = tmp[dc].dt.year
    piv = tmp.pivot_table(index="year", columns="month", values=sc, aggfunc="sum")
    if piv.empty: return None
    fig, ax = plt.subplots(figsize=(5.2, 2.8))
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    im = ax.imshow(piv.values, cmap="Purples", aspect="auto", interpolation="nearest")
    ax.set_xticks(range(piv.shape[1]))
    ax.set_xticklabels([months[m-1] for m in piv.columns], fontsize=7)
    ax.set_yticks(range(piv.shape[0]))
    ax.set_yticklabels([str(y) for y in piv.index], fontsize=7)
    ax.set_title(f"{sc} Seasonality Heatmap", fontsize=10, fontweight="bold",
                 color="#7C3AED", pad=8, loc="left")
    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.04)
    cbar.ax.tick_params(labelsize=6)
    fig.patch.set_facecolor("white")
    plt.tight_layout(pad=0.5)
    return _fig_bytes(fig)


# ════════════════════════════════════════════════════════════════════════════════
# REPORTLAB  PDF
# ════════════════════════════════════════════════════════════════════════════════

# KPI box colour pairs (background light, value accent)
_KPI_COLOURS = [
    ("#E0F7FA", "#00897B"),   # 0 cyan-teal
    ("#F0FDF4", "#16A34A"),   # 1 green
    ("#EFF6FF", "#2563EB"),   # 2 blue
    ("#F5F3FF", "#7C3AED"),   # 3 violet
    ("#FFFBEB", "#D97706"),   # 4 amber
    ("#FFF1F2", "#DC2626"),   # 5 rose
]

def _hf(canvas, doc):
    """Header + footer drawn on every page."""
    canvas.saveState()
    w, h = A4
    # Purple header bar
    canvas.setFillColor(colors.HexColor("#7C3AED"))
    canvas.rect(0, h - 18*mm, w, 18*mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawCentredString(w/2, h - 11*mm,
        "Zero Click AI  —  Comprehensive Analysis Report")
    # Sub-bar
    canvas.setFillColor(colors.HexColor("#A78BFA"))
    canvas.rect(0, h - 24*mm, w, 6*mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(12*mm, h - 21*mm,
        f"  Report Date: {NOW.strftime('%Y-%m-%d')}  |  "
        f"Period: Data from Jan 2025 – Mar 2026")
    canvas.drawRightString(w - 12*mm, h - 21*mm,
        "Source: AI Sales Chatbot System  ")
    # Footer
    canvas.setFillColor(colors.HexColor("#9CA3AF"))
    canvas.setFont("Helvetica-Oblique", 7)
    canvas.drawCentredString(w/2, 8*mm,
        f"Page {doc.page}  |  Generated {NOW.strftime('%Y-%m-%d %H:%M')}  |  Genesis Training")
    canvas.restoreState()


def _style(name, **kw):
    return ParagraphStyle(name, **kw)

def _styles():
    return {
        "section": _style("sec", fontName="Helvetica-Bold", fontSize=11,
                          textColor=colors.HexColor("#7C3AED"),
                          spaceBefore=8, spaceAfter=3),
        "body":    _style("body", fontName="Helvetica", fontSize=8.5,
                          textColor=colors.HexColor("#1F2937"),
                          spaceAfter=3, leading=13),
        "bold":    _style("bold", fontName="Helvetica-Bold", fontSize=9,
                          textColor=colors.HexColor("#7C3AED"), spaceAfter=2),
        "note":    _style("note", fontName="Helvetica-Oblique", fontSize=7,
                          textColor=colors.HexColor("#9CA3AF")),
        "ai_head": _style("aih", fontName="Helvetica-Bold", fontSize=9,
                          textColor=colors.HexColor("#7C3AED"),
                          spaceBefore=5, spaceAfter=2),
    }


def _section_hdr(text, ST):
    return [
        Paragraph(text, ST["section"]),
        HRFlowable(width="100%", thickness=0.6,
                   color=colors.HexColor("#A78BFA"), spaceAfter=4),
    ]


def _build_kpi_row(kpi_triples, start_idx=0, pw=None):
    """
    Build ONE row of 3 KPI boxes.
    kpi_triples = [(label, value, delta), ...]  (3 items)
    """
    col_w = (pw - 6*mm) / 3
    cells = []
    for i, (lbl, val, dlt) in enumerate(kpi_triples):
        idx   = (start_idx + i) % len(_KPI_COLOURS)
        bg, accent = _KPI_COLOURS[idx]
        pos   = not str(dlt).lstrip().startswith("-")
        dlt_c = colors.HexColor("#16A34A") if pos else colors.HexColor("#DC2626")
        sym   = "▲" if pos else "▼"

        inner = Table(
            [[Paragraph(str(val)[:16],
                        _style(f"kv{i}", fontName="Helvetica-Bold", fontSize=14,
                               textColor=colors.HexColor(accent), alignment=TA_CENTER))],
             [Paragraph(f"{sym} {dlt}",
                        _style(f"kd{i}", fontName="Helvetica", fontSize=8,
                               textColor=dlt_c, alignment=TA_CENTER))],
             [Paragraph(str(lbl)[:22],
                        _style(f"kl{i}", fontName="Helvetica", fontSize=7,
                               textColor=colors.HexColor("#6B7280"), alignment=TA_CENTER))]],
            colWidths=[col_w],
            style=TableStyle([
                ("BACKGROUND",    (0,0), (-1,-1), colors.HexColor(bg)),
                ("BOX",           (0,0), (-1,-1), 0.8, colors.HexColor(accent)),
                ("TOPPADDING",    (0,0), (-1,-1), 6),
                ("BOTTOMPADDING", (0,0), (-1,-1), 6),
                ("ALIGN",         (0,0), (-1,-1), "CENTER"),
                ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
            ])
        )
        cells.append(inner)

    row_tbl = Table([cells],
                    colWidths=[col_w + 2*mm]*3,
                    style=TableStyle([
                        ("ALIGN",        (0,0), (-1,-1), "CENTER"),
                        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
                        ("LEFTPADDING",  (0,0), (-1,-1), 2),
                        ("RIGHTPADDING", (0,0), (-1,-1), 2),
                    ]))
    return row_tbl


def _mini_tbl(headers, rows, col_w_mm, row_h=5.5):
    """Styled data table — purple header, alternating rows."""
    cw   = [w * mm for w in col_w_mm]
    data = [headers] + rows
    tbl  = Table(data, colWidths=cw, repeatRows=1)
    style = [
        # Header
        ("BACKGROUND",    (0,0), (-1, 0), colors.HexColor("#7C3AED")),
        ("TEXTCOLOR",     (0,0), (-1, 0), colors.white),
        ("FONTNAME",      (0,0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1, 0), 8),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("GRID",          (0,0), (-1,-1), 0.25, colors.HexColor("#D1D5DB")),
        ("FONTSIZE",      (0,1), (-1,-1), 7.5),
        ("TOPPADDING",    (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]
    # Alternating row backgrounds
    for r in range(1, len(data)):
        bg = "#F3F0FF" if r % 2 == 1 else "#FFFFFF"
        style.append(("BACKGROUND", (0,r), (-1,r), colors.HexColor(bg)))
    tbl.setStyle(TableStyle(style))
    return tbl


def _chart_img(buf, w_mm, h_mm):
    if buf is None: return None
    return RLImage(buf, width=w_mm*mm, height=h_mm*mm)


def generate_report_pdf(df, kpis, ml_results, forecast_data, insights, charts) -> bytes:
    if not HAS_RL:
        return b""

    ct     = _col_types(df)
    ST     = _styles()
    pw     = A4[0] - 24*mm   # usable page width
    buf    = io.BytesIO()

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=28*mm, bottomMargin=18*mm,
        leftMargin=12*mm, rightMargin=12*mm,
    )
    story = []

    # ── Page 1: Performance Dashboard ─────────────────────────────────────────
    # Title bar
    dash_t = Table(
        [[Paragraph("PERFORMANCE DASHBOARD",
                    _style("dt", fontName="Helvetica-Bold", fontSize=13,
                           textColor=colors.HexColor("#7C3AED"), alignment=TA_CENTER))]],
        colWidths=[pw],
        style=TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), colors.HexColor("#EDE9FE")),
            ("BOX",           (0,0),(-1,-1), 0.8, colors.HexColor("#A78BFA")),
            ("TOPPADDING",    (0,0),(-1,-1), 7),
            ("BOTTOMPADDING", (0,0),(-1,-1), 7),
        ])
    )
    story.append(dash_t)
    story.append(Spacer(1, 4*mm))

    # KPI boxes
    kpi_list = list(kpis or [])
    while len(kpi_list) < 6:
        kpi_list.append(("N/A", "—", "—"))

    def _ktriple(k):
        if len(k) >= 3: return (str(k[0]), str(k[1]), str(k[2]))
        if len(k) == 2: return (str(k[0]), str(k[1]), "—")
        return (str(k[0]), "—", "—")

    story.append(_build_kpi_row([_ktriple(kpi_list[i]) for i in range(3)], 0, pw))
    story.append(Spacer(1, 4*mm))
    story.append(_build_kpi_row([_ktriple(kpi_list[i]) for i in range(3, 6)], 3, pw))
    story.append(Spacer(1, 5*mm))

    # AI Summary section
    ai_head_tbl = Table(
        [[Paragraph("  AI NARRATED SUMMARY",
                    _style("aih2", fontName="Helvetica-Bold", fontSize=9,
                           textColor=colors.HexColor("#7C3AED")))]],
        colWidths=[pw],
        style=TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), colors.HexColor("#EDE9FE")),
            ("BOX",           (0,0),(-1,-1), 0.5, colors.HexColor("#A78BFA")),
            ("TOPPADDING",    (0,0),(-1,-1), 3),
            ("BOTTOMPADDING", (0,0),(-1,-1), 3),
        ])
    )
    story.append(ai_head_tbl)

    # AI text body
    ai_short = ""
    if isinstance(insights, str):
        lines = [l.strip() for l in insights.split("\n")
                 if l.strip() and not l.strip().startswith("#")]
        ai_short = " ".join(lines[:4])[:520]
    elif isinstance(insights, list):
        ai_short = " ".join(str(i) for i in insights[:4])[:520]

    ai_body = Table(
        [[Paragraph(ai_short or "AI analysis complete.", ST["body"])]],
        colWidths=[pw],
        style=TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), colors.white),
            ("BOX",           (0,0),(-1,-1), 0.5, colors.HexColor("#A78BFA")),
            ("TOPPADDING",    (0,0),(-1,-1), 7),
            ("BOTTOMPADDING", (0,0),(-1,-1), 7),
            ("LEFTPADDING",   (0,0),(-1,-1), 10),
            ("RIGHTPADDING",  (0,0),(-1,-1), 10),
        ])
    )
    story.append(ai_body)
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("*Profit margin = Profit/Sales", ST["note"]))

    # ── Page 2: Charts ────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.extend(_section_hdr("Dataset Charts", ST))

    chart_fns = [
        (f"{_metric_label(df, ct)} by {_group_label(_reg(df, ct), 'Region')}",      lambda: chart_region(df, ct)),
        (f"{_metric_label(df, ct)} by {_group_label(_cat(df, ct), 'Category')}",    lambda: chart_category(df, ct)),
        (f"Monthly {_metric_label(df, ct)} Trend",  lambda: chart_trend(df, ct)),
        (f"{_s(df, ct) or 'Metric'} vs {_p(df, ct) or 'Secondary Metric'}",      lambda: chart_scatter(df, ct)),
        ("Monthly Record Count Trend", lambda: chart_orders(df, ct)),
        (f"{_metric_label(df, ct)} Seasonality Heatmap",  lambda: chart_heatmap(df, ct)),
    ]
    chart_imgs = []
    for title, fn in chart_fns:
        try:
            b = fn()
            if b: chart_imgs.append((title, b))
        except Exception as e:
            print(f"  Chart '{title}' skipped: {e}")

    CW = (pw - 4*mm) / 2
    CH = 56  # mm height for each chart
    for i in range(0, len(chart_imgs), 2):
        lt, lb = chart_imgs[i]
        rt, rb = chart_imgs[i+1] if i+1 < len(chart_imgs) else (None, None)
        li = _chart_img(lb, CW/mm, CH) or Spacer(1, 1)
        ri = _chart_img(rb, CW/mm, CH) if rb else Spacer(1, 1)
        lbl = lambda t: Paragraph(t or "",
            _style("ct", fontName="Helvetica-Bold", fontSize=8,
                   textColor=colors.HexColor("#374151"), alignment=TA_CENTER))
        row_tbl = Table([[lbl(lt), lbl(rt)], [li, ri]],
                        colWidths=[CW, CW],
                        style=TableStyle([
                            ("ALIGN",         (0,0),(-1,-1),"CENTER"),
                            ("VALIGN",        (0,0),(-1,-1),"MIDDLE"),
                            ("LEFTPADDING",   (0,0),(-1,-1), 2),
                            ("RIGHTPADDING",  (0,0),(-1,-1), 2),
                            ("BOTTOMPADDING", (0,0),(-1,-1), 3),
                        ]))
        story.append(row_tbl)
        story.append(Spacer(1, 3*mm))

    # ── Page 3: Top Products ──────────────────────────────────────────────────
    story.append(PageBreak())
    story.extend(_section_hdr("Top Records by Key Metric", ST))
    tp = top_products(df, ct, n=16)
    if not tp.empty:
        hdrs = list(tp.columns)
        nc   = len(hdrs)
        cw   = [10] + [int((pw/mm - 12)/(nc-1))]*(nc-1)
        rows = [[str(tp.iloc[i][c])[:22] for c in tp.columns]
                for i in range(len(tp))]
        story.append(_mini_tbl(hdrs, rows, cw))

    # ── Page 4: ML Insights ───────────────────────────────────────────────────
    story.append(PageBreak())
    story.extend(_section_hdr("Machine Learning Insights", ST))
    if ml_results:
        for res in ml_results:
            story.append(Paragraph(f"■  {res.get('title','Model')}", ST["bold"]))
            story.append(Paragraph(
                f"    {res.get('metric_name')}: {res.get('metric_value')}",
                _style("mv", fontName="Helvetica", fontSize=8,
                       textColor=colors.HexColor("#16A34A"), spaceAfter=2)))
            story.append(Paragraph(
                f"    Type: {res.get('type')} | {res.get('extra','')}",
                ST["body"]))
            story.append(Spacer(1, 3*mm))
    else:
        story.append(Paragraph("ML models not trained — need numeric columns.", ST["body"]))

    # ── Page 5: Forecast ──────────────────────────────────────────────────────
    if forecast_data:
        story.append(PageBreak())
        story.extend(_section_hdr("Time-Series Forecast", ST))
        story.append(Paragraph(
            f"Model: {forecast_data.get('model','N/A')}  |  6-month horizon",
            ST["body"]))
        story.append(Spacer(1, 3*mm))
        fdf = forecast_data.get("forecast_df")
        if fdf is not None and not fdf.empty:
            hdrs = ["Period", "Predicted", "Lower 95%", "Upper 95%"]
            cw   = [50, 44, 44, 44]
            rows = []
            for _, row in fdf.head(12).iterrows():
                dt = str(row.get("ds","")).split(" ")[0]
                rows.append([dt,
                    f"${_num(row.get('yhat',0)):,.0f}",
                    f"${_num(row.get('yhat_lower',0)):,.0f}",
                    f"${_num(row.get('yhat_upper',0)):,.0f}"])
            story.append(_mini_tbl(hdrs, rows, cw))

    # ── Page 6: Full AI Insights ──────────────────────────────────────────────
    story.append(PageBreak())
    story.extend(_section_hdr("Full AI Insights", ST))
    full = (insights if isinstance(insights, str)
            else "\n".join(f"• {i}" for i in (insights or [])))
    for line in full.split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 2*mm))
        elif line.startswith("## "):
            story.append(Paragraph(line[3:], ST["ai_head"]))
        elif line.startswith(("- ", "• ", "* ")):
            story.append(Paragraph(f"  • {line[2:]}", ST["body"]))
        else:
            story.append(Paragraph(line, ST["body"]))

    # ── Page 7: Dataset Sample ────────────────────────────────────────────────
    story.append(PageBreak())
    story.extend(_section_hdr("Dataset Sample — First 20 Rows", ST))
    sample = df.head(20).astype(str)
    cols   = list(sample.columns[:7])
    nc     = len(cols)
    cw     = [int(pw/mm / nc)] * nc
    rows   = [[str(sample.iloc[i][c])[:18] for c in cols]
              for i in range(len(sample))]
    story.append(_mini_tbl([c[:16] for c in cols], rows, cw))

    doc.build(story, onFirstPage=_hf, onLaterPages=_hf)
    return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════════════
# EXCEL REPORT  — multi-coloured, polished worksheets
# ════════════════════════════════════════════════════════════════════════════════

# Tab/sheet accent colours
_SHEET_ACCENTS = {
    "README":             "7C3AED",
    "KPIs":               "0891B2",
    "Sales_by_Region":    "059669",
    "Sales_by_Category":  "7C3AED",
    "Top10_Products_Profit": "C2410C",
    "Monthly_Trend":      "1D4ED8",
    "Raw_Data":           "374151",
}

def _xl_hdr(ws, row, headers, accent="7C3AED"):
    fill = PatternFill("solid", fgColor=accent)
    fnt  = Font(bold=True, color="FFFFFF", size=10)
    bdr  = Border(left=Side(style="thin"), right=Side(style="thin"),
                  top=Side(style="thin"),  bottom=Side(style="thin"))
    for ci, h in enumerate(headers, 1):
        c = ws.cell(row=row, column=ci, value=h)
        c.fill = fill; c.font = fnt; c.border = bdr
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(ci)].width = max(14, len(str(h))+4)

def _xl_row(ws, ri, vals, alt=False, accent="7C3AED"):
    hex_bg = "F3F0FF" if alt else "FFFFFF"
    fill = PatternFill("solid", fgColor=hex_bg)
    bdr  = Border(left=Side(style="thin"), right=Side(style="thin"),
                  top=Side(style="thin"),  bottom=Side(style="thin"))
    for ci, val in enumerate(vals, 1):
        c = ws.cell(row=ri, column=ci, value=val)
        c.fill = fill; c.border = bdr
        c.font = Font(size=9)
        c.alignment = Alignment(horizontal="center", vertical="center")

def _xl_title(ws, text, row=1, end_col=8, accent="7C3AED"):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=end_col)
    c = ws.cell(row=row, column=1, value=text)
    c.fill = PatternFill("solid", fgColor=accent)
    c.font = Font(bold=True, color="FFFFFF", size=12)
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[row].height = 24

def _write_df_xl(ws, df_in, start=2, accent="7C3AED"):
    hdrs = list(df_in.columns)
    _xl_hdr(ws, start, hdrs, accent)
    for ri, (_, row) in enumerate(df_in.iterrows(), 1):
        vals = list(row)
        _xl_row(ws, start+ri, vals, alt=ri%2==0, accent=accent)
        for ci, val in enumerate(vals, 1):
            cell = ws.cell(row=start+ri, column=ci)
            cn   = hdrs[ci-1].lower()
            if "mom" in cn or "growth" in cn:
                try:
                    v = float(val)
                    cell.font  = Font(size=9, bold=True,
                                      color="166534" if v>=0 else "991B1B")
                    cell.value = f"+{v*100:.2f}%" if v>=0 else f"{v*100:.2f}%"
                except: pass
            elif any(w in cn for w in ["sales","revenue","profit","amount","price","total"]):
                try: cell.number_format = "#,##0.00"; cell.value = float(val)
                except: pass


def generate_report_excel(df, kpis, ml_results, forecast_data, insights) -> bytes:
    if not HAS_OXL:
        return b""
    ct = _col_types(df)
    wb = openpyxl.Workbook()

    # ── README ────────────────────────────────────────────────────────────────
    ws = wb.active; ws.title = "README"
    acc = _SHEET_ACCENTS["README"]
    _xl_title(ws, "Zero Click AI — Comprehensive Analysis Report", row=1, end_col=6, accent=acc)
    info = [
        ("Report Date",  NOW.strftime("%Y-%m-%d %H:%M")),
        ("Platform",     "Zero Click AI · Genesis Training"),
        ("Rows",         f"{len(df):,}"),
        ("Columns",      f"{len(df.columns)}"),
        ("AI Summary",   (insights[:250] if isinstance(insights,str)
                          else str(insights)[:250])),
    ]
    for ri, (k, v) in enumerate(info, 3):
        ws.cell(row=ri, column=1, value=k).font = Font(bold=True, color=acc, size=10)
        ws.cell(row=ri, column=2, value=v).font  = Font(size=10)
        ws.row_dimensions[ri].height = 16
    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 65

    # ── KPIs ──────────────────────────────────────────────────────────────────
    ws2 = wb.create_sheet("KPIs")
    acc2 = _SHEET_ACCENTS["KPIs"]
    _xl_title(ws2, "Key Performance Indicators", end_col=4, accent=acc2)
    kpi_rows = [[str(k[0]), str(k[1]), str(k[2]) if len(k)>2 else ""]
                for k in (kpis or [])]
    _xl_hdr(ws2, 2, ["Metric", "Value", "Description"], acc2)
    for i, r in enumerate(kpi_rows):
        _xl_row(ws2, i+3, r, alt=i%2==0, accent=acc2)
    ws2.column_dimensions["A"].width = 32
    ws2.column_dimensions["B"].width = 22
    ws2.column_dimensions["C"].width = 42
    if len(kpi_rows) >= 2:
        ch = BarChart(); ch.title = "KPI Values"; ch.style = 10
        ch.width = 16; ch.height = 9
        data = Reference(ws2, min_col=2, min_row=2, max_row=2+len(kpi_rows))
        cats = Reference(ws2, min_col=1, min_row=3, max_row=2+len(kpi_rows))
        ch.add_data(data, titles_from_data=True); ch.set_categories(cats)
        ws2.add_chart(ch, "E2")

    # ── Sales by Region ───────────────────────────────────────────────────────
    ws3 = wb.create_sheet("Sales_by_Region")
    acc3 = _SHEET_ACCENTS["Sales_by_Region"]
    _xl_title(ws3, f"{_metric_label(df, ct)} by {_group_label(_reg(df, ct), 'Region')}", end_col=4, accent=acc3)
    rbr = sales_by_region(df, ct)
    _write_df_xl(ws3, rbr, start=2, accent=acc3)
    if len(rbr) >= 2:
        ch = BarChart(); ch.title = f"{_metric_label(df, ct)} by {_group_label(_reg(df, ct), 'Region')}"; ch.style = 10
        ch.width = 16; ch.height = 9
        data = Reference(ws3, min_col=2, min_row=2, max_row=2+len(rbr))
        cats = Reference(ws3, min_col=1, min_row=3, max_row=2+len(rbr))
        ch.add_data(data, titles_from_data=True); ch.set_categories(cats)
        ws3.add_chart(ch, "D2")

    # ── Sales by Category ─────────────────────────────────────────────────────
    ws4 = wb.create_sheet("Sales_by_Category")
    acc4 = _SHEET_ACCENTS["Sales_by_Category"]
    _xl_title(ws4, f"{_metric_label(df, ct)} by {_group_label(_cat(df, ct), 'Category')}", end_col=5, accent=acc4)
    sbc = sales_by_category(df, ct)
    _write_df_xl(ws4, sbc, start=2, accent=acc4)
    if len(sbc) >= 2:
        ch = PieChart(); ch.title = "Category Distribution"; ch.style = 10
        ch.width = 14; ch.height = 9
        data = Reference(ws4, min_col=2, min_row=2, max_row=2+len(sbc))
        cats = Reference(ws4, min_col=1, min_row=3, max_row=2+len(sbc))
        ch.add_data(data, titles_from_data=True); ch.set_categories(cats)
        ws4.add_chart(ch, "E2")

    # ── Top 10 Products ───────────────────────────────────────────────────────
    ws5 = wb.create_sheet("Top10_Products_Profit")
    acc5 = _SHEET_ACCENTS["Top10_Products_Profit"]
    _xl_title(ws5, "Top 10 Records by Key Metric", end_col=6, accent=acc5)
    tp = top_products(df, ct, n=10)
    _write_df_xl(ws5, tp, start=2, accent=acc5)
    # Colour profit column
    if "Profit" in tp.columns:
        pci = list(tp.columns).index("Profit") + 1
        for ri in range(3, 3+len(tp)):
            cell = ws5.cell(row=ri, column=pci)
            try:
                v = float(cell.value)
                cell.fill = PatternFill("solid", fgColor="DCFCE7" if v>0 else "FEE2E2")
                cell.font = Font(color="166534" if v>0 else "991B1B", size=9, bold=True)
            except: pass

    # ── Monthly Trend ─────────────────────────────────────────────────────────
    ws6 = wb.create_sheet("Monthly_Trend")
    acc6 = _SHEET_ACCENTS["Monthly_Trend"]
    _xl_title(ws6, f"Monthly {_metric_label(df, ct)} Trend", end_col=5, accent=acc6)
    mt = monthly_trend(df, ct)
    if mt.empty:
        ws6.cell(row=3, column=1, value="No datetime column found.")
    else:
        _write_df_xl(ws6, mt, start=2, accent=acc6)
        ch = LineChart(); ch.title = f"Monthly {_metric_label(df, ct)} Trend"; ch.style = 10
        ch.width = 16; ch.height = 9
        data = Reference(ws6, min_col=2, min_row=2, max_row=2+len(mt))
        ch.add_data(data, titles_from_data=True)
        ws6.add_chart(ch, "E2")

    # ── Raw Data ──────────────────────────────────────────────────────────────
    ws7 = wb.create_sheet("Raw_Data")
    acc7 = _SHEET_ACCENTS["Raw_Data"]
    end  = min(len(df.columns), 12)
    _xl_title(ws7, "Raw Cleaned Dataset", end_col=end, accent=acc7)
    _write_df_xl(ws7, df.head(500), start=2, accent=acc7)

    for sheet in [ws2, ws3, ws4, ws5, ws6, ws7]:
        sheet.freeze_panes = "A3"

    out = io.BytesIO()
    wb.save(out)
    out.seek(0)
    return out.read()
