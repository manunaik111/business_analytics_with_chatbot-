import json
from nlp.entity_extractor import extract_entities
from nlp.intent_classifier import predict_intent

def parse_query(query, product_list):

    entities = extract_entities(query, product_list)

    # use your ML model
    intent = predict_intent(query)

    output = {
        "status": "success",
        "intent": intent,
        "data_filters": entities
    }

    return json.dumps(output, indent=4)


if __name__ == "__main__":

    test_products = ["laptop", "smartphone", "tablet"]

    user_input = input("Enter your query: ")

    result = parse_query(user_input, test_products)

    print(result)

    with open("output.json", "w") as f:
        f.write(result)

    print("\nOutput saved to output.json")