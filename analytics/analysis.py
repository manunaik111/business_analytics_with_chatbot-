"""
Retail Data Analysis System - Core Analysis Module
This module contains all analysis functions for the retail dataset.
"""

import pandas as pd
import numpy as np
from datetime import datetime

class RetailDataAnalyzer:
    """Main analyzer class for retail data analysis"""
    
    def __init__(self, filepath='SALES_DATA_SETT.csv'):
        """Initialize the analyzer with data file path"""
        self.filepath = filepath
        self.df = None
        self.required_columns = [
            'Row ID', 'Order ID', 'Order Date', 'Ship Date', 'Ship Mode',
            'Customer ID', 'Customer Name', 'Segment', 'Country', 'City',
            'State', 'Postal Code', 'Region', 'Product ID', 'Category',
            'Sub-Category', 'Product Name', 'Sales', 'Quantity', 'Discount',
            'Profit', 'shipping_delay_days', 'profit margin'
        ]
        
    def print_header(self, title, char="=", color=None):
        """Print a formatted header"""
        print("\n" + "★" * 80)
        print(f"  {title.upper()}")
        print("★" * 80)
    
    def print_subheader(self, title):
        """Print a formatted subheader"""
        print("\n" + "┌" + "─" * 78 + "┐")
        print(f"│ {title:<77}│")
        print("└" + "─" * 78 + "┘")
    
    def print_metric(self, label, value, unit="", width=30):
        """Print a formatted metric"""
        if unit == "$":
            print(f"  {label:<{width}} {unit}{value:>15,.2f}")
        elif unit == "%":
            print(f"  {label:<{width}} {value:>15,.2f}{unit}")
        else:
            print(f"  {label:<{width}} {value:>15}{unit}")
    
    def print_table(self, df, title=None):
        """Print a formatted table"""
        if title:
            print(f"\n  📊 {title}")
            print("  " + "─" * 60)
        
        # Convert DataFrame to string with formatting
        if isinstance(df, pd.Series):
            df = df.to_frame()
        
        # Format the table
        table_str = df.to_string(
            justify='right',
            float_format=lambda x: f"{x:,.2f}" if abs(x) > 0.01 else f"{x:.2f}"
        )
        
        # Indent each line
        for line in table_str.split('\n'):
            print(f"  {line}")
    
    def load_and_validate_data(self):
        """
        Load the dataset from CSV and validate all columns are present.
        Convert Order Date and Ship Date to datetime format.
        """
        self.print_header("STEP 1: LOADING AND VALIDATING DATA")
        
        try:
            # Load the dataset with proper encoding
            self.df = pd.read_csv(self.filepath, encoding='utf-8-sig')
            print(f"\n  ✅ Dataset loaded successfully from {self.filepath}")
            print(f"  📊 Dataset shape: {self.df.shape[0]:,} rows, {self.df.shape[1]} columns")
            
            # Display column names in a grid
            print("\n  📋 Column names in dataset:")
            cols_per_row = 4
            for i in range(0, len(self.df.columns), cols_per_row):
                row_cols = self.df.columns[i:i+cols_per_row]
                print("    ", end="")
                for col in row_cols:
                    print(f"• {col:<20}", end="")
                print()
            
            # Check for required columns
            missing_cols = []
            for req in self.required_columns:
                if req not in self.df.columns:
                    missing_cols.append(req)
            
            if missing_cols:
                print(f"\n  ⚠ Warning: Missing columns: {missing_cols}")
                print("  Attempting to proceed with available columns...")
            else:
                print("\n  ✅ All required columns present")
            
            # Convert dates to datetime
            date_formats = ['%d-%m-%Y', '%m-%d-%Y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']
            
            for date_col in ['Order Date', 'Ship Date']:
                if date_col in self.df.columns:
                    for fmt in date_formats:
                        try:
                            self.df[date_col] = pd.to_datetime(self.df[date_col], format=fmt, errors='coerce')
                            if self.df[date_col].notna().any():
                                print(f"  ✅ {date_col} converted using format {fmt}")
                                break
                        except:
                            continue
                    else:
                        self.df[date_col] = pd.to_datetime(self.df[date_col], errors='coerce')
                        print(f"  ✅ {date_col} converted with automatic format detection")
            
            return True
            
        except FileNotFoundError:
            print(f"\n  ❌ File {self.filepath} not found!")
            print("  Please ensure the file is in the current directory.")
            return False
        except Exception as e:
            print(f"\n  ❌ Error loading data: {str(e)}")
            return False
    
    def clean_data(self):
        """
        Clean the dataset by handling missing values,
        ensuring numeric columns are correctly formatted,
        and removing duplicates.
        """
        self.print_header("STEP 2: DATA CLEANING")
        
        # Check for missing values
        missing_before = self.df.isnull().sum().sum()
        if missing_before > 0:
            print(f"\n  Found {missing_before:,} missing values before cleaning")
            missing_cols = self.df.columns[self.df.isnull().any()].tolist()
            for col in missing_cols:
                missing_count = self.df[col].isnull().sum()
                print(f"    • {col}: {missing_count:,} missing values")
        
        # Handle missing values - drop rows with critical missing data
        critical_cols = ['Sales', 'Profit', 'Quantity', 'Customer ID', 'Order ID']
        existing_critical = [col for col in critical_cols if col in self.df.columns]
        
        if existing_critical:
            before_count = len(self.df)
            self.df.dropna(subset=existing_critical, inplace=True)
            after_count = len(self.df)
            if before_count > after_count:
                print(f"\n  ✅ Dropped {before_count - after_count} rows with missing critical data")
        
        # Ensure numeric columns are float
        numeric_cols = ['Sales', 'Quantity', 'Discount', 'Profit']
        if 'shipping_delay_days' in self.df.columns:
            numeric_cols.append('shipping_delay_days')
        
        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        
        # Remove duplicates
        before_dup = len(self.df)
        if 'Order ID' in self.df.columns and 'Product ID' in self.df.columns:
            self.df.drop_duplicates(subset=['Order ID', 'Product ID'], keep='first', inplace=True)
        elif 'Order ID' in self.df.columns:
            self.df.drop_duplicates(subset=['Order ID'], keep='first', inplace=True)
        else:
            self.df.drop_duplicates(inplace=True)
        
        after_dup = len(self.df)
        
        if before_dup > after_dup:
            print(f"  ✅ Removed {before_dup - after_dup:,} duplicate rows")
        
        missing_after = self.df.isnull().sum().sum()
        print(f"  ✅ Missing values after cleaning: {missing_after:,}")
        print(f"  ✅ Final dataset shape: {self.df.shape[0]:,} rows, {self.df.shape[1]} columns")
        
        return True
    
    def calculate_features(self):
        """
        Ensure shipping_delay_days and profit margin are present.
        Calculate them if missing.
        """
        self.print_header("STEP 3: FEATURE CALCULATION")
        
        # Calculate shipping delay if needed
        if 'shipping_delay_days' not in self.df.columns or self.df['shipping_delay_days'].isnull().all():
            if 'Ship Date' in self.df.columns and 'Order Date' in self.df.columns:
                print("\n  📦 Calculating shipping_delay_days from Ship Date - Order Date")
                self.df['shipping_delay_days'] = (self.df['Ship Date'] - self.df['Order Date']).dt.days
            else:
                print("\n  ⚠ Cannot calculate shipping_delay_days - missing date columns")
                self.df['shipping_delay_days'] = 0
        else:
            print("\n  ✅ shipping_delay_days already present")
        
        # Calculate profit margin if needed
        if 'profit margin' not in self.df.columns or self.df['profit margin'].isnull().all():
            print("  💰 Calculating profit margin from (Profit / Sales) * 100")
            # Handle division by zero
            self.df['profit margin'] = self.df.apply(
                lambda row: (row['Profit'] / row['Sales'] * 100) if row['Sales'] != 0 and pd.notna(row['Sales']) else 0, 
                axis=1
            )
            self.df['profit margin'] = self.df['profit margin'].round(2)
        else:
            # Convert percentage strings to float if needed
            if self.df['profit margin'].dtype == 'object':
                try:
                    self.df['profit margin'] = self.df['profit margin'].astype(str).str.replace('%', '').str.strip().astype(float)
                    print("  ✅ profit margin converted to numeric")
                except:
                    print("  ⚠ Could not convert profit margin to float, keeping as is")
            print("  ✅ profit margin already present")
        
        print("\n  ✅ Features ready for analysis")
        return True
    
    def calculate_kpis(self):
        """
        Calculate Key Performance Indicators.
        """
        self.print_header("STEP 4: KEY PERFORMANCE INDICATORS (KPIs)")
        
        kpis = {}
        
        # Total Sales
        kpis['total_sales'] = self.df['Sales'].sum()
        
        # Total Profit
        kpis['total_profit'] = self.df['Profit'].sum()
        
        # Total Orders (unique Order IDs)
        kpis['total_orders'] = self.df['Order ID'].nunique() if 'Order ID' in self.df.columns else len(self.df)
        
        # Total Quantity Sold
        kpis['total_quantity'] = self.df['Quantity'].sum() if 'Quantity' in self.df.columns else 0
        
        # Total Unique Customers
        kpis['unique_customers'] = self.df['Customer ID'].nunique() if 'Customer ID' in self.df.columns else 0
        
        # Average Order Value
        kpis['avg_order_value'] = kpis['total_sales'] / kpis['total_orders'] if kpis['total_orders'] > 0 else 0
        
        # Average Discount
        kpis['avg_discount'] = self.df['Discount'].mean() if 'Discount' in self.df.columns else 0
        
        # Average Shipping Delay - FIXED: Changed label and handle NaN
        shipping_delay = self.df['shipping_delay_days'].mean()
        kpis['avg_shipping_delay'] = 0 if pd.isna(shipping_delay) else shipping_delay
        
        # Best Performing Category
        if 'Category' in self.df.columns:
            cat_sales = self.df.groupby('Category')['Sales'].sum()
            if not cat_sales.empty:
                best_cat = cat_sales.idxmax()
                best_cat_sales = cat_sales.max()
                kpis['best_category'] = f"{best_cat} (${best_cat_sales:,.2f})"
            else:
                kpis['best_category'] = "N/A"
        else:
            kpis['best_category'] = "N/A"
        
        # Top Performing Region
        if 'Region' in self.df.columns:
            region_sales = self.df.groupby('Region')['Sales'].sum()
            if not region_sales.empty:
                best_region = region_sales.idxmax()
                best_region_sales = region_sales.max()
                kpis['best_region'] = f"{best_region} (${best_region_sales:,.2f})"
            else:
                kpis['best_region'] = "N/A"
        else:
            kpis['best_region'] = "N/A"
        
        # Display KPIs in a beautiful table
        print("\n  " + "┌" + "─" * 56 + "┐")
        print("  │ {:^56} │".format("KEY PERFORMANCE INDICATORS"))
        print("  ├" + "─" * 56 + "┤")
        
        metrics = [
            ("💰 Total Sales", f"${kpis['total_sales']:,.2f}"),
            ("📈 Total Profit", f"${kpis['total_profit']:,.2f}"),
            ("📦 Total Orders", f"{kpis['total_orders']:,}"),
            ("📊 Total Quantity Sold", f"{kpis['total_quantity']:,}"),
            ("👥 Unique Customers", f"{kpis['unique_customers']:,}"),
            ("🛒 Average Order Value", f"${kpis['avg_order_value']:,.2f}"),
            ("🏷️ Average Discount", f"{kpis['avg_discount']*100:.2f}%"),
            ("🚚 Average Shipping Delay", f"{kpis['avg_shipping_delay']:.1f} days"),  # FIXED: Changed label
            ("🏆 Best Category", kpis['best_category']),
            ("🌎 Best Region", kpis['best_region'])
        ]
        
        for label, value in metrics:
            print(f"  │ {label:<30} {value:>24} │")
        
        print("  └" + "─" * 56 + "┘")
        
        return kpis
    
    def category_analysis(self):
        """
        Analyze sales, profit, and quantity by category.
        """
        self.print_header("ANALYSIS 1: CATEGORY ANALYSIS")
        
        if 'Category' not in self.df.columns:
            print("\n  ⚠ Category column not found. Skipping category analysis.")
            return {}
        
        # Sales by Category
        sales_by_cat = self.df.groupby('Category')['Sales'].agg(['sum', 'mean', 'count']).round(2)
        sales_by_cat.columns = ['Total Sales', 'Avg Sale', 'Transaction Count']
        sales_by_cat['% of Sales'] = (sales_by_cat['Total Sales'] / sales_by_cat['Total Sales'].sum() * 100).round(2)
        
        self.print_table(sales_by_cat, "Sales by Category")
        
        # Profit by Category
        profit_by_cat = self.df.groupby('Category')['Profit'].agg(['sum', 'mean']).round(2)
        profit_by_cat.columns = ['Total Profit', 'Avg Profit']
        profit_by_cat['Profit Margin %'] = (profit_by_cat['Total Profit'] / sales_by_cat['Total Sales'] * 100).round(2)
        
        self.print_table(profit_by_cat, "Profit by Category")
        
        # Quantity by Category
        if 'Quantity' in self.df.columns:
            qty_by_cat = self.df.groupby('Category')['Quantity'].sum().round(0)
            self.print_table(qty_by_cat, "Quantity Sold by Category")
        else:
            qty_by_cat = pd.Series()
        
        return {
            'sales_by_category': sales_by_cat,
            'profit_by_category': profit_by_cat,
            'quantity_by_category': qty_by_cat
        }
    
    def product_analysis(self):
        """
        Analyze top and bottom products.
        """
        self.print_header("ANALYSIS 2: PRODUCT ANALYSIS")
        
        if 'Product Name' not in self.df.columns:
            print("\n  ⚠ Product Name column not found. Skipping product analysis.")
            return {}
        
        # Top 10 products by Sales
        top_products_sales = self.df.groupby(['Product ID', 'Product Name'])['Sales'].sum()\
            .sort_values(ascending=False).head(10).round(2)
        
        print("\n  🏆 TOP 10 PRODUCTS BY SALES")
        print("  " + "─" * 70)
        for i, (idx, sales) in enumerate(top_products_sales.items(), 1):
            product_id, product_name = idx
            short_name = product_name[:55] + "..." if len(product_name) > 55 else product_name
            print(f"  {i:2}. {short_name:<55} ${sales:>10,.2f}")
        
        # Top 10 products by Profit
        top_products_profit = self.df.groupby(['Product ID', 'Product Name'])['Profit'].sum()\
            .sort_values(ascending=False).head(10).round(2)
        
        print("\n  💰 TOP 10 PRODUCTS BY PROFIT")
        print("  " + "─" * 70)
        for i, (idx, profit) in enumerate(top_products_profit.items(), 1):
            product_id, product_name = idx
            short_name = product_name[:55] + "..." if len(product_name) > 55 else product_name
            print(f"  {i:2}. {short_name:<55} ${profit:>10,.2f}")
        
        # Loss-making products
        product_profit = self.df.groupby(['Product ID', 'Product Name'])['Profit'].sum()
        loss_products = product_profit[product_profit < 0].sort_values().head(10)
        
        print("\n  📉 TOP 10 LOSS-MAKING PRODUCTS")
        print("  " + "─" * 70)
        if len(loss_products) > 0:
            for i, (idx, loss) in enumerate(loss_products.items(), 1):
                product_id, product_name = idx
                short_name = product_name[:55] + "..." if len(product_name) > 55 else product_name
                print(f"  {i:2}. {short_name:<55} ${loss:>10,.2f}")
        else:
            print("  No loss-making products found")
        
        return {
            'top_sales': top_products_sales,
            'top_profit': top_products_profit,
            'loss_products': loss_products
        }
    
    def customer_analysis(self):
        """
        Analyze customer behavior and segments.
        """
        self.print_header("ANALYSIS 3: CUSTOMER ANALYSIS")
        
        results = {}
        
        # Top customers by sales
        if 'Customer Name' in self.df.columns and 'Customer ID' in self.df.columns:
            top_customers = self.df.groupby(['Customer ID', 'Customer Name'])['Sales'].sum()\
                .sort_values(ascending=False).head(10).round(2)
            
            print("\n  👤 TOP 10 CUSTOMERS BY SALES")
            print("  " + "─" * 60)
            for i, (idx, sales) in enumerate(top_customers.items(), 1):
                cust_id, cust_name = idx
                print(f"  {i:2}. {cust_name:<30} ${sales:>10,.2f}")
            
            results['top_customers'] = top_customers
            
            # Customers with highest number of orders
            if 'Order ID' in self.df.columns:
                customer_orders = self.df.groupby(['Customer ID', 'Customer Name'])['Order ID'].nunique()\
                    .sort_values(ascending=False).head(10)
                
                print("\n  📋 TOP 10 CUSTOMERS BY ORDER COUNT")
                print("  " + "─" * 60)
                for i, (idx, orders) in enumerate(customer_orders.items(), 1):
                    cust_id, cust_name = idx
                    print(f"  {i:2}. {cust_name:<30} {orders:>10} orders")
                
                results['customer_orders'] = customer_orders
        
        # Customer segment performance
        if 'Segment' in self.df.columns:
            segment_data = self.df.groupby('Segment')
            
            segment_perf = pd.DataFrame({
                'Total Sales': segment_data['Sales'].sum(),
                'Avg Sale': segment_data['Sales'].mean(),
                'Total Profit': segment_data['Profit'].sum(),
                'Avg Profit': segment_data['Profit'].mean(),
                'Orders': segment_data['Order ID'].nunique() if 'Order ID' in self.df.columns else len(segment_data),
                'Customers': segment_data['Customer ID'].nunique() if 'Customer ID' in self.df.columns else 0
            }).round(2)
            
            self.print_table(segment_perf, "Customer Segment Performance")
            results['segment_performance'] = segment_perf
        
        return results
    
    def regional_analysis(self):
        """
        Analyze performance by region, state, and city.
        """
        self.print_header("ANALYSIS 4: REGIONAL ANALYSIS")
        
        results = {}
        
        # Sales by Region
        if 'Region' in self.df.columns:
            region_sales = self.df.groupby('Region')['Sales'].sum().sort_values(ascending=False).round(2)
            region_profit = self.df.groupby('Region')['Profit'].sum().sort_values(ascending=False).round(2)
            
            print("\n  🌎 SALES BY REGION")
            print("  " + "─" * 70)
            for region, sales in region_sales.items():
                profit = region_profit.get(region, 0)
                margin = (profit / sales * 100) if sales > 0 else 0
                print(f"  {region:10} │ Sales: ${sales:>12,.2f} │ Profit: ${profit:>12,.2f} │ Margin: {margin:5.1f}%")
            
            results['region_sales'] = region_sales
            results['region_profit'] = region_profit
        
        # Top 10 States by Sales
        if 'State' in self.df.columns:
            state_sales = self.df.groupby('State')['Sales'].sum().sort_values(ascending=False).head(10).round(2)
            
            print("\n  🗽 TOP 10 STATES BY SALES")
            print("  " + "─" * 50)
            for i, (state, sales) in enumerate(state_sales.items(), 1):
                print(f"  {i:2}. {state:20} ${sales:>12,.2f}")
            
            results['state_sales'] = state_sales
        
        # Top 10 Cities by Sales
        if 'City' in self.df.columns:
            city_sales = self.df.groupby('City')['Sales'].sum().sort_values(ascending=False).head(10).round(2)
            
            print("\n  🏙️ TOP 10 CITIES BY SALES")
            print("  " + "─" * 50)
            for i, (city, sales) in enumerate(city_sales.items(), 1):
                print(f"  {i:2}. {city:20} ${sales:>12,.2f}")
            
            results['city_sales'] = city_sales
        
        return results
    
    def shipping_analysis(self):
        """
        Analyze shipping modes and delays.
        """
        self.print_header("ANALYSIS 5: SHIPPING ANALYSIS")
        
        results = {}
        
        # Orders by Ship Mode
        if 'Ship Mode' in self.df.columns:
            ship_mode_counts = self.df['Ship Mode'].value_counts()
            ship_mode_pct = (ship_mode_counts / ship_mode_counts.sum() * 100).round(1)
            
            print("\n  🚚 ORDERS BY SHIP MODE")
            print("  " + "─" * 50)
            for mode, count in ship_mode_counts.items():
                pct = ship_mode_pct[mode]
                bar = "█" * int(pct / 5)
                print(f"  {mode:15} │ {count:6} orders │ {pct:5.1f}% {bar}")
            
            results['ship_mode_counts'] = ship_mode_counts
            
            # Average shipping delay by Ship Mode
            if 'shipping_delay_days' in self.df.columns:
                delay_by_mode = self.df.groupby('Ship Mode')['shipping_delay_days'].mean().round(1).sort_values()
                
                print("\n  ⏱️ AVERAGE SHIPPING DELAY BY SHIP MODE")
                print("  " + "─" * 50)
                for mode, delay in delay_by_mode.items():
                    print(f"  {mode:15} │ {delay:5.1f} days")
                
                results['delay_by_mode'] = delay_by_mode
        
        return results
    
    def discount_analysis(self):
        """
        Analyze the impact of discounts on sales and profit.
        """
        self.print_header("ANALYSIS 6: DISCOUNT ANALYSIS")
        
        if 'Discount' not in self.df.columns:
            print("\n  ⚠ Discount column not found. Skipping discount analysis.")
            return pd.DataFrame()
        
        # Create discount brackets
        try:
            self.df['Discount_Bracket'] = pd.cut(
                self.df['Discount'], 
                bins=[-0.01, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 1.0],
                labels=['No Discount', '0-10%', '10-20%', '20-30%', '30-40%', '40-50%', '50%+']
            )
        except:
            # Fallback if bins don't work
            self.df['Discount_Bracket'] = pd.cut(
                self.df['Discount'], 
                bins=5,
                labels=['Very Low', 'Low', 'Medium', 'High', 'Very High']
            )
        
        # Impact on sales
        discount_sales = self.df.groupby('Discount_Bracket', observed=False).agg({
            'Sales': ['count', 'sum', 'mean'],
            'Profit': ['sum', 'mean']
        }).round(2)
        
        # Flatten column names
        discount_sales.columns = ['_'.join(col).strip() for col in discount_sales.columns.values]
        
        print("\n  💲 IMPACT OF DISCOUNT ON SALES AND PROFIT")
        print("  " + "─" * 80)
        
        # Format the table
        table_data = []
        for bracket in discount_sales.index:
            count = discount_sales.loc[bracket, 'Sales_count']
            sales_sum = discount_sales.loc[bracket, 'Sales_sum']
            sales_mean = discount_sales.loc[bracket, 'Sales_mean']
            profit_sum = discount_sales.loc[bracket, 'Profit_sum']
            profit_mean = discount_sales.loc[bracket, 'Profit_mean']
            margin = (profit_sum / sales_sum * 100) if sales_sum != 0 else 0
            
            # Color code based on profit
            if profit_sum > 0:
                profit_indicator = "✅"
            elif profit_sum < 0:
                profit_indicator = "❌"
            else:
                profit_indicator = "➖"
            
            print(f"  {bracket:12} │ Count: {count:4} │ Sales: ${sales_sum:>10,.2f} │ "
                  f"Profit: {profit_indicator} ${profit_sum:>9,.2f} │ Margin: {margin:5.1f}%")
        
        # Profit margin by discount bracket
        if 'Sales_sum' in discount_sales.columns and 'Profit_sum' in discount_sales.columns:
            discount_sales['Profit Margin %'] = (
                discount_sales['Profit_sum'] / discount_sales['Sales_sum'] * 100
            ).round(1)
            
            print("\n  📊 PROFIT MARGIN BY DISCOUNT BRACKET")
            print("  " + "─" * 60)
            for bracket in discount_sales.index:
                margin = discount_sales.loc[bracket, 'Profit Margin %']
                count = discount_sales.loc[bracket, 'Sales_count']
                if pd.notna(margin):
                    # Create a visual bar
                    if margin > 0:
                        bar = "🟩" * min(int(abs(margin) / 5), 10)
                    else:
                        bar = "🟥" * min(int(abs(margin) / 5), 10)
                    print(f"  {bracket:12} │ {count:4} transactions │ Margin: {margin:6.1f}% {bar}")
        
        return discount_sales
    
    def profitability_analysis(self):
        """
        Analyze profit margins by category and region.
        """
        self.print_header("ANALYSIS 7: PROFITABILITY ANALYSIS")
        
        results = {}
        
        # Profit margin by Category
        if 'Category' in self.df.columns:
            cat_data = []
            for category in self.df['Category'].unique():
                cat_df = self.df[self.df['Category'] == category]
                total_sales = cat_df['Sales'].sum()
                total_profit = cat_df['Profit'].sum()
                if total_sales != 0:
                    margin = (total_profit / total_sales * 100)
                else:
                    margin = 0
                cat_data.append({'Category': category, 'Profit Margin %': round(margin, 1)})
            
            cat_margin = pd.DataFrame(cat_data).set_index('Category').sort_values('Profit Margin %', ascending=False)
            
            print("\n  📈 PROFIT MARGIN BY CATEGORY")
            print("  " + "─" * 40)
            for cat, row in cat_margin.iterrows():
                margin = row['Profit Margin %']
                if margin > 10:
                    emoji = "🟢"
                elif margin > 0:
                    emoji = "🟡"
                else:
                    emoji = "🔴"
                print(f"  {emoji} {cat:15} {margin:6.1f}%")
            
            results['category_margin'] = cat_margin
        
        # Profit margin by Region
        if 'Region' in self.df.columns:
            region_data = []
            for region in self.df['Region'].unique():
                region_df = self.df[self.df['Region'] == region]
                total_sales = region_df['Sales'].sum()
                total_profit = region_df['Profit'].sum()
                if total_sales != 0:
                    margin = (total_profit / total_sales * 100)
                else:
                    margin = 0
                region_data.append({'Region': region, 'Profit Margin %': round(margin, 1)})
            
            region_margin = pd.DataFrame(region_data).set_index('Region').sort_values('Profit Margin %', ascending=False)
            
            print("\n  🌍 PROFIT MARGIN BY REGION")
            print("  " + "─" * 40)
            for region, row in region_margin.iterrows():
                margin = row['Profit Margin %']
                if margin > 12:
                    emoji = "🟢"
                elif margin > 8:
                    emoji = "🟡"
                else:
                    emoji = "🔴"
                print(f"  {emoji} {region:10} {margin:6.1f}%")
            
            results['region_margin'] = region_margin
        
        return results
    
    def data_summary(self):
        """
        Generate statistical summary of key metrics.
        """
        self.print_header("DATA SUMMARY ANALYSIS")
        
        # Select numeric columns for summary
        numeric_cols = ['Sales', 'Profit']
        if 'Discount' in self.df.columns:
            numeric_cols.append('Discount')
        if 'shipping_delay_days' in self.df.columns:
            numeric_cols.append('shipping_delay_days')
        
        existing_cols = [col for col in numeric_cols if col in self.df.columns]
        
        if existing_cols:
            # Statistical summary
            summary_stats = self.df[existing_cols].describe().round(2)
            self.print_table(summary_stats, "Statistical Summary")
            
            # Distribution insights
            print("\n  📈 DISTRIBUTION INSIGHTS")
            print("  " + "─" * 60)
            print(f"  💰 Sales Range: ${self.df['Sales'].min():,.2f} to ${self.df['Sales'].max():,.2f}")
            print(f"  💸 Profit Range: ${self.df['Profit'].min():,.2f} to ${self.df['Profit'].max():,.2f}")
            
            neg_profit = (self.df['Profit'] < 0).sum()
            neg_pct = neg_profit / len(self.df) * 100
            print(f"  📉 Transactions with Negative Profit: {neg_profit:,} ({neg_pct:.1f}%)")
            
            if 'Discount' in self.df.columns:
                disc_trans = (self.df['Discount'] > 0).sum()
                disc_pct = disc_trans / len(self.df) * 100
                print(f"  🏷️ Transactions with Discount: {disc_trans:,} ({disc_pct:.1f}%)")
            
            return summary_stats
        else:
            print("\n  ⚠ No numeric columns found for summary")
            return pd.DataFrame()
    
    def run_complete_analysis(self):
        """
        Run all analysis steps in sequence.
        """
        print("\n" + "🌟" * 40)
        print("🌟  RETAIL DATA ANALYSIS SYSTEM  🌟".center(78))
        print("🌟" * 40)
        
        # Run all steps
        if not self.load_and_validate_data():
            return False
        
        self.clean_data()
        self.calculate_features()
        
        # Store all results
        results = {}
        
        results['kpis'] = self.calculate_kpis()
        results['category'] = self.category_analysis()
        results['product'] = self.product_analysis()
        results['customer'] = self.customer_analysis()
        results['regional'] = self.regional_analysis()
        results['shipping'] = self.shipping_analysis()
        results['discount'] = self.discount_analysis()
        results['profitability'] = self.profitability_analysis()
        results['summary'] = self.data_summary()
        
        # Count analyses
        analysis_count = 0
        for key, value in results.items():
            if value is not None:
                analysis_count += 1
        
        print("\n" + "✨" * 40)
        print(f"✨  ANALYSIS COMPLETE! {analysis_count} Analytical Tables Generated  ✨".center(78))
        print("✨" * 40)
        
        return results