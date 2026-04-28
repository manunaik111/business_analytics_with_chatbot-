"""kpi_generator.py — Smart KPI generation from any dataset."""
import pandas as pd
import numpy as np
from dashboard import data_analysis
from dashboard import data_cleaning
from dashboard import utils

def _fmt(col_name: str, value) -> str:
    col_lower = str(col_name).lower()
    if any(k in col_lower for k in ["percentage", "rate", "margin", "discount"]):
        v = float(value)
        if abs(v) <= 1.0 and v != 0:
            return f"{v * 100:.1f}%"
        return f"{v:.1f}%"
    val_str = utils.format_number(value)
    if any(k in col_lower for k in ["price", "cost", "revenue", "sales", "amount", "profit", "budget"]):
        return f"${val_str}"
    return val_str

def generate_kpis(df: pd.DataFrame, column_types: dict) -> list:
    if df is None or df.empty:
        return []

    kpis = []
    report = data_cleaning.get_cleaning_report()

    kpis.append(("Total Records", f"{len(df):,}", "Rows in cleaned dataset"))
    if report.get("missing_filled", 0) > 0:
        kpis.append(("Missing Repaired", f"{report['missing_filled']:,}", "Cells imputed automatically"))
    if report.get("duplicates_removed", 0) > 0:
        kpis.append(("Duplicates Removed", f"{report['duplicates_removed']:,}", "Rows deduplicated"))

    raw_num = column_types.get("numeric", [])
    num_cols = [c for c in raw_num if not any(k in c.lower() for k in ["id", "index", "code"])]
    cat_cols = column_types.get("categorical", [])
    date_cols = column_types.get("datetime", [])
    used = set()

    # Volume metrics (sum)
    vol_kw = ["sales", "revenue", "profit", "amount", "total", "cost", "qty", "quantity", "volume", "budget"]
    for col in [c for c in num_cols if any(w in c.lower() for w in vol_kw)][:3]:
        total = df[col].sum()
        avg   = df[col].mean()
        short = str(col)[:15] + ("…" if len(str(col)) > 15 else "")
        kpis.append((f"Total {short}", _fmt(col, total), f"Avg: {_fmt(col, avg)} per row"))
        used.add(col)

    # Ratio metrics (mean)
    for col in [c for c in num_cols if c not in used][:3]:
        avg = df[col].mean()
        mn  = df[col].min()
        mx  = df[col].max()
        short = str(col)[:15] + ("…" if len(str(col)) > 15 else "")
        kpis.append((f"Avg {short}", _fmt(col, avg), f"Range {_fmt(col, mn)} – {_fmt(col, mx)}"))
        used.add(col)

    # Computed margins
    cols_l = [c.lower() for c in num_cols]
    if "revenue" in cols_l and "cost" in cols_l:
        r = num_cols[cols_l.index("revenue")]
        c = num_cols[cols_l.index("cost")]
        rev, cost = df[r].sum(), df[c].sum()
        if rev > 0:
            kpis.insert(1, ("Gross Margin", f"{(rev - cost) / rev * 100:.1f}%", "Revenue minus cost"))
    if "profit" in cols_l and "revenue" in cols_l:
        p = num_cols[cols_l.index("profit")]
        r = num_cols[cols_l.index("revenue")]
        if df[r].sum() > 0:
            kpis.insert(2, ("Profit Margin", f"{df[p].sum() / df[r].sum() * 100:.1f}%", "Overall profitability"))

    # Top correlation
    corrs = data_analysis.find_correlations(df)
    if corrs:
        top = corrs[0]
        c1 = str(top["col1"])[:12] + ("…" if len(str(top["col1"])) > 12 else "")
        c2 = str(top["col2"])[:12] + ("…" if len(str(top["col2"])) > 12 else "")
        kpis.append(("Top Correlation", f"{top['score']:.2f}", f"{c1} ↔ {c2}"))

    # Top categorical segment
    for col in cat_cols:
        if df[col].nunique() > 1:
            try:
                top_val   = df[col].mode().iloc[0]
                top_count = int((df[col] == top_val).sum())
                short     = str(col)[:15] + ("…" if len(str(col)) > 15 else "")
                val_fmt   = str(top_val)[:22] + ("…" if len(str(top_val)) > 22 else "")
                kpis.append((f"Top {short}", f"{utils.format_number(top_count)}", f"Value: '{val_fmt}'"))
                break
            except Exception:
                pass

    # Date range
    if date_cols:
        d = date_cols[0]
        mn, mx = df[d].min(), df[d].max()
        if pd.notna(mn) and pd.notna(mx):
            days = (mx - mn).days
            kpis.append((f"Timeline ({str(d)[:10]})", f"{days} days",
                         f"{mn.strftime('%b %d %Y')} – {mx.strftime('%b %d %Y')}"))

    return kpis[:12]
