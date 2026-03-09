# from intent_classifier import predict_intent

# query = input("Enter your question: ")

# intent = predict_intent(query)

# print("Predicted Intent:", intent)

from intent_classifier import predict_intent

tests = [
"show total sales",
"predict next month sales",
"compare east and west region",
"top 5 products by revenue",
"forecast sales next quarter"
]

for q in tests:
    print(q, "->", predict_intent(q))