import pandas as pd

from nlp.modules.data_quality import analyze_quality
from nlp.modules.dataset_profiling import generate_profile


def _column_map(df: pd.DataFrame) -> dict:
    return {
        c.lower().replace(" ", "").replace("-", "").replace("_", ""): c
        for c in df.columns
    }


def _resolve_column(df: pd.DataFrame, parsed_query: dict) -> str | None:
    if parsed_query.get("column") in df.columns:
        return parsed_query["column"]

    metric = parsed_query.get("metric")
    if not metric:
        return None

    if metric in df.columns:
        return metric

    key = str(metric).lower().replace(" ", "").replace("-", "").replace("_", "")
    col_map = _column_map(df)
    if key in col_map:
        return col_map[key]

    for short, full in col_map.items():
        if key in short or short in key:
            return full
    return None


def _first_datetime_column(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return col
    return None


def _first_numeric_column(df: pd.DataFrame) -> str | None:
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    return numeric_cols[0] if numeric_cols else None


def execute_query(df: pd.DataFrame, parsed_query: dict) -> dict:
    """Apply parsed NLP instructions to the active dataset safely and honestly."""
    filters = parsed_query.get("filters", {})
    metric = parsed_query.get("metric")
    operation = parsed_query.get("operation")
    intent = parsed_query.get("intent")

    result = {"status": "success", "data": None, "message": "", "kind": intent}
    filtered_df = df.copy()
    col_map = _column_map(filtered_df)
    explicit_metric = bool(parsed_query.get("column") or parsed_query.get("metric"))

    if "year" in filters:
        yr = str(filters["year"])
        if "Order Date" in filtered_df.columns:
            filtered_df = filtered_df[
                pd.to_datetime(filtered_df["Order Date"], errors="coerce").dt.year.astype(str) == yr
            ]
        elif "year" in col_map:
            filtered_df = filtered_df[filtered_df[col_map["year"]].astype(str) == yr]
        else:
            date_col = _first_datetime_column(filtered_df)
            if date_col:
                filtered_df = filtered_df[
                    pd.to_datetime(filtered_df[date_col], errors="coerce").dt.year.astype(str) == yr
                ]

    if "region" in filters:
        region_col = "Region" if "Region" in filtered_df.columns else col_map.get("region")
        if region_col:
            series = filtered_df[region_col].astype(str).str.lower()
            filtered_df = filtered_df[series == str(filters["region"]).lower()]

    if filtered_df.empty:
        result["message"] = f"No data found for the applied filters: {filters}"
        return result

    if intent == "profiling":
        profile = generate_profile(filtered_df)
        profile["kind"] = "profiling"
        return profile

    if intent == "quality":
        quality = analyze_quality(filtered_df)
        quality["kind"] = "quality"
        return quality

    if intent == "schema":
        numeric_cols = filtered_df.select_dtypes(include="number").columns.tolist()
        date_cols = [c for c in filtered_df.columns if pd.api.types.is_datetime64_any_dtype(filtered_df[c])]
        categorical_cols = [
            c for c in filtered_df.columns
            if c not in numeric_cols and c not in date_cols
        ]
        result["data"] = {
            "columns": filtered_df.columns.tolist(),
            "numeric_columns": numeric_cols,
            "date_columns": date_cols,
            "categorical_columns": categorical_cols,
        }
        result["message"] = "Listed dataset columns."
        return result

    if metric and str(metric).lower() in ("records", "rows", "count"):
        result["data"] = len(filtered_df)
        result["message"] = f"Total records: {len(filtered_df)}"
        result["kind"] = "aggregation"
        return result

    target_col = _resolve_column(filtered_df, parsed_query)

    if target_col is None:
        if operation in {"average", "sum", "min", "max"}:
            numeric_cols = filtered_df.select_dtypes(include="number").columns.tolist()
            if explicit_metric:
                requested = parsed_query.get("column") or parsed_query.get("metric") or "that field"
                result["status"] = "error"
                result["message"] = (
                    f"I could not find a matching column for '{requested}' in this dataset. "
                    f"Available numeric columns: {', '.join(numeric_cols[:8]) or 'none'}."
                )
                return result

            result["status"] = "error"
            result["message"] = (
                "Please mention which numeric column you want to analyze. "
                f"Available numeric columns: {', '.join(numeric_cols[:8]) or 'none'}."
            )
            return result

        result["data"] = filtered_df
        result["message"] = "I could not match a specific metric column, so I am using the filtered dataset summary."
        return result

    result["data"] = filtered_df
    result["target_column"] = target_col

    if operation and operation != "count":
        if not pd.api.types.is_numeric_dtype(filtered_df[target_col]):
            result["status"] = "error"
            result["message"] = f"The column '{target_col}' is not numeric, so I cannot calculate {operation}."
            result["data"] = None
            return result

    if intent == "aggregation" and operation:
        ops = {
            "sum": filtered_df[target_col].sum(),
            "average": filtered_df[target_col].mean(),
            "min": filtered_df[target_col].min(),
            "max": filtered_df[target_col].max(),
            "count": len(filtered_df),
        }
        val = ops.get(operation)
        if val is not None:
            result["data"] = val
            result["message"] = f"Calculated {operation} for {target_col}."
            return result

    result["message"] = f"Filtered data ready using column '{target_col}'."
    return result
