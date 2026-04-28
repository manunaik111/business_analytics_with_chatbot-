"""insights.py — AI insights via Groq + rule-based fallback."""
import os
import streamlit as st
import pandas as pd

def _rule_based(df, stats, correlations):
    lines = []
    num_cols = df.select_dtypes(include="number").columns.tolist()

    lines.append(f"Dataset contains **{len(df):,}** records across **{len(df.columns)}** columns.")

    if correlations:
        top = correlations[0]
        dir_word = "positive" if top["score"] > 0 else "negative"
        lines.append(
            f"Strong {dir_word} correlation (r={top['score']:.2f}) between "
            f"`{top['col1']}` and `{top['col2']}` — fluctuations in one predict the other."
        )

    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    if cat_cols:
        col = cat_cols[0]
        try:
            top_val = df[col].mode().iloc[0]
            lines.append(
                f"Dominant segment in `{col}` is **'{top_val}'** — the primary operational baseline."
            )
        except Exception:
            pass

    if num_cols:
        col = num_cols[0]
        mean_val = df[col].mean()
        lines.append(
            f"Average baseline for `{col}` is **{mean_val:,.2f}**. "
            "Sharp deviations should trigger review workflows."
        )

    missing = int(df.isnull().sum().sum())
    if missing > 0:
        lines.append(f"**{missing:,}** missing values were auto-imputed during cleaning.")

    return "\n\n".join(f"- {l}" for l in lines)

@st.cache_data(show_spinner=False)
def generate_insights(df, stats, correlations):
    if df is None or df.empty:
        return "No data available."

    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key or api_key == "your_key_here":
        return _rule_based(df, stats, correlations)

    try:
        from groq import Groq
        client = Groq(api_key=api_key)

        num_cols = list(df.select_dtypes("number").columns)
        cat_cols = list(df.select_dtypes(["object", "category"]).columns)

        stats_str = stats.to_csv() if stats is not None and not stats.empty else "N/A"
        import json
        corr_str  = json.dumps(correlations[:5]) if correlations else "None"

        prompt = (
            f"Analyze this dataset: {len(df)} rows, {len(df.columns)} cols, "
            f"numeric: {num_cols[:6]}, categorical: {cat_cols[:4]}, "
            f"stats: {stats_str[:800]}, correlations: {corr_str}. "
            "Give 3-5 bullet-point insights. Infer business/real-world meaning, not just numbers. Use Markdown."
        )

        resp = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
        )
        return resp.choices[0].message.content

    except Exception as e:
        print(f"Groq insights failed: {e}")
        return _rule_based(df, stats, correlations)

@st.cache_data(show_spinner=False)
def generate_full_report(df_shape, stats_str, cleaning_report_str, correlations_str, kpis_str, ml_results_str):
    """Generate a 10-section executive report via Groq llama-3.3-70b."""
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key or api_key == "your_key_here":
        return "⚠️ Add GROQ_API_KEY to .env to generate the full report."

    try:
        from groq import Groq
        client = Groq(api_key=api_key)

        system = (
            "You are an Expert Data Scientist. Write a professional Executive Data Report with these sections:\n"
            "## 2. Data Overview\n## 3. Data Preparation\n## 4. EDA\n## 5. Key Insights\n"
            "## 6. KPI Metrics\n## 7. ML Insights\n## 8. Dashboard Summary\n"
            "## 9. Business Recommendations\n## 10. Conclusion\n"
            "Use Markdown. Be specific, professional, actionable. Start with '## 2. Data Overview'."
        )
        context = (
            f"Shape: {df_shape}\nStats: {stats_str}\nCleaning: {cleaning_report_str}\n"
            f"Correlations: {correlations_str}\nKPIs: {kpis_str}\nML: {ml_results_str}"
        )
        resp = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": context},
            ],
            model="llama-3.3-70b-versatile",
        )
        return (
            "# 1. Executive Summary\n\n"
            "This automated report details the structural properties, "
            "statistical derivations, and actionable business intelligence "
            "extracted from the provided dataset.\n\n"
            + resp.choices[0].message.content
        )
    except Exception as e:
        return f"⚠️ Report generation error: {e}"
