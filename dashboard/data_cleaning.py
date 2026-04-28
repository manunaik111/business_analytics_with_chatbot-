"""data_cleaning.py — Automated data cleaning with detailed report."""
import pandas as pd
import numpy as np

_LAST_REPORT: dict = {}

def _any_date_hints(col_name: str, sample_val) -> bool:
    if any(k in col_name.lower() for k in ["date", "time", "year", "month", "day"]):
        return True
    try:
        pd.to_datetime([sample_val])
        return True
    except Exception:
        return False

def clean_data(df: pd.DataFrame):
    global _LAST_REPORT
    if df is None or df.empty:
        return df, {}

    cleaned = df.copy()
    report = {
        "initial_rows": len(cleaned),
        "initial_cols": len(cleaned.columns),
        "duplicates_removed": 0,
        "missing_filled": int(cleaned.isnull().sum().sum()),
        "date_conversions": [],
        "numeric_conversions": [],
    }

    # Remove duplicates
    dupes = int(cleaned.duplicated().sum())
    if dupes > 0:
        cleaned.drop_duplicates(inplace=True)
        report["duplicates_removed"] = dupes

    # Fill missing values
    for col in cleaned.columns:
        if cleaned[col].isnull().any():
            if pd.api.types.is_numeric_dtype(cleaned[col]):
                med = cleaned[col].median()
                cleaned[col].fillna(0 if pd.isna(med) else med, inplace=True)
            else:
                mode_vals = cleaned[col].mode()
                cleaned[col].fillna(
                    mode_vals.iloc[0] if not mode_vals.empty else "Unknown",
                    inplace=True,
                )

    # Auto-convert date columns
    for col in cleaned.select_dtypes(include=["object"]).columns:
        if cleaned[col].nunique() > 1:
            try:
                sample = cleaned[col].dropna().iloc[0]
                if isinstance(sample, str) and _any_date_hints(col, sample):
                    converted = pd.to_datetime(cleaned[col], errors="coerce")
                    if converted.notna().sum() > 0.8 * len(cleaned):
                        cleaned[col] = converted
                        report["date_conversions"].append(col)
                        continue
            except Exception:
                pass
            # Try numeric conversion
            try:
                temp = pd.to_numeric(cleaned[col], errors="coerce")
                if temp.notna().sum() / len(temp) > 0.5:
                    med = temp.median()
                    cleaned[col] = temp.fillna(0 if pd.isna(med) else med)
                    report["numeric_conversions"].append(col)
            except Exception:
                pass

    report["cleaned_rows"] = len(cleaned)
    _LAST_REPORT = report
    return cleaned, report

def get_cleaning_report() -> dict:
    return _LAST_REPORT.copy()
