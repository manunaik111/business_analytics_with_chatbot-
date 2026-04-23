"""data_analysis.py — Column type detection, statistics, correlations."""
import pandas as pd
import numpy as np

def get_column_types(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {"numeric": [], "categorical": [], "datetime": [], "boolean": []}

    num  = df.select_dtypes(include=[np.number]).columns.tolist()
    cat  = df.select_dtypes(include=["object", "category"]).columns.tolist()
    dt   = df.select_dtypes(include=["datetime64", "datetimetz"]).columns.tolist()
    bool_cols = df.select_dtypes(include=["bool"]).columns.tolist()

    # Try object columns that look like dates
    if not dt:
        for col in list(cat):
            if any(k in col.lower() for k in ["date", "time", "year", "month"]):
                try:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                    if df[col].notna().sum() > 0.5 * len(df):
                        dt.append(col)
                        cat.remove(col)
                except Exception:
                    pass

    return {"numeric": num, "categorical": cat, "datetime": dt, "boolean": bool_cols}

def compute_stats(df: pd.DataFrame) -> pd.DataFrame:
    num_cols = df.select_dtypes(include=[np.number]).columns
    if len(num_cols) == 0:
        return pd.DataFrame()
    return df[num_cols].describe().round(3)

def find_correlations(df: pd.DataFrame) -> list:
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(num_cols) < 2:
        return []
    corr = df[num_cols].corr()
    pairs = []
    for i, a in enumerate(num_cols):
        for b in num_cols[i + 1:]:
            score = corr.loc[a, b]
            if pd.notna(score) and abs(score) > 0.3:
                pairs.append({"col1": a, "col2": b, "score": round(float(score), 3)})
    pairs.sort(key=lambda x: abs(x["score"]), reverse=True)
    return pairs[:10]

def compute_group_impacts(df: pd.DataFrame, column_types: dict) -> list:
    impacts = []
    for cat in column_types.get("categorical", [])[:5]:
        for num in column_types.get("numeric", [])[:5]:
            try:
                if "id" in cat.lower() or "code" in cat.lower():
                    continue
                groups = df.groupby(cat)[num].mean().sort_values(ascending=False)
                if len(groups) < 2:
                    continue
                top_cat, top_val     = groups.index[0], float(groups.iloc[0])
                bottom_cat, bot_val  = groups.index[-1], float(groups.iloc[-1])
                denom = abs(bot_val) if bot_val != 0 else 1
                diff  = abs((top_val - bot_val) / denom) * 100
                impacts.append({
                    "cat": cat, "num": num,
                    "top": (top_cat, top_val),
                    "bottom": (bottom_cat, bot_val),
                    "diff": round(diff, 1),
                    "means": groups.reset_index().values.tolist(),
                })
            except Exception:
                continue
    impacts.sort(key=lambda x: x["diff"], reverse=True)
    return impacts
