import pandas as pd


def _format_value(value, target_column: str | None = None) -> str:
    try:
        val = float(value)
        is_money = target_column in {"Sales", "Profit", "Revenue"}
        if val == int(val) and abs(val) < 1_000_000:
            return f"${int(val):,}" if is_money else f"{int(val):,}"
        return f"${val:,.2f}" if is_money else f"{val:,.2f}"
    except (TypeError, ValueError):
        return str(value)


def generate_response(parsed_query: dict, processed_data: dict) -> str:
    """Convert processed NLP output into a concise, truthful chat reply."""
    if processed_data.get("status") == "error":
        return processed_data.get("message", "I could not complete that request.")

    data = processed_data.get("data")
    intent = processed_data.get("kind") or parsed_query.get("intent")
    message = processed_data.get("message", "")
    target_column = processed_data.get("target_column") or parsed_query.get("column") or parsed_query.get("metric")
    operation = (parsed_query.get("operation") or "").title()

    if data is None:
        return message or "I couldn't find matching data for that request."

    if intent == "profiling" and isinstance(data, dict):
        return (
            f"Dataset profile ready: {data.get('total_rows', 0):,} rows, "
            f"{data.get('total_cols', 0)} columns, and "
            f"{len(data.get('types', {}))} typed fields."
        )

    if intent == "quality" and isinstance(data, dict):
        return (
            f"Quality report ready: score {data.get('score', 'N/A')}, "
            f"{data.get('missing_total', 0)} missing cells, and "
            f"{data.get('duplicate_rows', 0)} duplicate rows."
        )

    if intent == "schema" and isinstance(data, dict):
        cols = data.get("columns", [])
        preview = ", ".join(cols[:8])
        suffix = "..." if len(cols) > 8 else ""
        return f"This dataset has {len(cols)} columns: {preview}{suffix}"

    if not isinstance(data, pd.DataFrame):
        formatted = _format_value(data, str(target_column) if target_column else None)
        if operation:
            return f"The {operation.lower()} for {target_column or 'the requested field'} is {formatted}."
        return f"The requested value is {formatted}."

    rows = len(data)
    if intent == "trend":
        return f"I found {rows:,} records for the trend request. {message}".strip()
    if intent == "comparison":
        return f"I found {rows:,} records for the comparison request. {message}".strip()
    if intent == "aggregation":
        return f"I found {rows:,} matching records. {message}".strip()

    return message or f"I found {rows:,} records matching your query."
