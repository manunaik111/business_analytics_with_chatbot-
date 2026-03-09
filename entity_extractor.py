import re
from thefuzz import process

METRICS = ["sales", "revenue", "profit"]
REGIONS = ["north", "south", "east", "west"]

def extract_entities(query, product_list):
    query = query.lower()
    
    years = re.findall(r'\b20\d{2}\b', query)
    found_metrics = [m for m in METRICS if m in query]
    found_regions = [r for r in REGIONS if r in query]
    top_n = re.findall(r'top\s?(\d+)', query)
    
    words = query.split()
    found_products = []
    for word in words:
        match, score = process.extractOne(word, product_list)
        if score > 85:
            found_products.append(match)

    # NEW: The Safety Net
    has_results = any([years, found_metrics, found_regions, found_products])

    return {
        "found_anything": has_results,
        "years": years,
        "top_n": top_n[0] if top_n else None,
        "metrics": found_metrics,
        "regions": found_regions,
        "products": list(set(found_products))
    }