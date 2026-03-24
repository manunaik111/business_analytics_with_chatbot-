# report_generator.py
# Team 5 — Integration & Interface
# Generates PDF and Excel reports from sales data

import io
import pandas as pd
from fpdf import FPDF
from datetime import datetime


# ── Colour palette ─────────────────────────────────────────────────────────────
PURPLE      = (74,  35,  90)
PURPLE_MID  = (125, 60, 152)
PURPLE_PALE = (245, 238, 252)
PURPLE_ROW  = (235, 213, 245)
WHITE       = (255, 255, 255)
BLACK       = (30,  30,  30)
GREY_LIGHT  = (248, 248, 248)
GREY_LINE   = (200, 200, 200)
GREY_TEXT   = (100, 100, 100)


# ══════════════════════════════════════════════════════════════════════════════
# Excel Report  (unchanged from original)
# ══════════════════════════════════════════════════════════════════════════════
def generate_excel_report(analyzer):
    df = analyzer.df
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:

        total_sales   = df['Sales'].sum()
        total_profit  = df['Profit'].sum()
        total_orders  = len(df)
        avg_order     = df['Sales'].mean()
        profit_margin = (total_profit / total_sales * 100) if total_sales else 0

        kpi_data = pd.DataFrame({
            'Metric': ['Total Sales', 'Total Profit', 'Total Orders',
                       'Average Order Value', 'Profit Margin %'],
            'Value':  [f"${total_sales:,.2f}", f"${total_profit:,.2f}",
                       f"{total_orders:,}",    f"${avg_order:,.2f}",
                       f"{profit_margin:.1f}%"]
        })
        kpi_data.to_excel(writer, sheet_name='KPI Summary', index=False)

        region_df = df.groupby('Region').agg(
            Total_Sales=('Sales', 'sum'), Total_Profit=('Profit', 'sum'),
            Total_Orders=('Order ID', 'count')
        ).reset_index().sort_values('Total_Sales', ascending=False)
        region_df[['Total_Sales', 'Total_Profit']] = region_df[['Total_Sales', 'Total_Profit']].round(2)
        region_df.to_excel(writer, sheet_name='Sales by Region', index=False)

        cat_df = df.groupby('Category').agg(
            Total_Sales=('Sales', 'sum'), Total_Profit=('Profit', 'sum'),
            Total_Orders=('Order ID', 'count')
        ).reset_index().sort_values('Total_Sales', ascending=False)
        cat_df[['Total_Sales', 'Total_Profit']] = cat_df[['Total_Sales', 'Total_Profit']].round(2)
        cat_df.to_excel(writer, sheet_name='Sales by Category', index=False)

        product_df = df.groupby('Product Name').agg(
            Total_Sales=('Sales', 'sum'), Total_Profit=('Profit', 'sum'),
            Total_Orders=('Order ID', 'count')
        ).reset_index().sort_values('Total_Sales', ascending=False).head(20)
        product_df[['Total_Sales', 'Total_Profit']] = product_df[['Total_Sales', 'Total_Profit']].round(2)
        product_df.to_excel(writer, sheet_name='Top Products', index=False)

        if 'Order Date' in df.columns:
            df['Month'] = df['Order Date'].dt.to_period('M').astype(str)
            monthly_df = df.groupby('Month').agg(
                Total_Sales=('Sales', 'sum'), Total_Profit=('Profit', 'sum'),
                Total_Orders=('Order ID', 'count')
            ).reset_index()
            monthly_df[['Total_Sales', 'Total_Profit']] = monthly_df[['Total_Sales', 'Total_Profit']].round(2)
            monthly_df.to_excel(writer, sheet_name='Monthly Trend', index=False)

        seg_df = df.groupby('Segment').agg(
            Total_Sales=('Sales', 'sum'), Total_Profit=('Profit', 'sum'),
            Total_Orders=('Order ID', 'count')
        ).reset_index().sort_values('Total_Sales', ascending=False)
        seg_df[['Total_Sales', 'Total_Profit']] = seg_df[['Total_Sales', 'Total_Profit']].round(2)
        seg_df.to_excel(writer, sheet_name='Segment Analysis', index=False)

    output.seek(0)
    return output


# ══════════════════════════════════════════════════════════════════════════════
# PDF Report
# ══════════════════════════════════════════════════════════════════════════════
class SalesPDF(FPDF):

    def header(self):
        self.set_fill_color(*PURPLE)
        self.rect(0, 0, 210, 20, 'F')
        self.set_font('Helvetica', 'B', 15)
        self.set_text_color(*WHITE)
        self.set_xy(0, 4)
        self.cell(210, 8, 'AI Sales Analytics Dashboard', align='C')
        self.set_font('Helvetica', '', 8)
        self.set_text_color(210, 180, 230)
        self.set_xy(0, 12)
        self.cell(210, 5, 'Sales Performance Report', align='C')
        self.set_draw_color(*PURPLE_MID)
        self.set_line_width(0.6)
        self.line(10, 21, 200, 21)
        self.set_text_color(*BLACK)
        self.ln(6)

    def footer(self):
        self.set_y(-14)
        self.set_fill_color(*PURPLE)
        self.rect(0, self.get_y(), 210, 14, 'F')
        self.set_font('Helvetica', 'I', 7.5)
        self.set_text_color(210, 180, 230)
        ts = datetime.now().strftime('%Y-%m-%d %H:%M')
        self.cell(95, 14, f'  Generated on {ts}', align='L')
        self.cell(105, 14, f'Page {self.page_no()}  ', align='R')

    def section_title(self, title):
        self.set_fill_color(*PURPLE)
        self.set_text_color(*WHITE)
        self.set_font('Helvetica', 'B', 10)
        self.set_draw_color(*PURPLE)
        self.cell(0, 9, f'   {title}', ln=True, fill=True)
        self.set_text_color(*BLACK)
        self.ln(2)

    def kpi_grid(self, kpis):
        card_w  = 90
        card_h  = 16
        gap     = 5
        start_x = self.get_x()

        for idx, (label, value) in enumerate(kpis):
            col = idx % 2
            x   = start_x + col * (card_w + gap)
            y   = self.get_y()

            self.set_fill_color(*PURPLE_PALE)
            self.set_draw_color(*PURPLE_MID)
            self.set_line_width(0.3)
            self.rect(x, y, card_w, card_h, 'FD')

            self.set_fill_color(*PURPLE_MID)
            self.rect(x, y, 3, card_h, 'F')

            self.set_xy(x + 6, y + 2)
            self.set_font('Helvetica', '', 7.5)
            self.set_text_color(*GREY_TEXT)
            self.cell(card_w - 6, 5, label)

            self.set_xy(x + 6, y + 7)
            self.set_font('Helvetica', 'B', 11)
            self.set_text_color(*PURPLE)
            self.cell(card_w - 6, 7, value)

            if col == 1 or idx == len(kpis) - 1:
                self.set_xy(start_x, y + card_h + 3)

        self.set_text_color(*BLACK)
        self.ln(4)

    def table_header(self, cols, widths):
        self.set_fill_color(*PURPLE)
        self.set_text_color(*WHITE)
        self.set_font('Helvetica', 'B', 8.5)
        self.set_draw_color(*GREY_LINE)
        self.set_line_width(0.25)
        for col, w in zip(cols, widths):
            self.cell(w, 9, f'  {col}', border=1, fill=True)
        self.ln()
        self.set_text_color(*BLACK)

    def table_row(self, values, widths, even=True):
        self.set_font('Helvetica', '', 8.5)
        self.set_fill_color(*(PURPLE_ROW if even else GREY_LIGHT))
        self.set_draw_color(*GREY_LINE)
        self.set_line_width(0.2)
        for val, w in zip(values, widths):
            self.cell(w, 8, f'  {str(val)}', border=1, fill=True)
        self.ln()


# ── Generator ──────────────────────────────────────────────────────────────────
def generate_pdf_report(analyzer):
    df = analyzer.df

    pdf = SalesPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # KPIs
    total_sales   = df['Sales'].sum()
    total_profit  = df['Profit'].sum()
    total_orders  = len(df)
    avg_order     = df['Sales'].mean()
    profit_margin = (total_profit / total_sales * 100) if total_sales else 0

    pdf.section_title('Key Performance Indicators')
    pdf.kpi_grid([
        ('Total Sales',           f'${total_sales:,.2f}'),
        ('Total Profit',          f'${total_profit:,.2f}'),
        ('Total Orders',          f'{total_orders:,}'),
        ('Average Order Value',   f'${avg_order:,.2f}'),
        ('Overall Profit Margin', f'{profit_margin:.1f}%'),
    ])

    # Sales by Region
    pdf.section_title('Sales by Region')
    region_df = df.groupby('Region').agg(
        Sales=('Sales', 'sum'), Profit=('Profit', 'sum'),
        Orders=('Order ID', 'count')
    ).reset_index().sort_values('Sales', ascending=False)
    pdf.table_header(['Region', 'Total Sales', 'Total Profit', 'Orders'], [50, 50, 50, 35])
    for i, row in enumerate(region_df.itertuples()):
        pdf.table_row([row.Region, f'${row.Sales:,.0f}', f'${row.Profit:,.0f}', f'{row.Orders:,}'],
                      [50, 50, 50, 35], even=(i % 2 == 0))
    pdf.ln(5)

    # Sales by Category
    pdf.section_title('Sales by Category')
    cat_df = df.groupby('Category').agg(
        Sales=('Sales', 'sum'), Profit=('Profit', 'sum'),
        Orders=('Order ID', 'count')
    ).reset_index().sort_values('Sales', ascending=False)
    pdf.table_header(['Category', 'Total Sales', 'Total Profit', 'Orders'], [55, 48, 48, 34])
    for i, row in enumerate(cat_df.itertuples()):
        pdf.table_row([row.Category, f'${row.Sales:,.0f}', f'${row.Profit:,.0f}', f'{row.Orders:,}'],
                      [55, 48, 48, 34], even=(i % 2 == 0))
    pdf.ln(5)

    # Top 10 Products
    pdf.section_title('Top 10 Products by Sales')
    product_df = df.groupby('Product Name').agg(
        Sales=('Sales', 'sum'), Profit=('Profit', 'sum')
    ).reset_index().sort_values('Sales', ascending=False).head(10)
    pdf.table_header(['Product Name', 'Total Sales', 'Total Profit'], [115, 38, 37])
    for i, (_, row) in enumerate(product_df.iterrows()):
        name = str(row['Product Name'])
        name = (name[:52] + '...') if len(name) > 52 else name
        pdf.table_row([name, f"${row['Sales']:,.0f}", f"${row['Profit']:,.0f}"],
                      [115, 38, 37], even=(i % 2 == 0))
    pdf.ln(5)

    # Monthly Sales Trend
    if 'Order Date' in df.columns:
        pdf.section_title('Monthly Sales Trend')
        df = df.copy()
        df['Month'] = df['Order Date'].dt.to_period('M').astype(str)
        monthly_df = df.groupby('Month').agg(
            Sales=('Sales', 'sum'), Orders=('Order ID', 'count')
        ).reset_index().tail(12)
        pdf.table_header(['Month', 'Total Sales', 'Orders'], [62, 62, 61])
        for i, row in enumerate(monthly_df.itertuples()):
            pdf.table_row([row.Month, f'${row.Sales:,.0f}', f'{row.Orders:,}'],
                          [62, 62, 61], even=(i % 2 == 0))

    output = io.BytesIO()
    pdf.output(output)
    output.seek(0)
    return output
