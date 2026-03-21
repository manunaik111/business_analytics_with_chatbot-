# report_generator.py
# Team 5 — Integration & Interface
# Generates PDF and Excel reports from sales data

import io
import pandas as pd
from fpdf import FPDF
from datetime import datetime


# ── Excel Report ──────────────────────────────────────────────────────
def generate_excel_report(analyzer):
    df = analyzer.df

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:

        # Sheet 1 — KPI Summary
        total_sales   = df['Sales'].sum()
        total_profit  = df['Profit'].sum()
        total_orders  = len(df)
        avg_order     = df['Sales'].mean()
        profit_margin = (total_profit / total_sales * 100) if total_sales else 0

        kpi_data = pd.DataFrame({
            'Metric': [
                'Total Sales',
                'Total Profit',
                'Total Orders',
                'Average Order Value',
                'Profit Margin %'
            ],
            'Value': [
                f"${total_sales:,.2f}",
                f"${total_profit:,.2f}",
                f"{total_orders:,}",
                f"${avg_order:,.2f}",
                f"{profit_margin:.1f}%"
            ]
        })
        kpi_data.to_excel(writer, sheet_name='KPI Summary', index=False)

        # Sheet 2 — Sales by Region
        region_df = df.groupby('Region').agg(
            Total_Sales=('Sales', 'sum'),
            Total_Profit=('Profit', 'sum'),
            Total_Orders=('Order ID', 'count')
        ).reset_index().sort_values('Total_Sales', ascending=False)
        region_df['Total_Sales']  = region_df['Total_Sales'].round(2)
        region_df['Total_Profit'] = region_df['Total_Profit'].round(2)
        region_df.to_excel(writer, sheet_name='Sales by Region', index=False)

        # Sheet 3 — Sales by Category
        cat_df = df.groupby('Category').agg(
            Total_Sales=('Sales', 'sum'),
            Total_Profit=('Profit', 'sum'),
            Total_Orders=('Order ID', 'count')
        ).reset_index().sort_values('Total_Sales', ascending=False)
        cat_df['Total_Sales']  = cat_df['Total_Sales'].round(2)
        cat_df['Total_Profit'] = cat_df['Total_Profit'].round(2)
        cat_df.to_excel(writer, sheet_name='Sales by Category', index=False)

        # Sheet 4 — Top 20 Products
        product_df = df.groupby('Product Name').agg(
            Total_Sales=('Sales', 'sum'),
            Total_Profit=('Profit', 'sum'),
            Total_Orders=('Order ID', 'count')
        ).reset_index().sort_values('Total_Sales', ascending=False).head(20)
        product_df['Total_Sales']  = product_df['Total_Sales'].round(2)
        product_df['Total_Profit'] = product_df['Total_Profit'].round(2)
        product_df.to_excel(writer, sheet_name='Top Products', index=False)

        # Sheet 5 — Monthly Trend
        if 'Order Date' in df.columns:
            df['Month'] = df['Order Date'].dt.to_period('M').astype(str)
            monthly_df  = df.groupby('Month').agg(
                Total_Sales=('Sales', 'sum'),
                Total_Profit=('Profit', 'sum'),
                Total_Orders=('Order ID', 'count')
            ).reset_index()
            monthly_df['Total_Sales']  = monthly_df['Total_Sales'].round(2)
            monthly_df['Total_Profit'] = monthly_df['Total_Profit'].round(2)
            monthly_df.to_excel(writer, sheet_name='Monthly Trend', index=False)

        # Sheet 6 — Segment Analysis
        seg_df = df.groupby('Segment').agg(
            Total_Sales=('Sales', 'sum'),
            Total_Profit=('Profit', 'sum'),
            Total_Orders=('Order ID', 'count')
        ).reset_index().sort_values('Total_Sales', ascending=False)
        seg_df['Total_Sales']  = seg_df['Total_Sales'].round(2)
        seg_df['Total_Profit'] = seg_df['Total_Profit'].round(2)
        seg_df.to_excel(writer, sheet_name='Segment Analysis', index=False)

    output.seek(0)
    return output


# ── PDF Report ────────────────────────────────────────────────────────
class SalesPDF(FPDF):
    def header(self):
        self.set_fill_color(74, 35, 90)
        self.rect(0, 0, 210, 20, 'F')
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(255, 255, 255)
        self.cell(0, 20, 'AI Sales Analytics Dashboard - Report', align='C', ln=True)
        self.set_text_color(0, 0, 0)
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")}  |  Page {self.page_no()}', align='C')

    def section_title(self, title):
        self.set_fill_color(74, 35, 90)
        self.set_text_color(255, 255, 255)
        self.set_font('Helvetica', 'B', 11)
        self.cell(0, 9, f'  {title}', ln=True, fill=True)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def kpi_row(self, label, value):
        self.set_font('Helvetica', 'B', 10)
        self.set_fill_color(240, 230, 255)
        self.cell(90, 8, f'  {label}', border=1, fill=True)
        self.set_font('Helvetica', '', 10)
        self.set_fill_color(255, 255, 255)
        self.cell(90, 8, f'  {value}', border=1, fill=True, ln=True)

    def table_header(self, cols, widths):
        self.set_fill_color(74, 35, 90)
        self.set_text_color(255, 255, 255)
        self.set_font('Helvetica', 'B', 9)
        for col, w in zip(cols, widths):
            self.cell(w, 8, f' {col}', border=1, fill=True)
        self.ln()
        self.set_text_color(0, 0, 0)

    def table_row(self, values, widths, fill=False):
        self.set_font('Helvetica', '', 9)
        self.set_fill_color(248, 240, 255)
        for val, w in zip(values, widths):
            self.cell(w, 7, f' {str(val)}', border=1, fill=fill)
        self.ln()


def generate_pdf_report(analyzer):
    df = analyzer.df

    pdf = SalesPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # ── KPI Section ───────────────────────────────────────────────────
    total_sales   = df['Sales'].sum()
    total_profit  = df['Profit'].sum()
    total_orders  = len(df)
    avg_order     = df['Sales'].mean()
    profit_margin = (total_profit / total_sales * 100) if total_sales else 0

    pdf.section_title("Key Performance Indicators")
    pdf.kpi_row("Total Sales",          f"${total_sales:,.2f}")
    pdf.kpi_row("Total Profit",         f"${total_profit:,.2f}")
    pdf.kpi_row("Total Orders",         f"{total_orders:,}")
    pdf.kpi_row("Average Order Value",  f"${avg_order:,.2f}")
    pdf.kpi_row("Overall Profit Margin", f"{profit_margin:.1f}%")
    pdf.ln(6)

    # ── Sales by Region ───────────────────────────────────────────────
    pdf.section_title("Sales by Region")
    region_df = df.groupby('Region').agg(
        Sales=('Sales', 'sum'),
        Profit=('Profit', 'sum'),
        Orders=('Order ID', 'count')
    ).reset_index().sort_values('Sales', ascending=False)

    pdf.table_header(
        ['Region', 'Total Sales', 'Total Profit', 'Orders'],
        [45, 50, 50, 35]
    )
    for i, row in region_df.iterrows():
        pdf.table_row(
            [row['Region'], f"${row['Sales']:,.0f}",
             f"${row['Profit']:,.0f}", f"{row['Orders']:,}"],
            [45, 50, 50, 35],
            fill=(i % 2 == 0)
        )
    pdf.ln(6)

    # ── Sales by Category ─────────────────────────────────────────────
    pdf.section_title("Sales by Category")
    cat_df = df.groupby('Category').agg(
        Sales=('Sales', 'sum'),
        Profit=('Profit', 'sum'),
        Orders=('Order ID', 'count')
    ).reset_index().sort_values('Sales', ascending=False)

    pdf.table_header(
        ['Category', 'Total Sales', 'Total Profit', 'Orders'],
        [55, 45, 45, 35]
    )
    for i, row in cat_df.iterrows():
        pdf.table_row(
            [row['Category'], f"${row['Sales']:,.0f}",
             f"${row['Profit']:,.0f}", f"{row['Orders']:,}"],
            [55, 45, 45, 35],
            fill=(i % 2 == 0)
        )
    pdf.ln(6)

    # ── Top 10 Products ───────────────────────────────────────────────
    pdf.section_title("Top 10 Products by Sales")
    product_df = df.groupby('Product Name').agg(
        Sales=('Sales', 'sum'),
        Profit=('Profit', 'sum')
    ).reset_index().sort_values('Sales', ascending=False).head(10)

    pdf.table_header(
        ['Product Name', 'Total Sales', 'Total Profit'],
        [110, 40, 40]
    )
    for i, row in product_df.iterrows():
        name = row['Product Name'][:45] + '...' if len(row['Product Name']) > 45 else row['Product Name']
        pdf.table_row(
            [name, f"${row['Sales']:,.0f}", f"${row['Profit']:,.0f}"],
            [110, 40, 40],
            fill=(i % 2 == 0)
        )
    pdf.ln(6)

    # ── Monthly Trend ─────────────────────────────────────────────────
    if 'Order Date' in df.columns:
        pdf.section_title("Monthly Sales Trend")
        df['Month'] = df['Order Date'].dt.to_period('M').astype(str)
        monthly_df  = df.groupby('Month').agg(
            Sales=('Sales', 'sum'),
            Orders=('Order ID', 'count')
        ).reset_index().tail(12)

        pdf.table_header(
            ['Month', 'Total Sales', 'Orders'],
            [60, 60, 60]
        )
        for i, row in monthly_df.iterrows():
            pdf.table_row(
                [row['Month'], f"${row['Sales']:,.0f}", f"{row['Orders']:,}"],
                [60, 60, 60],
                fill=(i % 2 == 0)
            )

    output = io.BytesIO()
    pdf_bytes = pdf.output()
    output.write(pdf_bytes)
    output.seek(0)
    return output