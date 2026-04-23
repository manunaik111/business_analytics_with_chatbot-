def generate_ai_insights(kpis):
    """Generate lightweight KPI-based insights for sales-compatible datasets."""
    insights = []

    total_profit = float(kpis.get("total_profit", 0) or 0)
    avg_discount = float(kpis.get("avg_discount", 0) or 0)
    avg_shipping_delay = float(kpis.get("avg_shipping_delay", 0) or 0)
    unique_customers = int(kpis.get("unique_customers", 0) or 0)
    avg_order_value = float(kpis.get("avg_order_value", 0) or 0)
    total_sales = float(kpis.get("total_sales", 0) or 0)
    total_orders = int(kpis.get("total_orders", 0) or 0)

    if total_profit < 0:
        insights.append("Overall profit is negative, so margin recovery needs attention.")
    elif total_profit > 0:
        insights.append("Overall profit is positive across the filtered dataset.")

    if avg_discount > 0.2:
        insights.append("High discounting may be compressing margins.")
    elif avg_discount > 0.1:
        insights.append("Discount usage is moderate and worth monitoring by segment.")

    if avg_shipping_delay > 5:
        insights.append("Average shipping delay is above five days.")

    if unique_customers > 500:
        insights.append("The dataset shows a broad customer base.")

    if avg_order_value > 400:
        insights.append("Average order value is relatively high.")

    if total_sales > 0 and total_orders > 0 and not insights:
        insights.append("Sales activity is present, but no strong KPI outlier was detected.")

    return insights
