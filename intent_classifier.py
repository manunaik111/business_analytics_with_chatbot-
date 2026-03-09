from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from training_data import queries, intents

vectorizer = TfidfVectorizer()

X = vectorizer.fit_transform(queries)

model = LogisticRegression()
model.fit(X, intents)


def predict_intent(query):
    q = vectorizer.transform([query])
    return model.predict(q)[0]