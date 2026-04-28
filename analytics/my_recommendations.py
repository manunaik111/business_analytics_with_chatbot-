def generate_smart_recommendations(kpis):
    """Generate lightweight KPI-based recommendations for sales-compatible datasets."""
    recommendations = []

    avg_discount = float(kpis.get("avg_discount", 0) or 0)
    avg_shipping_delay = float(kpis.get("avg_shipping_delay", 0) or 0)
    total_profit = float(kpis.get("total_profit", 0) or 0)
    avg_order_value = float(kpis.get("avg_order_value", 0) or 0)
    unique_customers = int(kpis.get("unique_customers", 0) or 0)

    if avg_discount > 0.2:
        recommendations.append("Review discount levels to protect margins.")

    if avg_shipping_delay > 5:
        recommendations.append("Improve logistics or fulfillment to reduce shipping delays.")

    if total_profit > 0:
        recommendations.append("Scale the strongest-performing categories or regions based on current results.")
    elif total_profit < 0:
        recommendations.append("Investigate loss-making orders, categories, or discount patterns.")

    if avg_order_value > 400:
        recommendations.append("Test premium bundles or upsell offers to sustain high order value.")

    if unique_customers > 500:
        recommendations.append("Use retention campaigns or loyalty programs to keep repeat customers engaged.")

    return recommendations
