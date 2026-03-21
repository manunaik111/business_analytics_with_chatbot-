import plotly.express as px
import streamlit as st
import pandas as pd

def create_profit_subcategory_chart(df):
    data = df.groupby("Sub-Category")["Profit"].sum().reset_index()
    fig = px.bar(
        data,
        x="Profit",
        y="Sub-Category",
        orientation="h",
        title="Profit by Sub-Category",
        color="Profit",
        color_discrete_sequence='viridis'
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#3E2C23", size=11),
        title=dict(text="Profit by Sub-Category", x=0.5, y=0.95, xanchor='center',yanchor='top'),  # center title
        height=250,
        margin=dict(l=10, r=10, t=30, b=20),
        # 2. Tighten the color bar (Legend)
        coloraxis_colorbar=dict(
            thicknessmode="pixels", thickness=15, # Slimmer bar
            lenmode="fraction", len=0.6,          # Shorter bar
            yanchor="middle", y=0.5,
            xpad=10,                              # Pulls it closer to the chart
            title=None                            # Remove "Profit" title to save space
        )
    )
    
    # 3. Make the bars thicker so they don't look spindly
    fig.update_traces(marker_line_width=0, selector=dict(type='bar'))
    st.plotly_chart(fig, use_container_width=True)


def create_sales_category_chart(df):
    data = df.groupby("Category")["Sales"].sum().reset_index()
    fig = px.pie(
        data,
        names="Category",
        values="Sales",
        title="Sales by Category",
        color="Category",
        color_discrete_sequence=["#6B8E23","#D4A017","#8DA84A"]
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#3E2C23", size=11),
        title=dict(text="Sales by Category", x=0.5, y=0.95, xanchor='center', yanchor='top'),
        margin=dict(l=10, r=10, t=50, b=10),
        height=250,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=0.85  # Brings the legend closer to the pie
        )
    )
    
    # 4. Display percentage labels inside for a cleaner look
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)


def create_sales_region_chart(df):
    data = df.groupby("Region")["Sales"].sum().reset_index()
    fig = px.bar(
        data,
        x="Region",
        y="Sales",
        title="Sales by Region",
        color="Region",
        color_discrete_sequence=["#8DA84A", "#6B8E23", "#D4A017", "#B8860B", "#556B2F"]
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#3E2C23", size=11),
        title=dict(text="Sales by Region", x=0.5, y=0.95, xanchor='center',yanchor='top'),
        margin=dict(l=10, r=10, t=50, b=10),
        height=250,
        showlegend=False,
        xaxis=dict(showgrid=False, tickfont=dict(size=10)),
        yaxis=dict(gridcolor="#E0E0E0", tickfont=dict(size=10))
    )
    
    fig.update_traces(marker_line_width=0, selector=dict(type='bar'))
    st.plotly_chart(fig, use_container_width=True)

def display_top_products(df):
    data = df.groupby("Product Name")["Sales"].sum().nlargest(5).reset_index()
    fig = px.bar(
        data,
        x="Sales",
        y="Product Name",
        orientation="h",
        title="Top 5 Products by Sales",
        color="Sales", 
        color_continuous_scale='sunsetdark'
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#3E2C23", size=11),
        title=dict(text="Top 5 Products by Sales", x=0.5, y=0.92),
       margin=dict(l=10, r=10, t=50, b=10),
        height=250,
        
        # 3. Clean up axes (Removing titles saves a lot of space)
        xaxis=dict(showgrid=False, tickfont=dict(size=10)),
        yaxis=dict(tickfont=dict(size=10)),
        
        # 4. Compact Color Bar
        coloraxis_colorbar=dict(
            thickness=12,
            len=0.7,
            yanchor="middle", y=0.5,
            xpad=5,
            title=None
        )
    )

    # Make bars thicker
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(fig, use_container_width=True)


def create_profit_vs_sales_scatter(df):
    fig = px.scatter(
        df,
        x="Sales",
        y="Profit",
        color="Category",
        title="Profit vs Sales Relationship",
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#3E2C23", size=11),
        title=dict(text="Profit vs Sales Relationship", x=0.5, y=0.95,xanchor='center', yanchor='top'),
        height=250,
        # 2. Tighten margins (t=30 removes that gap)
        margin=dict(l=10, r=10, t=30, b=10),
        
        # 3. Remove axis titles for a minimal, compact look
        xaxis=dict(showgrid=False, tickfont=dict(size=10)),
        yaxis=dict( gridcolor="#E0E0E0", tickfont=dict(size=10))
    )

    # 4. Make the line slightly thicker for a premium feel
    fig.update_traces(line=dict(width=3))
        
    st.plotly_chart(fig, use_container_width=True)


def create_monthly_trend_chart(df):
    df["Order Date"] = pd.to_datetime(df["Order Date"], dayfirst=True)
    df["Month"] = df["Order Date"].dt.to_period("M").astype(str)
    data = df.groupby("Month")["Sales"].sum().reset_index()
    fig = px.line(
        data,
        x="Month",
        y="Sales",
        title="Monthly Sales Trend",
        markers=True, line_shape="linear", 
        color_discrete_sequence=["#6B8E23"] # minimal blue
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#3E2C23", size=11),
        title=dict(text="Monthly Sales Trend", x=0.5, y=0.95, xanchor='center', yanchor='top'),
        height=250,
        # 2. Tighten all margins (t=30 removes that top gap)
        margin=dict(l=10, r=10, t=30, b=10),
        
        # 3. Remove axis titles for a cleaner look
        xaxis=dict(gridcolor="#E0E0E0", tickfont=dict(size=10)),
        yaxis=dict(gridcolor="#E0E0E0", tickfont=dict(size=10)),
        
        # 4. Pull the legend closer to the chart
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02, # Pulls it just outside the plot area
            font=dict(size=10),
            title=None # Removes "Category" title to save space
        )
    )

    # 5. Make the dots slightly smaller or more transparent if crowded
    fig.update_traces(marker=dict(size=6, opacity=0.8, line=dict(width=0)))
  
    st.plotly_chart(fig, use_container_width=True)


def create_shipping_delay_chart(df):
    data = df.groupby("Ship Mode")["Shipping Delay"].mean().reset_index()
    ship_colors = px.colors.sequential.Greens # shades of blue
    fig = px.bar(
        data,
        x="Ship Mode",
        y="Shipping Delay",
        title="Average Shipping Delay by Ship Mode",
        color="Ship Mode", 
        color_discrete_sequence=ship_colors
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#3E2C23", size=11),
        title=dict(text="Average Shipping Delay by Ship Mode", x=0.5, y=0.95, xanchor='center',yanchor='top'),
        height=250,
      # 2. Tighten margins (t=30 removes the gap under title)
        margin=dict(l=10, r=10, t=30, b=10),
        
        # 3. Clean up axes
        xaxis=dict(tickangle=0, tickfont=dict(size=10)),
        yaxis=dict(gridcolor="#E0E0E0",tickfont=dict(size=10)),
        
        # 4. Pull legend closer
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02,
            title=None
        )
    )

    # 5. Make bars slightly wider to fill the space
    fig.update_traces(marker_line_width=0, width=0.6)
    
    st.plotly_chart(fig, use_container_width=True)




    
