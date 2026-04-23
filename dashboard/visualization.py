"""visualization.py — Auto chart generation + specific chart builders."""
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dashboard import utils

@st.cache_data(show_spinner=False)
def auto_charts(df: pd.DataFrame, column_types: dict) -> list:
    charts = []
    if df is None or df.empty:
        return charts

    raw_num  = column_types.get("numeric", [])
    num_cols = [c for c in raw_num if not any(k in c.lower() for k in ["id", "index", "code"])]
    cat_cols = column_types.get("categorical", [])
    date_cols = column_types.get("datetime", [])
    plot_df   = df.sample(n=min(1000, len(df)), random_state=42).copy()

    # Trend line
    if date_cols and num_cols:
        try:
            dc, vc = date_cols[0], num_cols[0]
            agg = plot_df.dropna(subset=[dc, vc]).groupby(dc)[vc].mean().reset_index().sort_values(dc)
            fig = px.line(agg, x=dc, y=vc, title=f"Trend: {vc}",
                          color_discrete_sequence=["#a78bfa"])
            fig.update_traces(fill="tozeroy", fillcolor="rgba(167,139,250,0.08)")
            charts.append(("Trend Line", utils.apply_genesis_theme(fig)))
        except Exception:
            pass

    # Bar: cat vs num
    if cat_cols and num_cols:
        try:
            cc, nc = cat_cols[0], num_cols[0]
            if plot_df[cc].nunique() <= 20:
                bar_df = plot_df.groupby(cc)[nc].mean().reset_index().sort_values(nc, ascending=False).head(10)
                fig = px.bar(bar_df, x=cc, y=nc, title=f"Avg {nc} by {cc}",
                             color=nc, color_continuous_scale="Purples")
                fig.update_layout(coloraxis_showscale=False)
                charts.append(("Bar Chart", utils.apply_genesis_theme(fig)))
        except Exception:
            pass

    # Donut
    if cat_cols:
        try:
            pie_col = next((c for c in cat_cols if 1 < plot_df[c].nunique() <= 10), None)
            if pie_col:
                pie_df = plot_df[pie_col].value_counts().reset_index()
                pie_df.columns = [pie_col, "count"]
                fig = px.pie(pie_df, names=pie_col, values="count",
                             title=f"Share: {pie_col}", hole=0.55,
                             color_discrete_sequence=utils.COLORS)
                fig.update_traces(textposition="inside", textinfo="percent+label", textfont_size=9)
                fig.update_layout(showlegend=False)
                charts.append(("Donut", utils.apply_genesis_theme(fig)))
        except Exception:
            pass

    # Correlation heatmap
    if len(num_cols) >= 3:
        try:
            corr_df = plot_df[num_cols[:8]].corr()
            fig = px.imshow(corr_df, text_auto=".2f", title="Correlation Matrix",
                            color_continuous_scale="Purples", zmin=-1, zmax=1)
            charts.append(("Heatmap", utils.apply_genesis_theme(fig)))
        except Exception:
            pass

    # Scatter
    if len(num_cols) >= 2:
        try:
            fig = px.scatter(plot_df, x=num_cols[1], y=num_cols[0], trendline="ols",
                             title=f"{num_cols[1]} vs {num_cols[0]}",
                             color_discrete_sequence=["#38bdf8"])
            charts.append(("Scatter", utils.apply_genesis_theme(fig)))
        except Exception:
            pass

    return charts[:10]

def create_yoy_area_chart(df: pd.DataFrame) -> go.Figure:
    date_cols = df.select_dtypes(include=["datetime64", "datetimetz"]).columns
    num_cols  = df.select_dtypes("number").columns

    if not list(date_cols) or not list(num_cols):
        months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        np.random.seed(42)
        yoy = pd.DataFrame({
            "Month": months * 3,
            "Year":  ["2022"]*12 + ["2023"]*12 + ["2024"]*12,
            "Value": list(np.random.randint(100, 300, 12)) +
                     list(np.random.randint(150, 350, 12)) +
                     list(np.random.randint(200, 450, 12)),
        })
        x_col, y_col, g_col = "Month", "Value", "Year"
    else:
        dc, vc = date_cols[0], num_cols[0]
        tmp = df.copy()
        tmp["Year"]  = tmp[dc].dt.year.astype(str)
        tmp["Month"] = tmp[dc].dt.strftime("%b")
        yoy = tmp.groupby(["Year", "Month"])[vc].sum().reset_index()
        mo_order = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        yoy["Month"] = pd.Categorical(yoy["Month"], categories=mo_order, ordered=True)
        yoy = yoy.sort_values("Month")
        x_col, y_col, g_col = "Month", vc, "Year"

    fig = px.area(yoy, x=x_col, y=y_col, color=g_col,
                  color_discrete_sequence=["#4ade80", "#38bdf8", "#a78bfa"],
                  title="Year-over-Year Comparison")
    fig.update_traces(line_width=2.5)
    return utils.apply_genesis_theme(fig)

def create_mom_grouped_bars(df: pd.DataFrame) -> go.Figure:
    date_cols = df.select_dtypes(include=["datetime64", "datetimetz"]).columns
    num_cols  = df.select_dtypes("number").columns

    if list(date_cols) and list(num_cols):
        try:
            dc, vc = date_cols[0], num_cols[0]
            tmp = df.copy()
            tmp["Year"]  = tmp[dc].dt.year
            tmp["Month"] = tmp[dc].dt.month
            last_yr = int(tmp["Year"].max())
            prev_yr = last_yr - 1
            last_data = tmp[tmp["Year"] == last_yr].groupby("Month")[vc].sum()
            prev_data = tmp[tmp["Year"] == prev_yr].groupby("Month")[vc].sum()
            months = sorted(set(last_data.index) | set(prev_data.index))[-6:]
            data = pd.DataFrame({
                "Month": months * 2,
                "Period": [str(last_yr)] * len(months) + [str(prev_yr)] * len(months),
                "Value":  [last_data.get(m, 0) for m in months] + [prev_data.get(m, 0) for m in months],
            })
        except Exception:
            data = pd.DataFrame({"Month": ["Oct","Nov","Dec"]*2,
                                  "Period": ["Current"]*3 + ["Previous"]*3,
                                  "Value":  [340, 320, 380, 295, 280, 332]})
    else:
        data = pd.DataFrame({"Month": ["Oct","Nov","Dec"]*2,
                              "Period": ["Current"]*3 + ["Previous"]*3,
                              "Value":  [340, 320, 380, 295, 280, 332]})

    fig = px.bar(data, x="Month", y="Value", color="Period", barmode="group",
                 color_discrete_sequence=["#a78bfa", "rgba(167,139,250,0.3)"],
                 title="Month-over-Month Comparison")
    return utils.apply_genesis_theme(fig)

def create_region_donut(df: pd.DataFrame) -> go.Figure:
    cat_cols   = df.select_dtypes(["object", "category"]).columns
    region_col = next((c for c in cat_cols if "region" in c.lower()), None)
    if region_col:
        counts = df[region_col].value_counts().reset_index()
        counts.columns = [region_col, "count"]
        names_col = region_col
    else:
        counts     = pd.DataFrame({"Region": ["North","South","East","West"], "count": [32,28,24,16]})
        names_col  = "Region"

    fig = px.pie(counts.head(8), names=names_col, values="count", hole=0.6,
                 color_discrete_sequence=["#a78bfa","#38bdf8","#4ade80","#fb923c"],
                 title="Sales by Region")
    fig.update_traces(textposition="inside", textinfo="percent+label", textfont_size=9)
    fig.update_layout(showlegend=False)
    return utils.apply_genesis_theme(fig)

def create_scatter_anomaly(df: pd.DataFrame) -> go.Figure:
    num_cols = df.select_dtypes("number").columns.tolist()
    if len(num_cols) >= 2:
        x_col, y_col = num_cols[1], num_cols[0]
        scat = df[[x_col, y_col]].dropna().sample(min(300, len(df)), random_state=42)
    else:
        np.random.seed(42)
        scat = pd.DataFrame({"Qty": np.random.randint(1,15,200), "Rev": np.random.randint(100,2000,200)})
        x_col, y_col = "Qty", "Rev"

    Q1, Q3  = scat[y_col].quantile(0.25), scat[y_col].quantile(0.75)
    scat["Type"] = np.where(scat[y_col] > Q3 + 1.5*(Q3-Q1), "Anomaly", "Normal")

    fig = px.scatter(scat, x=x_col, y=y_col, color="Type",
                     color_discrete_map={"Normal": "#a78bfa", "Anomaly": "#f87171"},
                     title=f"Anomaly Detection · {x_col} vs {y_col}")
    fig.update_traces(marker=dict(size=7, opacity=0.65))
    return utils.apply_genesis_theme(fig)

def create_profit_margin_bars(df: pd.DataFrame):
    """Returns list of (category, pct, color) for HTML progress bars."""
    cat_cols = df.select_dtypes(["object","category"]).columns.tolist()
    num_cols = df.select_dtypes("number").columns.tolist()
    sales_col  = next((c for c in num_cols if "sales" in c.lower() or "revenue" in c.lower()), None)
    profit_col = next((c for c in num_cols if "profit" in c.lower()), None)
    cat_col    = next((c for c in cat_cols if "categ" in c.lower() or "type" in c.lower()), None)

    if cat_col and sales_col and profit_col:
        try:
            mg = df.groupby(cat_col).apply(
                lambda x: (x[profit_col].sum() / x[sales_col].sum() * 100) if x[sales_col].sum() else 0
            ).reset_index()
            mg.columns = ["Category", "Margin"]
            mg = mg.sort_values("Margin", ascending=False).head(5)
            colors = ["#a78bfa","#38bdf8","#4ade80","#fb923c","#f472b6"]
            return [(str(row["Category"]), round(float(row["Margin"]),1), colors[i])
                    for i, (_, row) in enumerate(mg.iterrows())]
        except Exception:
            pass
    return [("Technology",85,"#a78bfa"),("Furniture",42,"#38bdf8"),
            ("Office Supplies",64,"#4ade80"),("Services",71,"#fb923c")]
