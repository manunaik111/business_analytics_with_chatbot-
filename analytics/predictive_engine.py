"""
Retail Data Analysis System - Predictive Engine Module
Plugs into RetailDataAnalyzer to provide sales forecasting capabilities.
Designed for real-time data upload compatibility.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class SalesPredictiveEngine:
    """
    Predictive engine for sales forecasting.
    Accepts a pandas DataFrame directly — works with live/uploaded data.
    
    Usage:
        from analytics.predictive_engine import SalesPredictiveEngine
        engine = SalesPredictiveEngine(df=analyzer.df)
        engine.run_full_forecast()
    """

    def __init__(self, df: pd.DataFrame = None, filepath: str = None):
        """
        Initialize with either a DataFrame (for real-time/live data)
        or a filepath (for CSV loading).
        DataFrame takes priority over filepath.
        """
        self.df = df
        self.filepath = filepath
        self.monthly_sales = None
        self.forecast_results = {}

    # ─────────────────────────────────────────────
    # PRINT HELPERS  (matches analysis.py style)
    # ─────────────────────────────────────────────

    def print_header(self, title):
        print("\n" + "★" * 80)
        print(f"  {title.upper()}")
        print("★" * 80)

    def print_subheader(self, title):
        print("\n" + "┌" + "─" * 78 + "┐")
        print(f"│ {title:<77}│")
        print("└" + "─" * 78 + "┘")

    def print_table(self, df, title=None):
        if title:
            print(f"\n  📊 {title}")
            print("  " + "─" * 60)
        if isinstance(df, pd.Series):
            df = df.to_frame()
        table_str = df.to_string(
            justify='right',
            float_format=lambda x: f"{x:,.2f}" if isinstance(x, float) else str(x)
        )
        for line in table_str.split('\n'):
            print(f"  {line}")

    # ─────────────────────────────────────────────
    # DATA LOADING
    # ─────────────────────────────────────────────

    def load_data(self):
        """Load from filepath if df not already provided."""
        if self.df is not None:
            print(f"\n  ✅ Using live DataFrame: {self.df.shape[0]:,} rows, {self.df.shape[1]} columns")
            return True

        if self.filepath:
            try:
                self.df = pd.read_csv(self.filepath, encoding='utf-8-sig')
                print(f"\n  ✅ Loaded from {self.filepath}: {self.df.shape[0]:,} rows")
                return True
            except Exception as e:
                print(f"\n  ❌ Failed to load file: {e}")
                return False

        print("\n  ❌ No data source provided. Pass df= or filepath=")
        return False

    def _ensure_dates(self):
        """Parse Order Date to datetime if not already done."""
        if 'Order Date' not in self.df.columns:
            print("\n  ❌ 'Order Date' column required for forecasting.")
            return False

        if not pd.api.types.is_datetime64_any_dtype(self.df['Order Date']):
            date_formats = ['%d-%m-%Y', '%m-%d-%Y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']
            for fmt in date_formats:
                try:
                    parsed = pd.to_datetime(self.df['Order Date'], format=fmt, errors='coerce')
                    if parsed.notna().sum() > 0.8 * len(self.df):
                        self.df['Order Date'] = parsed
                        break
                except Exception:
                    continue
            else:
                self.df['Order Date'] = pd.to_datetime(self.df['Order Date'], errors='coerce')

        self.df = self.df.dropna(subset=['Order Date'])
        return True

    # ─────────────────────────────────────────────
    # STEP 1: BUILD MONTHLY TIME SERIES
    # ─────────────────────────────────────────────

    def build_monthly_series(self):
        """Aggregate sales into a monthly time series."""
        self.print_header("PREDICTIVE ENGINE — STEP 1: BUILDING MONTHLY TIME SERIES")

        if not self._ensure_dates():
            return False

        self.df['YearMonth'] = self.df['Order Date'].dt.to_period('M')
        self.monthly_sales = (
            self.df.groupby('YearMonth')['Sales']
            .sum()
            .sort_index()
            .reset_index()
        )
        self.monthly_sales.columns = ['YearMonth', 'Sales']
        self.monthly_sales['YearMonth_dt'] = self.monthly_sales['YearMonth'].dt.to_timestamp()
        self.forecast_results['monthly_sales'] = self.monthly_sales.copy()

        print(f"\n  ✅ Monthly series built: {len(self.monthly_sales)} months")
        print(f"  📅 Date range: {self.monthly_sales['YearMonth'].iloc[0]}  →  {self.monthly_sales['YearMonth'].iloc[-1]}")

        self.print_table(
            self.monthly_sales[['YearMonth', 'Sales']].tail(12).set_index('YearMonth'),
            "Last 12 Months of Sales"
        )
        return True

    # ─────────────────────────────────────────────
    # STEP 2: TREND & SEASONALITY DECOMPOSITION
    # ─────────────────────────────────────────────

    def decompose_trend_seasonality(self):
        """Extract trend and seasonal components using moving averages."""
        self.print_header("PREDICTIVE ENGINE — STEP 2: TREND & SEASONALITY ANALYSIS")

        if self.monthly_sales is None or len(self.monthly_sales) < 4:
            print("\n  ⚠ Not enough data for decomposition (need ≥ 4 months).")
            return {}

        sales = self.monthly_sales['Sales'].values.astype(float)
        n = len(sales)

        # ── Trend via centred moving average (window = min(12, n//2))
        window = min(12, max(3, n // 2))
        trend = pd.Series(sales).rolling(window=window, center=True, min_periods=1).mean().values

        # ── Detrended series
        detrended = sales - trend

        # ── Monthly seasonal indices (average deviation per calendar month)
        months = self.monthly_sales['YearMonth_dt'].dt.month.values
        seasonal_index = {}
        for m in range(1, 13):
            mask = months == m
            if mask.any():
                seasonal_index[m] = float(np.mean(detrended[mask]))
            else:
                seasonal_index[m] = 0.0

        # Normalise so seasonal indices sum to 0
        mean_si = np.mean(list(seasonal_index.values()))
        seasonal_index = {m: v - mean_si for m, v in seasonal_index.items()}

        # ── Overall growth rate (month-over-month average %)
        pct_changes = pd.Series(sales).pct_change().dropna()
        avg_growth_rate = float(pct_changes.mean()) if len(pct_changes) > 0 else 0.0

        # ── Trend direction
        if avg_growth_rate > 0.02:
            trend_dir = "📈 UPWARD"
        elif avg_growth_rate < -0.02:
            trend_dir = "📉 DOWNWARD"
        else:
            trend_dir = "➡️  STABLE"

        # ── Peak / trough months
        month_names = {
            1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
            7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
        }
        peak_month = max(seasonal_index, key=seasonal_index.get)
        trough_month = min(seasonal_index, key=seasonal_index.get)

        print(f"\n  📊 Trend Direction      : {trend_dir}")
        print(f"  📊 Avg Monthly Growth   : {avg_growth_rate * 100:+.2f}%")
        print(f"  🔝 Seasonal Peak Month  : {month_names[peak_month]}  (index: {seasonal_index[peak_month]:+,.2f})")
        print(f"  🔻 Seasonal Trough Month: {month_names[trough_month]}  (index: {seasonal_index[trough_month]:+,.2f})")

        # ── Print seasonal indices table
        print("\n  📅 MONTHLY SEASONAL INDICES")
        print("  " + "─" * 50)
        for m in range(1, 13):
            si = seasonal_index[m]
            bar = ("▲" if si >= 0 else "▼") * min(int(abs(si) / max(abs(v) for v in seasonal_index.values()) * 10) + 1, 10)
            print(f"  {month_names[m]:3}  │  index: {si:+10,.2f}  {bar}")

        self.forecast_results['trend'] = trend
        self.forecast_results['seasonal_index'] = seasonal_index
        self.forecast_results['avg_growth_rate'] = avg_growth_rate
        self.forecast_results['peak_month'] = peak_month
        self.forecast_results['trough_month'] = trough_month

        return self.forecast_results

    # ─────────────────────────────────────────────
    # STEP 3: LINEAR REGRESSION FORECAST
    # ─────────────────────────────────────────────

    def linear_regression_forecast(self, periods: int = 6):
        """
        Fit a simple OLS linear trend and project forward `periods` months.
        Returns a DataFrame with predicted sales + confidence bands.
        """
        self.print_header(f"PREDICTIVE ENGINE — STEP 3: LINEAR REGRESSION FORECAST ({periods} MONTHS)")

        if self.monthly_sales is None or len(self.monthly_sales) < 3:
            print("\n  ⚠ Not enough data for regression (need ≥ 3 months).")
            return pd.DataFrame()

        sales = self.monthly_sales['Sales'].values.astype(float)
        X = np.arange(len(sales), dtype=float)

        # ── OLS fit
        coeffs = np.polyfit(X, sales, deg=1)
        slope, intercept = coeffs
        fitted = slope * X + intercept
        residuals = sales - fitted
        rmse = float(np.sqrt(np.mean(residuals ** 2)))
        ss_res = float(np.sum(residuals ** 2))
        ss_tot = float(np.sum((sales - np.mean(sales)) ** 2))
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        print(f"\n  📐 Regression Results")
        print(f"  {'Slope (monthly change)':<30} ${slope:>12,.2f}")
        print(f"  {'Intercept':<30} ${intercept:>12,.2f}")
        print(f"  {'R² (fit quality)':<30} {r2:>12.4f}")
        print(f"  {'RMSE':<30} ${rmse:>12,.2f}")

        # ── Project forward
        last_idx = len(sales) - 1
        last_period = self.monthly_sales['YearMonth'].iloc[-1]

        future_rows = []
        seasonal_index = self.forecast_results.get('seasonal_index', {m: 0 for m in range(1, 13)})

        for i in range(1, periods + 1):
            future_idx = last_idx + i
            future_period = last_period + i
            future_dt = future_period.to_timestamp()
            month = future_dt.month

            base_pred = slope * future_idx + intercept
            seasonal_adj = seasonal_index.get(month, 0)
            final_pred = max(0.0, base_pred + seasonal_adj)

            # 95% confidence interval (±1.96 * RMSE scaled by sqrt(i))
            margin = 1.96 * rmse * np.sqrt(i / len(sales) + 1)
            lower = max(0.0, final_pred - margin)
            upper = final_pred + margin

            future_rows.append({
                'Period': str(future_period),
                'Predicted Sales': round(final_pred, 2),
                'Lower Bound (95%)': round(lower, 2),
                'Upper Bound (95%)': round(upper, 2),
                'Seasonal Adj': round(seasonal_adj, 2)
            })

        forecast_df = pd.DataFrame(future_rows).set_index('Period')

        print("\n  🔮 SALES FORECAST")
        print("  " + "─" * 75)
        print(f"  {'Period':<10}  {'Predicted':>14}  {'Lower (95%)':>14}  {'Upper (95%)':>14}  {'Seas. Adj':>10}")
        print("  " + "─" * 75)
        for period, row in forecast_df.iterrows():
            print(f"  {period:<10}  ${row['Predicted Sales']:>13,.2f}  "
                  f"${row['Lower Bound (95%)']:>13,.2f}  "
                  f"${row['Upper Bound (95%)']:>13,.2f}  "
                  f"${row['Seasonal Adj']:>9,.2f}")

        self.forecast_results['linear_forecast'] = forecast_df
        return forecast_df

    # ─────────────────────────────────────────────
    # STEP 4: EXPONENTIAL SMOOTHING FORECAST
    # ─────────────────────────────────────────────

    def exponential_smoothing_forecast(self, periods: int = 6, alpha: float = 0.3):
        """
        Simple exponential smoothing (SES) forecast.
        alpha controls how fast older observations decay (0 < alpha < 1).
        Higher alpha = more weight on recent data.
        """
        self.print_header(f"PREDICTIVE ENGINE — STEP 4: EXPONENTIAL SMOOTHING FORECAST (α={alpha})")

        if self.monthly_sales is None or len(self.monthly_sales) < 2:
            print("\n  ⚠ Not enough data for exponential smoothing.")
            return pd.DataFrame()

        sales = self.monthly_sales['Sales'].values.astype(float)

        # ── Apply SES
        smoothed = [sales[0]]
        for val in sales[1:]:
            smoothed.append(alpha * val + (1 - alpha) * smoothed[-1])

        last_smooth = smoothed[-1]
        last_period = self.monthly_sales['YearMonth'].iloc[-1]
        seasonal_index = self.forecast_results.get('seasonal_index', {m: 0 for m in range(1, 13)})

        # In-sample error
        fitted_arr = np.array(smoothed)
        residuals = sales - fitted_arr
        mae = float(np.mean(np.abs(residuals)))
        rmse = float(np.sqrt(np.mean(residuals ** 2)))

        print(f"\n  📐 Exponential Smoothing Stats")
        print(f"  {'Alpha (smoothing factor)':<30} {alpha:>12.2f}")
        print(f"  {'Level (last smoothed value)':<30} ${last_smooth:>12,.2f}")
        print(f"  {'MAE':<30} ${mae:>12,.2f}")
        print(f"  {'RMSE':<30} ${rmse:>12,.2f}")

        # ── Project forward (level stays constant = last_smooth, +seasonal)
        future_rows = []
        for i in range(1, periods + 1):
            future_period = last_period + i
            future_dt = future_period.to_timestamp()
            month = future_dt.month

            seasonal_adj = seasonal_index.get(month, 0)
            pred = max(0.0, last_smooth + seasonal_adj)
            margin = 1.96 * rmse * np.sqrt(i)
            lower = max(0.0, pred - margin)
            upper = pred + margin

            future_rows.append({
                'Period': str(future_period),
                'SES Forecast': round(pred, 2),
                'Lower Bound (95%)': round(lower, 2),
                'Upper Bound (95%)': round(upper, 2),
            })

        ses_df = pd.DataFrame(future_rows).set_index('Period')

        print("\n  🔮 EXPONENTIAL SMOOTHING FORECAST")
        print("  " + "─" * 65)
        print(f"  {'Period':<10}  {'SES Forecast':>14}  {'Lower (95%)':>14}  {'Upper (95%)':>14}")
        print("  " + "─" * 65)
        for period, row in ses_df.iterrows():
            print(f"  {period:<10}  ${row['SES Forecast']:>13,.2f}  "
                  f"${row['Lower Bound (95%)']:>13,.2f}  "
                  f"${row['Upper Bound (95%)']:>13,.2f}")

        self.forecast_results['ses_forecast'] = ses_df
        return ses_df

    # ─────────────────────────────────────────────
    # STEP 5: CATEGORY-LEVEL FORECAST
    # ─────────────────────────────────────────────

    def category_forecast(self, periods: int = 6):
        """
        Run a simple linear trend forecast per product category.
        """
        self.print_header(f"PREDICTIVE ENGINE — STEP 5: CATEGORY-LEVEL FORECAST ({periods} MONTHS)")

        if 'Category' not in self.df.columns:
            print("\n  ⚠ Category column not found. Skipping.")
            return {}

        if not self._ensure_dates():
            return {}

        categories = self.df['Category'].dropna().unique()
        category_forecasts = {}

        for cat in sorted(categories):
            cat_df = self.df[self.df['Category'] == cat].copy()
            cat_df['YearMonth'] = cat_df['Order Date'].dt.to_period('M')
            monthly = (
                cat_df.groupby('YearMonth')['Sales']
                .sum()
                .sort_index()
                .reset_index()
            )
            monthly.columns = ['YearMonth', 'Sales']

            if len(monthly) < 3:
                print(f"\n  ⚠ Skipping {cat} — insufficient data ({len(monthly)} months)")
                continue

            sales = monthly['Sales'].values.astype(float)
            X = np.arange(len(sales), dtype=float)
            slope, intercept = np.polyfit(X, sales, deg=1)
            last_period = monthly['YearMonth'].iloc[-1]
            last_idx = len(sales) - 1

            print(f"\n  📦 {cat.upper()}")
            print("  " + "─" * 65)
            print(f"  {'Trend (monthly Δ)':<30} ${slope:>+12,.2f}")

            rows = []
            for i in range(1, periods + 1):
                future_period = last_period + i
                pred = max(0.0, slope * (last_idx + i) + intercept)
                rows.append({'Period': str(future_period), 'Predicted Sales': round(pred, 2)})
                print(f"    {str(future_period):<12} → ${pred:>12,.2f}")

            category_forecasts[cat] = pd.DataFrame(rows).set_index('Period')

        self.forecast_results['category_forecast'] = category_forecasts
        return category_forecasts

    # ─────────────────────────────────────────────
    # STEP 6: REVENUE TARGETS & ALERTS
    # ─────────────────────────────────────────────

    def revenue_targets_and_alerts(self, target_growth_pct: float = 10.0):
        """
        Compare forecasted revenue against a growth target.
        Generates PASS / WARNING / ALERT flags per month.
        """
        self.print_header("PREDICTIVE ENGINE — STEP 6: REVENUE TARGETS & ALERTS")

        linear_fc = self.forecast_results.get('linear_forecast')
        if linear_fc is None or linear_fc.empty:
            print("\n  ⚠ Run linear_regression_forecast() first.")
            return pd.DataFrame()

        # Baseline = average of last 3 months actual
        recent_avg = self.monthly_sales['Sales'].tail(3).mean()
        monthly_target = recent_avg * (1 + target_growth_pct / 100)

        print(f"\n  🎯 Target Growth          : +{target_growth_pct:.1f}% vs recent 3-month avg")
        print(f"  📊 Recent 3-Month Avg     : ${recent_avg:,.2f}")
        print(f"  🏁 Monthly Revenue Target : ${monthly_target:,.2f}")

        print("\n  " + "─" * 75)
        print(f"  {'Period':<10}  {'Predicted':>14}  {'Target':>14}  {'vs Target':>10}  {'Status':>12}")
        print("  " + "─" * 75)

        alert_rows = []
        for period, row in linear_fc.iterrows():
            pred = row['Predicted Sales']
            diff = pred - monthly_target
            diff_pct = (diff / monthly_target * 100) if monthly_target > 0 else 0

            if diff_pct >= 5:
                status = "✅ ON TRACK"
            elif diff_pct >= -5:
                status = "⚠️  WARNING"
            else:
                status = "🚨 ALERT"

            print(f"  {period:<10}  ${pred:>13,.2f}  ${monthly_target:>13,.2f}  "
                  f"{diff_pct:>+9.1f}%  {status}")

            alert_rows.append({
                'Period': period,
                'Predicted Sales': pred,
                'Target': round(monthly_target, 2),
                'vs Target %': round(diff_pct, 2),
                'Status': status
            })

        alerts_df = pd.DataFrame(alert_rows).set_index('Period')
        self.forecast_results['alerts'] = alerts_df
        return alerts_df

    # ─────────────────────────────────────────────
    # STEP 7: FORECAST SUMMARY
    # ─────────────────────────────────────────────

    def forecast_summary(self):
        """Print a consolidated summary of all forecast results."""
        self.print_header("PREDICTIVE ENGINE — FORECAST SUMMARY")

        linear_fc = self.forecast_results.get('linear_forecast', pd.DataFrame())
        ses_fc = self.forecast_results.get('ses_forecast', pd.DataFrame())

        if linear_fc.empty and ses_fc.empty:
            print("\n  ⚠ No forecast results available. Run full forecast first.")
            return

        print("\n  " + "┌" + "─" * 72 + "┐")
        print("  │ {:^72} │".format("6-MONTH FORECAST COMPARISON"))
        print("  ├" + "─" * 72 + "┤")
        print(f"  │ {'Period':<10}  {'Linear Reg':>14}  {'Exp Smooth':>14}  {'Avg Forecast':>14}  │")
        print("  ├" + "─" * 72 + "┤")

        periods = linear_fc.index.tolist() if not linear_fc.empty else ses_fc.index.tolist()
        for period in periods:
            lin_val = linear_fc.loc[period, 'Predicted Sales'] if period in linear_fc.index else 0
            ses_val = ses_fc.loc[period, 'SES Forecast'] if period in ses_fc.index else 0
            avg_val = (lin_val + ses_val) / 2 if lin_val and ses_val else lin_val or ses_val
            print(f"  │ {period:<10}  ${lin_val:>13,.2f}  ${ses_val:>13,.2f}  ${avg_val:>13,.2f}  │")

        print("  └" + "─" * 72 + "┘")

        # Key insights
        if not linear_fc.empty:
            total_6m = linear_fc['Predicted Sales'].sum()
            peak_period = linear_fc['Predicted Sales'].idxmax()
            peak_val = linear_fc['Predicted Sales'].max()
            print(f"\n  💰 Total 6-Month Forecasted Revenue : ${total_6m:,.2f}")
            print(f"  🔝 Peak Forecast Period              : {peak_period}  (${peak_val:,.2f})")

        growth_rate = self.forecast_results.get('avg_growth_rate', 0)
        print(f"  📈 Avg Monthly Growth Rate           : {growth_rate * 100:+.2f}%")
        peak_m = self.forecast_results.get('peak_month')
        if peak_m:
            month_names = {
                1: 'January', 2: 'February', 3: 'March', 4: 'April',
                5: 'May', 6: 'June', 7: 'July', 8: 'August',
                9: 'September', 10: 'October', 11: 'November', 12: 'December'
            }
            print(f"  🗓️  Historically Strongest Month      : {month_names.get(peak_m, str(peak_m))}")

    # ─────────────────────────────────────────────
    # MAIN ENTRY POINT
    # ─────────────────────────────────────────────

    def run_full_forecast(self, forecast_periods: int = 6,
                          target_growth_pct: float = 10.0,
                          ses_alpha: float = 0.3):
        """
        Run the complete predictive pipeline in sequence.

        Args:
            forecast_periods    : Number of months to forecast ahead (default 6)
            target_growth_pct   : Revenue growth target % for alert generation (default 10)
            ses_alpha           : Smoothing factor for exponential smoothing (default 0.3)

        Returns:
            dict with all forecast results
        """
        print("\n" + "🔮" * 40)
        print("🔮  SALES PREDICTIVE ENGINE  🔮".center(78))
        print("🔮" * 40)

        if not self.load_data():
            return {}

        if not self.build_monthly_series():
            return {}

        self.decompose_trend_seasonality()
        self.linear_regression_forecast(periods=forecast_periods)
        self.exponential_smoothing_forecast(periods=forecast_periods, alpha=ses_alpha)
        self.category_forecast(periods=forecast_periods)
        self.revenue_targets_and_alerts(target_growth_pct=target_growth_pct)
        self.forecast_summary()

        print("\n" + "✨" * 40)
        print("✨  PREDICTIVE ENGINE COMPLETE  ✨".center(78))
        print("✨" * 40)

        return self.forecast_results
