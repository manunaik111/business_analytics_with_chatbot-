"""
data_management/schema_mapper.py

Conservative column mapper — only renames when the alias is unambiguously
about that concept.

Rules:
  - Only map STRONG aliases (domain-specific names that clearly mean one thing).
  - NEVER map generic words (amount, value, count, type, id, name) to sales columns.
  - NEVER map domain-specific non-sales words (casualties, severity, diagnosis)
    to sales columns.
  - If a dataset is not sales data, leave its columns alone and report it honestly.
"""

import re

import pandas as pd

# ── Conservative alias map ────────────────────────────────────────────────────
# Only aliases that are UNAMBIGUOUSLY about this concept belong here.
#
# Deliberately excluded (too risky):
#   Sales   ← amount, value, total, price, fare, income, earnings, transaction_amount
#   Quantity← count, volume, cases, casualties, victims
#   Category← type, class, group, dept, accident_type, incident_type, crime_type
#   Order ID← id, record_id
#   Customer Name ← name, customer, client
# ─────────────────────────────────────────────────────────────────────────────
COLUMN_MAP: dict[str, list[str]] = {

    # ── Sales / Revenue ───────────────────────────────────────────────────────
    # Only map columns that explicitly say "sales" or "revenue"
    "Sales": [
        "sales",
        "revenue",
        "total_sales",
        "totalsales",
        "sale_amount",
        "net_sales",
        "gross_sales",
        "sales_amount",
        "revenue_amount",
    ],

    # ── Profit ────────────────────────────────────────────────────────────────
    # Only map columns that explicitly contain "profit"
    "Profit": [
        "profit",
        "net_profit",
        "netprofit",
        "gross_profit",
        "operating_profit",
        "profit_amount",
    ],

    # ── Order / Transaction ID ────────────────────────────────────────────────
    # Avoid bare "id" — it could be anything
    "Order ID": [
        "order_id",
        "orderid",
        "order_number",
        "ordernumber",
        "transaction_id",
        "transactionid",
        "invoice_id",
        "invoice_no",
        "invoice_number",
        "receipt_id",
        "receipt_no",
    ],

    # ── Customer ──────────────────────────────────────────────────────────────
    "Customer ID": [
        "customer_id",
        "customerid",
        "client_id",
        "clientid",
        "buyer_id",
        "member_id",
    ],
    "Customer Name": [
        "customer_name",
        "customername",
        "client_name",
        "clientname",
        "buyer_name",
    ],

    # ── Product ───────────────────────────────────────────────────────────────
    "Product Name": [
        "product_name",
        "productname",
        "item_name",
        "itemname",
        "product_description",
        "sku_name",
    ],

    # ── Category ──────────────────────────────────────────────────────────────
    # Only explicit "category" or "product_category" — not generic "type" or "class"
    "Category": [
        "category",
        "product_category",
        "item_category",
        "sales_category",
    ],

    # ── Sub-Category ──────────────────────────────────────────────────────────
    "Sub-Category": [
        "sub_category",
        "subcategory",
        "sub-category",
        "subcat",
        "product_subcategory",
    ],

    # ── Geography ─────────────────────────────────────────────────────────────
    # Only explicitly geographic aggregation columns, not raw "city" or "country"
    # (those are fine as-is for non-sales datasets)
    "Region": [
        "region",
        "sales_region",
        "territory",
        "sales_territory",
        "market_region",
    ],

    # ── Dates ─────────────────────────────────────────────────────────────────
    # Map common date column aliases to Order Date only when clearly transactional
    "Order Date": [
        "order_date",
        "orderdate",
        "transaction_date",
        "transactiondate",
        "purchase_date",
        "sale_date",
        "invoice_date",
    ],
    "Ship Date": [
        "ship_date",
        "shipdate",
        "shipping_date",
        "delivery_date",
        "dispatch_date",
    ],

    # ── Quantity ──────────────────────────────────────────────────────────────
    # Only map explicit order-quantity columns; NOT count/volume/casualties/victims
    "Quantity": [
        "quantity",
        "qty",
        "units_sold",
        "items_sold",
        "order_quantity",
        "quantity_ordered",
        "num_items",
        "no_of_items",
        "amount_ordered",
    ],

    # ── Discount ──────────────────────────────────────────────────────────────
    "Discount": [
        "discount",
        "discount_rate",
        "discount_pct",
        "discount_percent",
        "disc_rate",
        "rebate_rate",
    ],
}

# ── Build reverse lookup: alias (lowercase, normalised) → standard name ───────
_REVERSE_MAP: dict[str, str] = {}
for _standard, _aliases in COLUMN_MAP.items():
    for _alias in _aliases:
        _key = _alias.lower().strip()
        _REVERSE_MAP[_key] = _standard


# ─────────────────────────────────────────────────────────────────────────────
def map_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Rename DataFrame columns to standard names where a *conservative* alias
    match is found.

    Returns:
        (mapped_df, mapping_report)
        mapping_report = {"Sales": "revenue", "Order Date": "transaction_date", ...}
    """
    df = df.copy()
    mapping_report: dict[str, str] = {}
    rename_dict: dict[str, str] = {}

    for col in df.columns:
        # Normalise: lowercase, strip, spaces/dashes → underscores
        normalised = col.lower().strip().replace(" ", "_").replace("-", "_")
        if normalised not in _REVERSE_MAP:
            continue
        standard = _REVERSE_MAP[normalised]
        # Skip if the standard column is already present (don't overwrite)
        if standard in df.columns:
            continue
        # Skip if the column name is already the standard name
        if col == standard:
            continue
        rename_dict[col] = standard
        mapping_report[standard] = col  # standard → original name

    if rename_dict:
        df = df.rename(columns=rename_dict)

    return df, mapping_report


def detect_dataset_type(df: pd.DataFrame) -> str:
    """
    Classify the dataset based on what columns are present AFTER mapping.
    Uses post-mapping column names so that conservative aliases are respected.

    Returns one of: "sales" | "accident" | "hr" | "finance" | "healthcare" | "generic"
    """
    cols = {_normalise_name(c) for c in df.columns}
    joined = " ".join(cols)

    # Sales: must have at least one of these explicitly sales-oriented columns
    sales_signals = {"sales", "revenue", "profit", "order_id", "order_date"}
    if cols & sales_signals:
        return "sales"

    # Accident / public-safety
    accident_signals = ("accident", "casualt", "incident", "severity",
                        "fatal", "injur", "crash", "collision")
    if any(signal in joined for signal in accident_signals):
        return "accident"

    # HR / People
    hr_signals = ("salary", "employee", "hire_date",
                  "department", "headcount", "attrition", "payroll")
    if any(signal in joined for signal in hr_signals):
        return "hr"

    # Finance / Stock
    finance_signals = ("ticker", "stock", "market_cap", "share_price")
    if any(signal in joined for signal in finance_signals):
        return "finance"

    # Healthcare
    health_signals = ("patient", "diagnosis", "treatment", "hospital",
                      "procedure", "medication", "discharge")
    if any(signal in joined for signal in health_signals):
        return "healthcare"

    return "generic"


def _normalise_name(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_")


def get_missing_warnings(df: pd.DataFrame) -> list[str]:
    """
    Return honest warnings about what standard columns are ABSENT
    after conservative mapping.  Only warn about columns that would
    actually disable a feature.
    """
    cols = set(df.columns.tolist())
    warnings: list[str] = []

    if "Sales" not in cols and "Profit" not in cols:
        warnings.append(
            "No revenue or profit column detected — "
            "KPI cards will show generic numeric summaries instead of financial KPIs."
        )
    if "Order Date" not in cols:
        # Check whether any datetime column exists at all
        has_any_date = any(
            pd.api.types.is_datetime64_any_dtype(df[c]) for c in df.columns
        )
        if has_any_date:
            warnings.append(
                "Date column not mapped to 'Order Date' — "
                "time-based filters use the first detected datetime column."
            )
        else:
            warnings.append(
                "No date column detected — "
                "monthly trend chart and time-based filters will be unavailable."
            )
    if "Category" not in cols:
        warnings.append(
            "No 'Category' column detected — "
            "category breakdown chart and filter will use the first text column found."
        )
    if "Region" not in cols:
        warnings.append(
            "No 'Region' column detected — "
            "regional chart and filter will be unavailable."
        )
    return warnings


def build_chatbot_suggestions(df: pd.DataFrame) -> list[str]:
    """
    Generate relevant quick-ask suggestions based on columns ACTUALLY present.
    Never suggests sales questions if there is no sales column.
    """
    cols = set(df.columns.tolist())
    num_cols = df.select_dtypes(include="number").columns.tolist()
    suggestions: list[str] = []

    # Universal
    suggestions.append("How many records are in this dataset?")
    suggestions.append("What columns does this dataset have?")

    # Sales-specific — only if sales columns exist
    if "Sales" in cols:
        suggestions.append("What is the total sales/revenue?")
        suggestions.append("Which category has the highest sales?")
    if "Profit" in cols:
        suggestions.append("What is the total profit?")
        suggestions.append("What is the profit margin?")
    if "Region" in cols:
        suggestions.append("Which region has the highest total?")
    if "Order Date" in cols:
        suggestions.append("Show the monthly trend.")
        suggestions.append("Which month had the highest volume?")
    if "Category" in cols:
        suggestions.append("Show me the top categories.")

    # Generic numeric suggestions — only when no sales columns found
    if "Sales" not in cols and num_cols:
        first = num_cols[0]
        suggestions.append(f"What is the average {first}?")
        suggestions.append(f"What is the maximum {first}?")
        if len(num_cols) > 1:
            suggestions.append(f"Show the distribution of {num_cols[1]}.")

    return suggestions[:6]
