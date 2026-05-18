"""
report_generator.py — Professional PDF + Excel Reports
=======================================================
PDF Layout (4–5 pages):
  Page 1 : Executive Dashboard  — KPI cards + AI summary
  Page 2 : Visual Analytics     — 6 polished charts in 2-col grid
  Page 3 : Top Items table      + AI insights (two-column layout)
  Page 4 : Dataset Sample       — styled first-20-rows preview
  Page 5 : Forecast             — only rendered when forecast data exists
  ML page : only rendered when ml_results is populated

Design improvements:
  - Consistent deep-violet + teal brand palette
  - Category chart fixed: horizontal bar (no broken donut)
  - Rolling-average overlay on order volume chart
  - Peak-cell highlight on heatmap
  - Two-column layout on page 3 (table + insights side-by-side)
  - Auto-filter + freeze panes on Excel sheets
  - Column detection works on any dataset (Reliance, Zomato, etc.)
"""

import io, datetime, warnings
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")

# ── matplotlib ────────────────────────────────────────────────────────────────
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

# ── ReportLab ─────────────────────────────────────────────────────────────────
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
        Image as RLImage, HRFlowable, PageBreak,
    )
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    HAS_RL = True
except ImportError:
    HAS_RL = False

# ── OpenPyXL ──────────────────────────────────────────────────────────────────
try:
    import openpyxl
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.chart import BarChart, LineChart, PieChart, Reference
    HAS_OXL = True
except ImportError:
    HAS_OXL = False

NOW = datetime.datetime.now()

# ════════════════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM
# ════════════════════════════════════════════════════════════════════════════════
BRAND = {
    "deep":    "#4C1D95",
    "mid":     "#7C3AED",
    "soft":    "#A78BFA",
    "pale":    "#EDE9FE",
    "teal":    "#0D9488",
    "teal_lt": "#CCFBF1",
    "ink":     "#1E1B4B",
    "muted":   "#6B7280",
    "rule":    "#DDD6FE",
    "white":   "#FFFFFF",
    "offwhite":"#FAFAF9",
    "green":   "#16A34A",
    "red":     "#DC2626",
    "row_a":   "#F5F3FF",
    "row_b":   "#FFFFFF",
}

CHART_PALETTE = {
    "region":   "#0D9488",
    "category": "#7C3AED",
    "trend":    "#059669",
    "scatter":  "#EA580C",
    "orders":   "#2563EB",
    "heatmap":  "#7C3AED",
}

KPI_CARDS = [
    ("#ECFDF5", "#059669"),
    ("#EFF6FF", "#2563EB"),
    ("#F5F3FF", "#7C3AED"),
    ("#FFF7ED", "#EA580C"),
    ("#F0FDF4", "#16A34A"),
    ("#FEF2F2", "#DC2626"),
]

XL_ACCENTS = {
    "README":             "4C1D95",
    "KPIs":               "0D9488",
    "Sales_by_Region":    "0369A1",
    "Sales_by_Category":  "7C3AED",
    "Top_Products":       "B45309",
    "Monthly_Trend":      "047857",
    "Raw_Data":           "374151",
}

# ════════════════════════════════════════════════════════════════════════════════
# DATA HELPERS
# ════════════════════════════════════════════════════════════════════════════════
def _col_types(df):
    return {
        "numeric":     df.select_dtypes(include="number").columns.tolist(),
        "categorical": df.select_dtypes(include=["object","category"]).columns.tolist(),
        "datetime":    df.select_dtypes(include=["datetime64","datetimetz"]).columns.tolist(),
    }

def _sales_col(df, ct):
    for kw in ["total revenue","revenue","sales","amount","total"]:
        c = next((c for c in ct["numeric"] if kw in c.lower()), None)
        if c: return c
    return ct["numeric"][0] if ct["numeric"] else None

def _profit_col(df, ct):
    return next((c for c in ct["numeric"]
                 if "profit" in c.lower() and "margin" not in c.lower()), None)

def _cat_col(df, ct):
    for kw in ["categ","type","segment","cuisine","food_type"]:
        c = next((c for c in ct["categorical"] if kw in c.lower()), None)
        if c: return c
    for c in ct["categorical"]:
        if df[c].nunique() <= 30 and not any(x in c.lower() for x in ["id","name","order","customer"]):
            return c
    return None

def _item_col(df, ct):
    for exact in ["product name","food item","item name","sku name"]:
        c = next((c for c in df.columns if c.lower() == exact), None)
        if c: return c
    for kw in ["product","food","item","sku"]:
        c = next((c for c in ct["categorical"] if kw in c.lower()), None)
        if c: return c
    return None

def _reg_col(df, ct):
    return next((c for c in df.columns if "region" in c.lower()), None)

def _date_col(df, ct):
    dcs = ct.get("datetime", [])
    if dcs: return dcs[0]
    for c in df.columns:
        if "date" in c.lower(): return c
    return None

def _fmt(v):
    try:
        v = float(v)
        if abs(v) >= 1e9: return f"${v/1e9:.2f}B"
        if abs(v) >= 1e6: return f"${v/1e6:.2f}M"
        if abs(v) >= 1e3: return f"${v/1e3:.1f}K"
        return f"${v:,.0f}"
    except: return str(v)

def _num(x):
    try: return float(x)
    except: return 0.0

def _sales_by_region(df, ct):
    rc, sc = _reg_col(df, ct), _sales_col(df, ct)
    if not rc or not sc: return pd.DataFrame({"Region": ["N/A"], "Sales": [0]})
    out = df.groupby(rc)[sc].sum().reset_index().sort_values(sc, ascending=True)
    out.columns = ["Region", "Sales"]
    return out.round(2)

def _sales_by_category(df, ct):
    cc, sc = _cat_col(df, ct), _sales_col(df, ct)
    if not cc or not sc: return pd.DataFrame({"Category": ["N/A"], "Sales": [0], "Pct": [100]})
    out = df.groupby(cc)[sc].sum().reset_index().sort_values(sc, ascending=True)
    out.columns = ["Category", "Sales"]
    tot = out["Sales"].sum()
    out["Pct"] = (out["Sales"] / tot * 100).round(1) if tot else 0
    return out.round(2)

def _top_items(df, ct, n=16):
    item = _item_col(df, ct) or _cat_col(df, ct)
    sc, pc = _sales_col(df, ct), _profit_col(df, ct)
    if not item or not sc: return pd.DataFrame({"Item": ["N/A"], "Sales": [0]})
    gcols = [sc] + ([pc] if pc else [])
    out = (df.groupby(item)[gcols].sum().reset_index()
             .sort_values(sc, ascending=False).head(n))
    if pc:
        tot = out[sc].sum()
        out["Profit Rank %"] = (out[sc] / tot * 100).round(1)
    out.insert(0, "Rank", range(1, len(out)+1))
    cols = ["Rank", item, "Sales"] + ([pc, "Profit Rank %"] if pc else [])
    out = out[cols]
    out.columns = ["Rank", "Item", "Sales"] + (["Profit", "Profit Rank %"] if pc else [])
    return out.round(2)

def _monthly_trend(df, ct):
    dc, sc = _date_col(df, ct), _sales_col(df, ct)
    if not dc or not sc: return pd.DataFrame({"Date": [], "Sales": [], "MoM": []})
    tmp = df.copy()
    tmp[dc] = pd.to_datetime(tmp[dc], errors="coerce")
    tmp["_p"] = tmp[dc].dt.to_period("M").dt.to_timestamp()
    m = tmp.groupby("_p")[sc].sum().reset_index()
    m.columns = ["Date", "Sales"]
    m["MoM"] = m["Sales"].pct_change().fillna(0).round(4)
    return m.round(2)

# ════════════════════════════════════════════════════════════════════════════════
# CHART FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════════
def _save(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=160, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    buf.seek(0)
    plt.close(fig)
    return buf

def _base_ax(ax, grid_axis="x"):
    ax.spines[["top","right"]].set_visible(False)
    ax.spines[["left","bottom"]].set_color("#E5E7EB")
    ax.tick_params(colors="#6B7280", labelsize=7.5)
    ax.set_facecolor("#FAFAFA")
    if grid_axis == "x":
        ax.xaxis.grid(True, color="#F3F4F6", linewidth=0.6, zorder=0)
        ax.yaxis.grid(False)
    else:
        ax.yaxis.grid(True, color="#F3F4F6", linewidth=0.6, zorder=0)
        ax.xaxis.grid(False)
    ax.set_axisbelow(True)

def _chart_title(ax, text, color):
    ax.set_title(text, fontsize=9.5, fontweight="bold", color=color, pad=9, loc="left")

def chart_region(df, ct):
    data = _sales_by_region(df, ct)
    if data.empty or data["Sales"].sum() == 0: return None
    fig, ax = plt.subplots(figsize=(5.4, 2.9))
    fig.patch.set_facecolor("white")
    color = CHART_PALETTE["region"]
    n = len(data)
    alphas = np.linspace(0.5, 1.0, n)
    bars = ax.barh(data["Region"].astype(str), data["Sales"],
                   color=color, edgecolor="white", linewidth=0.8,
                   height=0.55, zorder=3)
    for bar, a in zip(bars, alphas):
        bar.set_alpha(a)
    for bar in bars:
        w = bar.get_width()
        ax.text(w * 0.97, bar.get_y() + bar.get_height()/2,
                _fmt(w), va="center", ha="right", fontsize=7,
                color="white", fontweight="bold")
    _chart_title(ax, f"{_sales_col(df,ct) or 'Sales'} by Region", color)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: _fmt(x)))
    _base_ax(ax, "x")
    plt.tight_layout(pad=0.6)
    return _save(fig)

def chart_category(df, ct):
    """Horizontal bar chart — readable for any number of categories."""
    data = _sales_by_category(df, ct)
    if data.empty or data["Sales"].sum() == 0: return None
    fig, ax = plt.subplots(figsize=(5.4, 2.9))
    fig.patch.set_facecolor("white")
    n = len(data)
    # Purple gradient from light to deep
    purples = plt.cm.get_cmap("RdPu", n + 3)
    clrs = [purples(i + 2) for i in range(n)]
    bars = ax.barh(data["Category"].astype(str), data["Sales"],
                   color=clrs, edgecolor="white", linewidth=0.8,
                   height=0.55, zorder=3)
    max_val = data["Sales"].max()
    for bar, pct in zip(bars, data["Pct"]):
        w = bar.get_width()
        # Pct label to the right of bar
        ax.text(max_val * 1.02, bar.get_y() + bar.get_height()/2,
                f"{pct:.1f}%", va="center", ha="left", fontsize=7, color="#6B7280")
    ax.set_xlim(0, max_val * 1.20)
    _chart_title(ax, f"Sales by {_cat_col(df,ct) or 'Category'}", CHART_PALETTE["category"])
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: _fmt(x)))
    _base_ax(ax, "x")
    plt.tight_layout(pad=0.6)
    return _save(fig)

def chart_trend(df, ct):
    mt = _monthly_trend(df, ct)
    if mt.empty: return None
    sc = _sales_col(df, ct) or "Sales"
    color = CHART_PALETTE["trend"]
    fig, ax = plt.subplots(figsize=(5.4, 2.9))
    fig.patch.set_facecolor("white")
    x = range(len(mt))
    ax.fill_between(x, mt["Sales"], alpha=0.15, color=color, zorder=2)
    ax.plot(x, mt["Sales"], color=color, linewidth=2.0, zorder=3,
            marker="o", markersize=3.5, markerfacecolor="white",
            markeredgecolor=color, markeredgewidth=1.5)
    # Star on peak
    peak_idx = mt["Sales"].idxmax()
    ax.plot(peak_idx, mt.loc[peak_idx, "Sales"],
            marker="*", markersize=11, color="#FBBF24", zorder=4)
    _chart_title(ax, f"Monthly {sc} Trend", color)
    lbls = [str(d)[:7] for d in mt["Date"]]
    step = max(1, len(lbls) // 7)
    ax.set_xticks(range(0, len(lbls), step))
    ax.set_xticklabels([lbls[i] for i in range(0, len(lbls), step)], rotation=30, fontsize=6.5)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: _fmt(x)))
    _base_ax(ax, "y")
    plt.tight_layout(pad=0.6)
    return _save(fig)

def chart_scatter(df, ct):
    sc, pc = _sales_col(df, ct), _profit_col(df, ct)
    if not sc or not pc: return None
    samp = df[[sc, pc]].dropna().sample(min(500, len(df)), random_state=42)
    color = CHART_PALETTE["scatter"]
    fig, ax = plt.subplots(figsize=(5.4, 2.9))
    fig.patch.set_facecolor("white")
    ax.scatter(samp[sc], samp[pc], alpha=0.45, color=color, s=16,
               edgecolors="white", linewidths=0.3, zorder=3)
    try:
        z = np.polyfit(samp[sc], samp[pc], 1)
        xs = np.linspace(samp[sc].min(), samp[sc].max(), 200)
        ax.plot(xs, np.poly1d(z)(xs), color=color, lw=1.8, alpha=0.7,
                linestyle="--", zorder=4)
    except: pass
    _chart_title(ax, f"{sc} vs {pc}", color)
    ax.set_xlabel(sc, fontsize=7, color="#6B7280")
    ax.set_ylabel(pc, fontsize=7, color="#6B7280")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: _fmt(x)))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: _fmt(x)))
    _base_ax(ax, "y")
    plt.tight_layout(pad=0.6)
    return _save(fig)

def chart_orders(df, ct):
    dc = _date_col(df, ct)
    if not dc: return None
    color = CHART_PALETTE["orders"]
    tmp = df.copy()
    tmp[dc] = pd.to_datetime(tmp[dc], errors="coerce")
    tmp["_p"] = tmp[dc].dt.to_period("M").dt.to_timestamp()
    counts = tmp.groupby("_p").size().reset_index(name="Orders")
    if counts.empty: return None
    fig, ax = plt.subplots(figsize=(5.4, 2.9))
    fig.patch.set_facecolor("white")
    x = range(len(counts))
    ax.bar(x, counts["Orders"], color=color, alpha=0.82,
           edgecolor="white", linewidth=0.5, width=0.72, zorder=3)
    if len(counts) >= 3:
        roll = counts["Orders"].rolling(3, center=True).mean()
        ax.plot(x, roll, color="#FBBF24", linewidth=2, zorder=4,
                linestyle="-", label="3-mo avg")
        ax.legend(fontsize=6.5, frameon=False, loc="upper left")
    _chart_title(ax, "Monthly Order Volume", color)
    lbls = [str(d)[:7] for d in counts["_p"]]
    step = max(1, len(lbls) // 7)
    ax.set_xticks(range(0, len(lbls), step))
    ax.set_xticklabels([lbls[i] for i in range(0, len(lbls), step)], rotation=30, fontsize=6.5)
    _base_ax(ax, "y")
    plt.tight_layout(pad=0.6)
    return _save(fig)

def chart_heatmap(df, ct):
    dc, sc = _date_col(df, ct), _sales_col(df, ct)
    if not dc or not sc: return None
    tmp = df.copy()
    tmp[dc] = pd.to_datetime(tmp[dc], errors="coerce")
    tmp = tmp.dropna(subset=[dc])
    if tmp.empty: return None
    tmp["month"] = tmp[dc].dt.month.astype(int)
    tmp["year"]  = tmp[dc].dt.year.astype(int)
    piv = tmp.pivot_table(index="year", columns="month", values=sc, aggfunc="sum").fillna(0)
    piv.columns = piv.columns.astype(int)
    piv.index   = piv.index.astype(int)
    fig, ax = plt.subplots(figsize=(5.4, 2.9))
    fig.patch.set_facecolor("white")
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    im = ax.imshow(piv.values, cmap="BuPu", aspect="auto", interpolation="nearest")
    ax.set_xticks(range(piv.shape[1]))
    ax.set_xticklabels([months[m-1] for m in piv.columns], fontsize=7)
    ax.set_yticks(range(piv.shape[0]))
    ax.set_yticklabels([str(y) for y in piv.index], fontsize=7)
    # Highlight peak cell
    flat_max = np.unravel_index(np.argmax(piv.values), piv.values.shape)
    ax.add_patch(plt.Rectangle((flat_max[1]-0.5, flat_max[0]-0.5), 1, 1,
                                fill=False, edgecolor="#FBBF24", lw=2.5))
    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.04)
    cbar.ax.tick_params(labelsize=6)
    _chart_title(ax, f"{sc} Seasonality Heatmap", CHART_PALETTE["heatmap"])
    plt.tight_layout(pad=0.6)
    return _save(fig)


# ════════════════════════════════════════════════════════════════════════════════
# REPORTLAB PDF HELPERS
# ════════════════════════════════════════════════════════════════════════════════
def _ps(name, **kw):
    return ParagraphStyle(name, **kw)

def _styles():
    return {
        "section": _ps("sec", fontName="Helvetica-Bold", fontSize=11.5,
                       textColor=colors.HexColor(BRAND["deep"]),
                       spaceBefore=5, spaceAfter=2),
        "sub":     _ps("sub", fontName="Helvetica-Bold", fontSize=9,
                       textColor=colors.HexColor(BRAND["mid"]),
                       spaceBefore=4, spaceAfter=2),
        "body":    _ps("body", fontName="Helvetica", fontSize=8.5,
                       textColor=colors.HexColor(BRAND["ink"]),
                       leading=13, spaceAfter=2),
        "bullet":  _ps("blt", fontName="Helvetica", fontSize=8.5,
                       textColor=colors.HexColor(BRAND["ink"]),
                       leading=13, spaceAfter=2, leftIndent=12),
        "note":    _ps("note", fontName="Helvetica-Oblique", fontSize=7,
                       textColor=colors.HexColor(BRAND["muted"])),
    }

def _section_block(text, ST):
    return [
        Paragraph(text, ST["section"]),
        HRFlowable(width="100%", thickness=0.9,
                   color=colors.HexColor(BRAND["soft"]), spaceAfter=5),
    ]

def _hf(canvas, doc):
    """Branded header + footer on every page."""
    canvas.saveState()
    W, H = A4

    # Header — deep band
    canvas.setFillColor(colors.HexColor(BRAND["deep"]))
    canvas.rect(0, H - 20*mm, W, 20*mm, fill=1, stroke=0)

    # Teal left accent strip
    canvas.setFillColor(colors.HexColor(BRAND["teal"]))
    canvas.rect(0, H - 20*mm, 4*mm, 20*mm, fill=1, stroke=0)

    # Report title
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 11.5)
    canvas.drawString(10*mm, H - 12*mm, "Zero Click AI  ·  Comprehensive Analysis Report")

    # Sub-line
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor(BRAND["soft"]))
    canvas.drawString(10*mm, H - 17.5*mm,
                      f"Report Date: {NOW.strftime('%d %b %Y')}  |  "
                      f"Generated: {NOW.strftime('%H:%M')}  |  Genesis Training")
    canvas.drawRightString(W - 10*mm, H - 17.5*mm, "Source: Zero Click AI")

    # Footer
    canvas.setFillColor(colors.HexColor(BRAND["pale"]))
    canvas.rect(0, 0, W, 10*mm, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor(BRAND["teal"]))
    canvas.rect(0, 0, 3*mm, 10*mm, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor(BRAND["muted"]))
    canvas.setFont("Helvetica", 7)
    canvas.drawCentredString(W/2, 3.5*mm,
                             f"Page {doc.page}  |  Confidential — For Internal Use Only")
    canvas.restoreState()

def _kpi_row(kpi_triples, start_idx, pw):
    col_w = (pw - 8*mm) / 3
    cells = []
    for i, (lbl, val, dlt) in enumerate(kpi_triples):
        idx     = (start_idx + i) % len(KPI_CARDS)
        bg, acc = KPI_CARDS[idx]
        is_pos  = not str(dlt).lstrip().startswith("-")
        dlt_col = colors.HexColor(BRAND["green"]) if is_pos else colors.HexColor(BRAND["red"])
        sym     = "▲" if is_pos else "▼"
        inner = Table(
            [[Paragraph(str(val)[:14],
                        _ps(f"kv{i}", fontName="Helvetica-Bold", fontSize=15,
                            textColor=colors.HexColor(acc), alignment=TA_CENTER))],
             [Paragraph(f"{sym}  {dlt}",
                        _ps(f"kd{i}", fontName="Helvetica", fontSize=7.5,
                            textColor=dlt_col, alignment=TA_CENTER))],
             [Paragraph(str(lbl)[:26],
                        _ps(f"kl{i}", fontName="Helvetica-Bold", fontSize=7,
                            textColor=colors.HexColor(BRAND["muted"]),
                            alignment=TA_CENTER))]],
            colWidths=[col_w],
            style=TableStyle([
                ("BACKGROUND",    (0,0),(-1,-1), colors.HexColor(bg)),
                ("BOX",           (0,0),(-1,-1), 1.2, colors.HexColor(acc)),
                ("LINEABOVE",     (0,0),(-1,0),  3,   colors.HexColor(acc)),
                ("TOPPADDING",    (0,0),(-1,-1), 8),
                ("BOTTOMPADDING", (0,0),(-1,-1), 8),
                ("ALIGN",         (0,0),(-1,-1), "CENTER"),
                ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
            ])
        )
        cells.append(inner)

    return Table([cells],
                 colWidths=[col_w + 2.5*mm]*3,
                 style=TableStyle([
                     ("ALIGN",         (0,0),(-1,-1), "CENTER"),
                     ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
                     ("LEFTPADDING",   (0,0),(-1,-1), 2),
                     ("RIGHTPADDING",  (0,0),(-1,-1), 2),
                 ]))

def _data_table(headers, rows, col_w_mm):
    cw   = [w * mm for w in col_w_mm]
    data = [headers] + rows
    style = [
        ("BACKGROUND",    (0,0),(-1,0),  colors.HexColor(BRAND["deep"])),
        ("TEXTCOLOR",     (0,0),(-1,0),  colors.white),
        ("FONTNAME",      (0,0),(-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",       (0,0),(-1,0),  8),
        ("FONTNAME",      (0,1),(-1,-1), "Helvetica"),
        ("FONTSIZE",       (0,1),(-1,-1), 7.5),
        ("ALIGN",         (0,0),(-1,-1), "CENTER"),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("GRID",          (0,0),(-1,-1), 0.3, colors.HexColor(BRAND["rule"])),
        ("TOPPADDING",    (0,0),(-1,-1), 3.5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 3.5),
        ("LINEBELOW",     (0,0),(-1,0),  2, colors.HexColor(BRAND["teal"])),
    ]
    for r in range(1, len(data)):
        bg = BRAND["row_a"] if r % 2 == 1 else BRAND["row_b"]
        style.append(("BACKGROUND", (0,r),(-1,r), colors.HexColor(bg)))
    tbl = Table(data, colWidths=cw, repeatRows=1)
    tbl.setStyle(TableStyle(style))
    return tbl

def _chart_img(buf, w_mm, h_mm):
    if buf is None: return Spacer(w_mm*mm, h_mm*mm)
    return RLImage(buf, width=w_mm*mm, height=h_mm*mm)


# ════════════════════════════════════════════════════════════════════════════════
# MAIN PDF GENERATOR
# ════════════════════════════════════════════════════════════════════════════════
def generate_report_pdf(df, kpis, ml_results, forecast_data, insights, charts) -> bytes:
    if not HAS_RL:
        return b""

    ct = _col_types(df)
    ST = _styles()
    pw = A4[0] - 24*mm

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=24*mm, bottomMargin=14*mm,
        leftMargin=12*mm, rightMargin=12*mm,
    )
    story = []

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 1 — EXECUTIVE DASHBOARD
    # ══════════════════════════════════════════════════════════════════════════
    banner = Table(
        [[Paragraph("EXECUTIVE PERFORMANCE DASHBOARD",
                    _ps("bh", fontName="Helvetica-Bold", fontSize=12,
                        textColor=colors.white, alignment=TA_CENTER))]],
        colWidths=[pw],
        style=TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), colors.HexColor(BRAND["mid"])),
            ("TOPPADDING",    (0,0),(-1,-1), 9),
            ("BOTTOMPADDING", (0,0),(-1,-1), 9),
            ("LINEABOVE",     (0,0),(-1,0),  3, colors.HexColor(BRAND["teal"])),
            ("LINEBELOW",     (0,0),(-1,-1), 3, colors.HexColor(BRAND["teal"])),
        ])
    )
    story.append(banner)
    story.append(Spacer(1, 5*mm))

    kpi_list = list(kpis or [])
    while len(kpi_list) < 6:
        kpi_list.append(("N/A", "—", "—"))

    def _ktriple(k):
        if len(k) >= 3: return (str(k[0]), str(k[1]), str(k[2]))
        if len(k) == 2: return (str(k[0]), str(k[1]), "—")
        return (str(k[0]), "—", "—")

    story.append(_kpi_row([_ktriple(kpi_list[i]) for i in range(3)], 0, pw))
    story.append(Spacer(1, 4*mm))
    story.append(_kpi_row([_ktriple(kpi_list[i]) for i in range(3, 6)], 3, pw))
    story.append(Spacer(1, 7*mm))

    # AI Summary
    ai_hdr = Table(
        [[Paragraph("  ◈  AI NARRATED SUMMARY",
                    _ps("aih", fontName="Helvetica-Bold", fontSize=9,
                        textColor=colors.HexColor(BRAND["deep"])))]],
        colWidths=[pw],
        style=TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), colors.HexColor(BRAND["pale"])),
            ("LINEABOVE",     (0,0),(-1,0),  3, colors.HexColor(BRAND["teal"])),
            ("TOPPADDING",    (0,0),(-1,-1), 5),
            ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ])
    )
    story.append(ai_hdr)

    ai_short = ""
    if isinstance(insights, str):
        lines = [l.strip() for l in insights.split("\n")
                 if l.strip() and not l.strip().startswith("#")]
        ai_short = " ".join(lines[:5])[:700]
    elif isinstance(insights, list):
        ai_short = " ".join(str(i) for i in insights[:5])[:700]

    ai_body = Table(
        [[Paragraph(ai_short or "Analysis complete.", ST["body"])]],
        colWidths=[pw],
        style=TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), colors.white),
            ("BOX",           (0,0),(-1,-1), 0.6, colors.HexColor(BRAND["rule"])),
            ("TOPPADDING",    (0,0),(-1,-1), 9),
            ("BOTTOMPADDING", (0,0),(-1,-1), 9),
            ("LEFTPADDING",   (0,0),(-1,-1), 12),
            ("RIGHTPADDING",  (0,0),(-1,-1), 12),
        ])
    )
    story.append(ai_body)
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        "*Profit margin = Profit / Sales  |  Data reflects the period shown in available records.",
        ST["note"]))

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 2 — VISUAL ANALYTICS
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.extend(_section_block("Visual Analytics", ST))

    chart_defs = [
        (f"{_sales_col(df,ct) or 'Sales'} by Region",
         lambda: chart_region(df, ct)),
        (f"Sales by {_cat_col(df,ct) or 'Category'}",
         lambda: chart_category(df, ct)),
        (f"Monthly {_sales_col(df,ct) or 'Sales'} Trend",
         lambda: chart_trend(df, ct)),
        (f"{_sales_col(df,ct) or 'Sales'} vs {_profit_col(df,ct) or 'Profit'}",
         lambda: chart_scatter(df, ct)),
        ("Monthly Order Volume",
         lambda: chart_orders(df, ct)),
        (f"{_sales_col(df,ct) or 'Sales'} Seasonality",
         lambda: chart_heatmap(df, ct)),
    ]

    rendered = []
    for title, fn in chart_defs:
        try:
            b = fn()
            if b: rendered.append((title, b))
        except Exception as e:
            print(f"  Chart '{title}' skipped: {e}")

    CW = (pw - 5*mm) / 2
    CH = 66

    for i in range(0, len(rendered), 2):
        lt, lb = rendered[i]
        rt, rb = rendered[i+1] if i+1 < len(rendered) else (None, None)
        li = _chart_img(lb, CW/mm, CH)
        ri = _chart_img(rb, CW/mm, CH) if rb else Spacer(CW, CH*mm)

        def _cap(t):
            return Paragraph(t or "",
                             _ps("ct", fontName="Helvetica-Bold", fontSize=7.5,
                                 textColor=colors.HexColor(BRAND["muted"]),
                                 alignment=TA_CENTER))

        grid = Table(
            [[_cap(lt), _cap(rt)], [li, ri]],
            colWidths=[CW, CW],
            style=TableStyle([
                ("ALIGN",         (0,0),(-1,-1), "CENTER"),
                ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
                ("LEFTPADDING",   (0,0),(-1,-1), 2),
                ("RIGHTPADDING",  (0,0),(-1,-1), 2),
                ("BOTTOMPADDING", (0,0),(-1,-1), 4),
            ])
        )
        story.append(grid)
        if i + 2 < len(rendered):
            story.append(Spacer(1, 2*mm))

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 3 — TOP ITEMS + AI INSIGHTS (two-column)
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.extend(_section_block("Top Records by Key Metric", ST))

    tp    = _top_items(df, ct, n=16)
    hdrs  = list(tp.columns)
    nc    = len(hdrs)
    t_pw  = pw * 0.55
    i_pw  = pw * 0.41

    col_w = [8] + [int((t_pw/mm - 10) / (nc-1))] * (nc-1)
    t_rows = [[str(tp.iloc[r][c])[:20] for c in tp.columns] for r in range(len(tp))]
    prod_tbl = _data_table(hdrs, t_rows, col_w)

    # Build insights paragraphs
    full_ins = (insights if isinstance(insights, str)
                else "\n".join(f"• {i}" for i in (insights or [])))
    ins_items = [
        Paragraph("AI Insights", ST["section"]),
        HRFlowable(width="100%", thickness=0.9,
                   color=colors.HexColor(BRAND["soft"]), spaceAfter=5),
    ]
    for line in full_ins.split("\n"):
        line = line.strip()
        if not line:
            ins_items.append(Spacer(1, 2*mm))
        elif line.startswith("## "):
            ins_items.append(Paragraph(line[3:], ST["sub"]))
        elif line.startswith(("- ","• ","* ")):
            ins_items.append(Paragraph(f"• {line[2:]}", ST["bullet"]))
        else:
            ins_items.append(Paragraph(line, ST["body"]))

    ins_tbl = Table(
        [[item] for item in ins_items],
        colWidths=[i_pw],
        style=TableStyle([
            ("TOPPADDING",    (0,0),(-1,-1), 1),
            ("BOTTOMPADDING", (0,0),(-1,-1), 1),
            ("LEFTPADDING",   (0,0),(-1,-1), 8),
            ("RIGHTPADDING",  (0,0),(-1,-1), 0),
        ])
    )

    two_col = Table(
        [[prod_tbl, ins_tbl]],
        colWidths=[t_pw + 2*mm, i_pw],
        style=TableStyle([
            ("VALIGN",       (0,0),(-1,-1), "TOP"),
            ("LEFTPADDING",  (0,0),(-1,-1), 0),
            ("RIGHTPADDING", (0,0),(-1,-1), 0),
            ("LINEBEFORE",   (1,0),(1,-1), 0.5, colors.HexColor(BRAND["rule"])),
        ])
    )
    story.append(two_col)

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 4 — DATASET SAMPLE
    # ══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    story.extend(_section_block("Dataset Sample — First 20 Rows", ST))

    sample = df.head(20).astype(str)
    cols   = list(sample.columns[:8])
    nc2    = len(cols)
    cw2    = [int(pw/mm / nc2)] * nc2
    s_rows = [[str(sample.iloc[r][c])[:16] for c in cols] for r in range(len(sample))]
    story.append(_data_table([c[:14] for c in cols], s_rows, cw2))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        f"Showing first 20 of {len(df):,} records  |  {len(df.columns)} columns total.",
        ST["note"]))

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 5 (OPTIONAL) — FORECAST
    # ══════════════════════════════════════════════════════════════════════════
    if forecast_data:
        story.append(PageBreak())
        story.extend(_section_block("Time-Series Forecast", ST))
        story.append(Paragraph(
            f"Model: {forecast_data.get('model','N/A')}  |  Horizon: 6 months", ST["body"]))
        story.append(Spacer(1, 3*mm))
        fdf = forecast_data.get("forecast_df")
        if fdf is not None and not fdf.empty:
            f_hdrs = ["Period", "Predicted", "Lower 95%", "Upper 95%"]
            f_cw   = [50, 44, 44, 44]
            f_rows = []
            for _, row in fdf.head(12).iterrows():
                dt = str(row.get("ds","")).split(" ")[0]
                f_rows.append([dt,
                               f"${_num(row.get('yhat',0)):,.0f}",
                               f"${_num(row.get('yhat_lower',0)):,.0f}",
                               f"${_num(row.get('yhat_upper',0)):,.0f}"])
            story.append(_data_table(f_hdrs, f_rows, f_cw))

    # ML page — only if populated
    if ml_results:
        story.append(PageBreak())
        story.extend(_section_block("Machine Learning Insights", ST))
        for res in ml_results:
            story.append(Paragraph(f"■  {res.get('title','Model')}", ST["sub"]))
            story.append(Paragraph(
                f"    {res.get('metric_name')}: {res.get('metric_value')}",
                _ps("mv", fontName="Helvetica", fontSize=8.5,
                    textColor=colors.HexColor(BRAND["green"]), spaceAfter=2)))
            story.append(Paragraph(
                f"    Type: {res.get('type')}  |  {res.get('extra','')}",
                ST["body"]))
            story.append(Spacer(1, 3*mm))

    doc.build(story, onFirstPage=_hf, onLaterPages=_hf)
    return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════════════
# EXCEL REPORT
# ════════════════════════════════════════════════════════════════════════════════
def _xl_hdr(ws, row, headers, accent):
    fill = PatternFill("solid", fgColor=accent)
    fnt  = Font(bold=True, color="FFFFFF", size=10)
    bdr  = Border(left=Side(style="thin"), right=Side(style="thin"),
                  top=Side(style="thin"), bottom=Side(style="medium"))
    for ci, h in enumerate(headers, 1):
        c = ws.cell(row=row, column=ci, value=h)
        c.fill = fill; c.font = fnt; c.border = bdr
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(ci)].width = max(14, len(str(h))+5)
    ws.row_dimensions[row].height = 20

def _xl_data_row(ws, ri, vals, alt=False):
    hex_bg = "F5F3FF" if alt else "FFFFFF"
    fill = PatternFill("solid", fgColor=hex_bg)
    bdr  = Border(left=Side(style="thin"), right=Side(style="thin"),
                  top=Side(style="thin"),  bottom=Side(style="thin"))
    for ci, val in enumerate(vals, 1):
        c = ws.cell(row=ri, column=ci, value=val)
        c.fill = fill; c.border = bdr
        c.font = Font(size=9)
        c.alignment = Alignment(horizontal="center", vertical="center")

def _xl_title(ws, text, row=1, end_col=8, accent="4C1D95"):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=end_col)
    c = ws.cell(row=row, column=1, value=text)
    c.fill = PatternFill("solid", fgColor=accent)
    c.font = Font(bold=True, color="FFFFFF", size=13)
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[row].height = 28

def _xl_subtitle(ws, text, row, end_col=8, accent="0D9488"):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=end_col)
    c = ws.cell(row=row, column=1, value=text)
    c.fill = PatternFill("solid", fgColor=accent)
    c.font = Font(bold=True, color="FFFFFF", size=9)
    c.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[row].height = 16

def _write_df(ws, df_in, start=3, accent="4C1D95"):
    hdrs = list(df_in.columns)
    _xl_hdr(ws, start, hdrs, accent)
    for ri, (_, row) in enumerate(df_in.iterrows(), 1):
        vals = list(row)
        _xl_data_row(ws, start+ri, vals, alt=ri%2==0)
        for ci, val in enumerate(vals, 1):
            cell = ws.cell(row=start+ri, column=ci)
            cn   = hdrs[ci-1].lower()
            if any(kw in cn for kw in ["mom","growth","pct","share"]):
                try:
                    v = float(val)
                    cell.font = Font(size=9, bold=True,
                                     color="166534" if v>=0 else "991B1B")
                    cell.value = f"+{v*100:.2f}%" if v>=0 else f"{v*100:.2f}%"
                except: pass
            elif any(kw in cn for kw in ["sales","revenue","profit","amount","price","total","fee"]):
                try: cell.value = float(val); cell.number_format = '#,##0.00'
                except: pass

def _parse_kpi_numeric(s):
    s = str(s).strip().replace(",","").replace("$","").replace("%","")
    s = s.replace("B","e9").replace("M","e6").replace("K","e3").replace("k","e3")
    try:    return float(s)
    except: return None


def generate_report_excel(df, kpis, ml_results, forecast_data, insights) -> bytes:
    if not HAS_OXL:
        return b""

    ct = _col_types(df)
    wb = openpyxl.Workbook()

    # README
    ws = wb.active; ws.title = "README"
    acc = XL_ACCENTS["README"]
    _xl_title(ws, "Zero Click AI  ·  Comprehensive Analysis Report", 1, 6, acc)
    _xl_subtitle(ws, "Report Summary", 2, 6, XL_ACCENTS["KPIs"])
    info = [
        ("Report Date",   NOW.strftime("%d %b %Y  %H:%M")),
        ("Platform",      "Zero Click AI  ·  Genesis Training"),
        ("Total Rows",    f"{len(df):,}"),
        ("Total Columns", f"{len(df.columns)}"),
        ("AI Summary",    (insights[:300] if isinstance(insights,str) else str(insights)[:300])),
    ]
    for ri, (k, v) in enumerate(info, 3):
        ws.cell(row=ri, column=1, value=k).font = Font(bold=True, color=acc, size=10)
        c2 = ws.cell(row=ri, column=2, value=v)
        c2.font = Font(size=10)
        c2.alignment = Alignment(wrap_text=True)
        ws.row_dimensions[ri].height = 18
    ws.column_dimensions["A"].width = 20
    ws.column_dimensions["B"].width = 72

    # KPIs
    ws2 = wb.create_sheet("KPIs")
    acc2 = XL_ACCENTS["KPIs"]
    _xl_title(ws2, "Key Performance Indicators", 1, 5, XL_ACCENTS["README"])
    _xl_subtitle(ws2, "Core business metrics", 2, 5, acc2)
    kpi_rows = [[str(k[0]), str(k[1]), str(k[2]) if len(k)>2 else ""]
                for k in (kpis or [])]
    _xl_hdr(ws2, 3, ["Metric", "Value", "Description", "", "Numeric Value"], acc2)
    for i, r in enumerate(kpi_rows):
        _xl_data_row(ws2, i+4, r + ["",""], alt=i%2==0)
        nv = _parse_kpi_numeric(r[1]) if len(r)>1 else None
        if nv is not None:
            cell = ws2.cell(row=i+4, column=5, value=nv)
            cell.font = Font(size=9, bold=True, color="047857")
            cell.alignment = Alignment(horizontal="center")
            cell.fill = PatternFill("solid", fgColor="ECFDF5")
            cell.number_format = '#,##0.00'
    ws2.column_dimensions["A"].width = 30
    ws2.column_dimensions["B"].width = 20
    ws2.column_dimensions["C"].width = 40
    ws2.column_dimensions["E"].width = 20
    n_kpi = len(kpi_rows)
    if n_kpi >= 2:
        ch = BarChart(); ch.type = "bar"; ch.title = "KPI Overview"
        ch.style = 10; ch.width = 20; ch.height = max(10, n_kpi*1.4)
        data = Reference(ws2, min_col=5, min_row=3, max_row=3+n_kpi)
        cats = Reference(ws2, min_col=1, min_row=4, max_row=3+n_kpi)
        ch.add_data(data, titles_from_data=True); ch.set_categories(cats)
        ch.series[0].graphicalProperties.solidFill = acc2
        ws2.add_chart(ch, "G3")

    # Sales by Region
    ws3 = wb.create_sheet("Sales_by_Region")
    acc3 = XL_ACCENTS["Sales_by_Region"]
    sc_lbl = _sales_col(df,ct) or "Sales"
    rg_lbl = _reg_col(df,ct)  or "Region"
    _xl_title(ws3, f"{sc_lbl} by {rg_lbl}", 1, 4, XL_ACCENTS["README"])
    _xl_subtitle(ws3, "Regional performance breakdown", 2, 4, acc3)
    rbr = _sales_by_region(df, ct).sort_values("Sales", ascending=False)
    _write_df(ws3, rbr, start=3, accent=acc3)
    if len(rbr) >= 2:
        ch = BarChart(); ch.title = f"{sc_lbl} by Region"; ch.style = 10
        ch.width = 16; ch.height = 10
        data = Reference(ws3, min_col=2, min_row=3, max_row=3+len(rbr))
        cats = Reference(ws3, min_col=1, min_row=4, max_row=3+len(rbr))
        ch.add_data(data, titles_from_data=True); ch.set_categories(cats)
        ch.series[0].graphicalProperties.solidFill = acc3
        ws3.add_chart(ch, "D3")

    # Sales by Category
    ws4 = wb.create_sheet("Sales_by_Category")
    acc4 = XL_ACCENTS["Sales_by_Category"]
    ct_lbl = _cat_col(df,ct) or "Category"
    _xl_title(ws4, f"{sc_lbl} by {ct_lbl}", 1, 5, XL_ACCENTS["README"])
    _xl_subtitle(ws4, "Category distribution", 2, 5, acc4)
    sbc = _sales_by_category(df, ct).sort_values("Sales", ascending=False)
    _write_df(ws4, sbc, start=3, accent=acc4)
    if len(sbc) >= 2:
        ch = BarChart(); ch.title = f"{sc_lbl} by {ct_lbl}"; ch.style = 10
        ch.width = 18; ch.height = 12
        data = Reference(ws4, min_col=2, min_row=3, max_row=3+len(sbc))
        cats = Reference(ws4, min_col=1, min_row=4, max_row=3+len(sbc))
        ch.add_data(data, titles_from_data=True); ch.set_categories(cats)
        ch.series[0].graphicalProperties.solidFill = acc4
        ws4.add_chart(ch, "E3")

    # Top Products
    ws5 = wb.create_sheet("Top_Products")
    acc5 = XL_ACCENTS["Top_Products"]
    _xl_title(ws5, "Top Items by Revenue", 1, 6, XL_ACCENTS["README"])
    _xl_subtitle(ws5, "Ranked by total sales", 2, 6, acc5)
    tp = _top_items(df, ct, n=10)
    _write_df(ws5, tp, start=3, accent=acc5)
    if "Profit" in tp.columns:
        pci = list(tp.columns).index("Profit") + 1
        for ri in range(4, 4+len(tp)):
            cell = ws5.cell(row=ri, column=pci)
            try:
                v = float(cell.value)
                cell.fill = PatternFill("solid", fgColor="DCFCE7" if v>0 else "FEE2E2")
                cell.font = Font(color="166534" if v>0 else "991B1B", size=9, bold=True)
                cell.number_format = '#,##0.00'; cell.value = v
            except: pass

    # Monthly Trend
    ws6 = wb.create_sheet("Monthly_Trend")
    acc6 = XL_ACCENTS["Monthly_Trend"]
    _xl_title(ws6, f"Monthly {sc_lbl} Trend", 1, 5, XL_ACCENTS["README"])
    _xl_subtitle(ws6, "Month-over-month performance", 2, 5, acc6)
    mt = _monthly_trend(df, ct)
    if mt.empty:
        ws6.cell(row=4, column=1, value="No datetime column detected.")
    else:
        _write_df(ws6, mt, start=3, accent=acc6)
        ch = LineChart(); ch.title = f"Monthly {sc_lbl}"; ch.style = 10
        ch.width = 20; ch.height = 10
        data = Reference(ws6, min_col=2, min_row=3, max_row=3+len(mt))
        ch.add_data(data, titles_from_data=True)
        ch.series[0].graphicalProperties.solidFill = acc6
        ws6.add_chart(ch, "E3")

    # Raw Data
    ws7 = wb.create_sheet("Raw_Data")
    acc7 = XL_ACCENTS["Raw_Data"]
    end  = min(len(df.columns), 14)
    _xl_title(ws7, f"Raw Cleaned Dataset  ·  First 500 rows", 1, end, XL_ACCENTS["README"])
    _xl_subtitle(ws7, f"{len(df):,} total rows  ·  {len(df.columns)} columns", 2, end, acc7)
    _write_df(ws7, df.head(500), start=3, accent=acc7)

    for sheet in [ws2, ws3, ws4, ws5, ws6, ws7]:
        sheet.freeze_panes = "A4"
    for sheet in [ws3, ws4, ws5, ws6, ws7]:
        sheet.auto_filter.ref = sheet.dimensions

    out = io.BytesIO()
    wb.save(out)
    out.seek(0)
    return out.read()
