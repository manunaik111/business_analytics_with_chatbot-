import re
from thefuzz import process

METRICS = ["sales", "revenue", "profit"]
REGIONS = ["north", "south", "east", "west"]


def extract_entities(query, product_list):
    query = query.lower()
    words = query.split()

    # 1. Years — validated range (avoids matching random 20XX numbers in product names)
    all_years = re.findall(r'\b20\d{2}\b', query)
    years = [y for y in all_years if 2015 <= int(y) <= 2026]

    # 2. Metrics — fuzzy match so "sale" → "sales", "profitability" → "profit"
    found_metrics = []
    for word in words:
        if len(word) > 2:
            match, score = process.extractOne(word, METRICS)
            if score > 80:
                found_metrics.append(match)
    found_metrics = list(set(found_metrics))

    # 3. Regions — exact substring (region names are short and unambiguous)
    found_regions = [r for r in REGIONS if r in query]

    # 4. Top N — e.g. "top 5" or "top5"
    top_n = re.findall(r'top\s?(\d+)', query)

    # 5. Products — fuzzy match, only on words long enough to be meaningful
    found_products = []
    if product_list:
        for word in words:
            if len(word) > 3:                                    # skip short noise words
                match, score = process.extractOne(word, product_list)
                if score > 85:
                    found_products.append(match)
    found_products = list(set(found_products))

    # 6. Safety check
    has_results = any([years, found_metrics, found_regions, found_products])

    return {
        "found_anything": has_results,
        "years":          years,
        "top_n":          top_n[0] if top_n else None,
        "metrics":        found_metrics,
        "regions":        found_regions,
        "products":       found_products,
    }


# --- Quick test ---
if __name__ == "__main__":
    my_products = ["iPhone 15", "Samsung S23", "MacBook Air"]
    test_query = "What was the SALE for north in 2024?"
    print(extract_entities(test_query, my_products))
