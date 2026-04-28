"""
data_management/dataset_profiling.py

Pure-Python dataset profiling — works for any dataset type.
No Streamlit dependency. Called from api.py /api/data/profile endpoint.

The Streamlit UI functions (dataset_profiling_section, plot_*) are kept
inside optional try/except blocks so the Streamlit app can still call them,
but the FastAPI endpoint only needs generate_profiling_table() and
generate_profiling_summary().
"""

import io
import pandas as pd
import numpy as np

# ── Optional UI dependencies (Streamlit app only) ─────────────────────────────
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    st = None           # type: ignore[assignment]
    HAS_STREAMLIT = False

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    HAS_PLOTTING = True
except ImportError:
    plt = None          # type: ignore[assignment]
    sns = None          # type: ignore[assignment]
    HAS_PLOTTING = False


# ─────────────────────────────────────────────────────────────────────────────
#  CORE PROFILING — no optional dependencies below this line
# ─────────────────────────────────────────────────────────────────────────────

def get_column_type(series: pd.Series) -> str:
    """Classify a column as Numeric, Date, or Categorical."""
    if pd.api.types.is_numeric_dtype(series):
        return "Numeric"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "Date"
    # Try to parse as date without raising
    sample = series.dropna().head(50)
    if len(sample) > 0:
        try:
            parsed = pd.to_datetime(sample, errors="coerce")
            if parsed.notna().mean() > 0.8:
                return "Date"
        except Exception:
            pass
    return "Categorical"


def generate_profiling_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a column-level profiling summary as a DataFrame.
    Works for any dataset — sales, HR, accident, generic.
    """
    rows = []
    total = len(df)

    for col in df.columns:
        series   = df[col]
        col_type = get_column_type(series)
        missing  = int(series.isna().sum())
        miss_pct = round(missing / total * 100, 2) if total > 0 else 0.0
        unique   = int(series.nunique())

        if col_type == "Numeric":
            clean = series.dropna()
            min_v  = round(float(clean.min()),  4) if len(clean) else "N/A"
            max_v  = round(float(clean.max()),  4) if len(clean) else "N/A"
            mean_v = round(float(clean.mean()), 4) if len(clean) else "N/A"
            std_v  = round(float(clean.std()),  4) if len(clean) else "N/A"
        else:
            min_v = max_v = mean_v = std_v = "N/A"

        rows.append({
            "Column":         col,
            "Data Type":      col_type,
            "Missing Values": missing,
            "Missing %":      f"{miss_pct}%",
            "Unique Values":  unique,
            "Min":            min_v,
            "Max":            max_v,
            "Mean":           mean_v,
            "Std Dev":        std_v,
        })

    return pd.DataFrame(rows)


def generate_profiling_summary(df: pd.DataFrame) -> dict:
    """
    Return a JSON-serialisable profiling summary suitable for the API response.
    Works for any dataset type.
    """
    total_cells   = df.shape[0] * df.shape[1]
    missing_cells = int(df.isnull().sum().sum())
    completeness  = round((1 - missing_cells / total_cells) * 100, 2) if total_cells else 100.0
    dup_rows      = int(df.duplicated().sum())

    num_cols  = df.select_dtypes(include="number").columns.tolist()
    cat_cols  = df.select_dtypes(include=["object", "category"]).columns.tolist()
    date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]

    # Per-column missing counts
    missing_by_col = {
        col: {"count": int(df[col].isna().sum()),
              "pct":   round(df[col].isna().mean() * 100, 2)}
        for col in df.columns
        if df[col].isna().any()
    }

    # Numeric stats
    numeric_stats: dict = {}
    for col in num_cols:
        s = df[col].dropna()
        if len(s) == 0:
            continue
        numeric_stats[col] = {
            "min":    round(float(s.min()),    4),
            "max":    round(float(s.max()),    4),
            "mean":   round(float(s.mean()),   4),
            "median": round(float(s.median()), 4),
            "std":    round(float(s.std()),    4),
            "q25":    round(float(s.quantile(0.25)), 4),
            "q75":    round(float(s.quantile(0.75)), 4),
        }

    # Categorical top-value summaries
    categorical_stats: dict = {}
    for col in cat_cols[:10]:  # Cap at 10 to keep response size reasonable
        vc = df[col].value_counts()
        if len(vc) == 0:
            continue
        categorical_stats[col] = {
            "unique":     int(df[col].nunique()),
            "top_value":  str(vc.index[0]),
            "top_count":  int(vc.iloc[0]),
            "top_values": [
                {"value": str(k), "count": int(v)}
                for k, v in vc.head(5).items()
            ],
        }

    return {
        "overview": {
            "rows":          df.shape[0],
            "columns":       df.shape[1],
            "completeness":  completeness,
            "missing_cells": missing_cells,
            "duplicate_rows": dup_rows,
            "numeric_cols":  len(num_cols),
            "categorical_cols": len(cat_cols),
            "date_cols":     len(date_cols),
        },
        "missing_by_column":  missing_by_col,
        "numeric_stats":      numeric_stats,
        "categorical_stats":  categorical_stats,
        "column_names":       df.columns.tolist(),
        "numeric_columns":    num_cols,
        "categorical_columns": cat_cols,
        "date_columns":       date_cols,
    }


def validate_upload(
    df: pd.DataFrame,
    filename: str,
) -> list[str]:
    """
    Run structural validation on a freshly loaded DataFrame.
    Returns a list of warning strings (empty = no issues).
    This is called after parsing but before schema mapping.
    """
    warnings: list[str] = []

    if df.empty:
        warnings.append("The uploaded file has no rows.")
        return warnings  # Nothing else to check

    if len(df.columns) == 0:
        warnings.append("The uploaded file has no columns.")
        return warnings

    # Duplicate column names
    dup_cols = [c for c in df.columns if list(df.columns).count(c) > 1]
    if dup_cols:
        warnings.append(
            f"Duplicate column names detected: {', '.join(set(dup_cols))}. "
            "Please rename duplicate columns before uploading."
        )

    # All-null columns
    all_null = [c for c in df.columns if df[c].isna().all()]
    if all_null:
        warnings.append(
            f"The following columns are entirely empty and will be ignored: "
            f"{', '.join(all_null)}."
        )

    # High missing rate
    high_miss = [
        f"{c} ({df[c].isna().mean()*100:.0f}%)"
        for c in df.columns
        if 0 < df[c].isna().mean() < 1 and df[c].isna().mean() >= 0.5
    ]
    if high_miss:
        warnings.append(
            f"Columns with >50% missing values: {', '.join(high_miss)}."
        )

    # Too many rows for memory safety warning (informational only)
    if len(df) > 1_000_000:
        warnings.append(
            f"Large dataset: {len(df):,} rows. "
            "Some operations may be slower than usual."
        )

    return warnings


# ─────────────────────────────────────────────────────────────────────────────
#  STREAMLIT UI SECTION (only used by main_app.py / Streamlit)
# ─────────────────────────────────────────────────────────────────────────────

def _plot_missing_heatmap(df: pd.DataFrame):
    if not HAS_PLOTTING:
        return None
    fig, ax = plt.subplots(figsize=(max(10, len(df.columns) * 0.6), 5))
    missing_matrix = df.isnull().astype(int)
    sns.heatmap(
        missing_matrix,
        cmap="YlOrRd",
        cbar_kws={"label": "Missing (1) / Present (0)"},
        yticklabels=False,
        ax=ax,
        linewidths=0.1,
    )
    ax.set_title("Missing Value Heatmap", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Columns", fontsize=11)
    ax.set_ylabel("Rows", fontsize=11)
    plt.xticks(rotation=45, ha="right", fontsize=9)
    plt.tight_layout()
    return fig


def _plot_missing_bar(df: pd.DataFrame):
    if not HAS_PLOTTING:
        return None
    missing_pct = (df.isnull().sum() / len(df) * 100).sort_values(ascending=False)
    missing_pct = missing_pct[missing_pct > 0]
    if missing_pct.empty:
        return None
    fig, ax = plt.subplots(figsize=(max(8, len(missing_pct) * 0.7), 4))
    colors = ["#d62728" if v > 30 else "#ff7f0e" if v > 10 else "#1f77b4"
              for v in missing_pct.values]
    bars = ax.bar(missing_pct.index, missing_pct.values, color=colors, edgecolor="white")
    ax.set_title("Missing Values (%) per Column", fontsize=13, fontweight="bold", pad=10)
    ax.set_xlabel("Columns", fontsize=11)
    ax.set_ylabel("Missing %", fontsize=11)
    ax.set_ylim(0, 110)
    for bar, val in zip(bars, missing_pct.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                f"{val:.1f}%", ha="center", va="bottom", fontsize=8)
    plt.xticks(rotation=45, ha="right", fontsize=9)
    plt.tight_layout()
    return fig


def _plot_numeric_distributions(df: pd.DataFrame):
    if not HAS_PLOTTING:
        return None
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    if not numeric_cols:
        return None
    n_cols = 3
    n_rows = (len(numeric_cols) + n_cols - 1) // n_cols
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 3.5 * n_rows))
    axes = np.array(axes).flatten()
    for i, col in enumerate(numeric_cols):
        axes[i].hist(df[col].dropna(), bins=25, color="#4c72b0", edgecolor="white", alpha=0.85)
        axes[i].set_title(col, fontsize=10, fontweight="bold")
        axes[i].set_xlabel("Value", fontsize=8)
        axes[i].set_ylabel("Frequency", fontsize=8)
    for j in range(len(numeric_cols), len(axes)):
        axes[j].set_visible(False)
    plt.suptitle("Numeric Column Distributions", fontsize=14, fontweight="bold", y=1.01)
    plt.tight_layout()
    return fig


def dataset_profiling_section(df: pd.DataFrame) -> None:
    """Streamlit UI section — only called from main_app.py."""
    if not HAS_STREAMLIT or st is None:
        return

    st.title("📊 Smart Dataset Profiling")
    st.markdown(
        "Full structural and statistical profile of your uploaded dataset — "
        "including missing value analysis and visual insights."
    )
    st.divider()

    # ── Overview ──────────────────────────────────────────────────────────────
    summary = generate_profiling_summary(df)
    ov = summary["overview"]

    st.subheader("📋 Dataset Overview")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Rows",       f"{ov['rows']:,}")
    c2.metric("Total Columns",    ov["columns"])
    c3.metric("Completeness",     f"{ov['completeness']}%")
    c4.metric("Duplicate Rows",   ov["duplicate_rows"])
    c5.metric("Numeric Columns",  ov["numeric_cols"])
    st.divider()

    # ── Preview ───────────────────────────────────────────────────────────────
    with st.expander("🔍 Preview Dataset (first 10 rows)", expanded=True):
        st.dataframe(df.head(10), use_container_width=True)
    st.divider()

    # ── Profiling Table ───────────────────────────────────────────────────────
    st.subheader("📑 Column-Level Profiling Summary")
    profiling_df = generate_profiling_table(df)

    def _highlight_missing(val):
        try:
            pct = float(str(val).replace("%", ""))
            if pct > 30:
                return "background-color: #ffcccc"
            if pct > 10:
                return "background-color: #fff3cd"
            return ""
        except Exception:
            return ""

    styled = profiling_df.style.map(_highlight_missing, subset=["Missing %"])
    st.dataframe(styled, use_container_width=True, height=350)
    st.caption("🟥 >30% missing  |  🟨 10–30% missing  |  ⬜ <10% missing")
    st.divider()

    # ── Missing Value Visuals ─────────────────────────────────────────────────
    if ov["missing_cells"] > 0:
        st.subheader("🕳️ Missing Value Analysis")
        tab1, tab2 = st.tabs(["Heatmap", "Bar Chart"])
        with tab1:
            st.markdown("Each cell shows whether a value is **missing (dark)** or **present (light)**.")
            fig = _plot_missing_heatmap(df)
            if fig:
                st.pyplot(fig)
        with tab2:
            fig = _plot_missing_bar(df)
            if fig:
                st.pyplot(fig)
            else:
                st.success("🎉 No missing values found!")
        st.divider()

    # ── Numeric Distributions ─────────────────────────────────────────────────
    if ov["numeric_cols"] > 0:
        st.subheader("📈 Numeric Column Distributions")
        fig = _plot_numeric_distributions(df)
        if fig:
            st.pyplot(fig)
        st.divider()

    # ── Descriptive Statistics ────────────────────────────────────────────────
    st.subheader("🔢 Descriptive Statistics")
    num_cols = df.select_dtypes(include="number").columns.tolist()
    if num_cols:
        st.dataframe(df[num_cols].describe().T.round(4), use_container_width=True)
    else:
        st.info("No numeric columns found in this dataset.")
    st.divider()

    # ── Categorical Summary ───────────────────────────────────────────────────
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    if cat_cols:
        st.subheader("🏷️ Categorical Column Summary")
        cat_data = []
        for col in cat_cols:
            vc = df[col].value_counts()
            cat_data.append({
                "Column":        col,
                "Unique Values": df[col].nunique(),
                "Top Value":     str(vc.index[0]) if len(vc) else "N/A",
                "Top Count":     int(vc.iloc[0])  if len(vc) else 0,
                "Missing %":     f"{round(df[col].isna().mean() * 100, 2)}%",
            })
        st.dataframe(pd.DataFrame(cat_data), use_container_width=True)
        st.divider()

    # ── Download ──────────────────────────────────────────────────────────────
    st.subheader("⬇️ Download Profiling Report")
    buf = io.StringIO()
    generate_profiling_table(df).to_csv(buf, index=False)
    st.download_button(
        label="📥 Download Profiling Summary (CSV)",
        data=buf.getvalue(),
        file_name="profiling_report.csv",
        mime="text/csv",
    )
