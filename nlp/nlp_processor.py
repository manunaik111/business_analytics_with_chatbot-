import os
import pickle
import re
from typing import Optional

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(_DIR, "intent_classifier.pkl")
VECTORIZER_PATH = os.path.join(_DIR, "tfidf_vectorizer.pkl")


def train_and_load_model():
    """Load the cached intent classifier or train a lightweight fallback model."""
    if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
        try:
            with open(MODEL_PATH, "rb") as model_file:
                clf = pickle.load(model_file)
            with open(VECTORIZER_PATH, "rb") as vec_file:
                vectorizer = pickle.load(vec_file)
            return clf, vectorizer
        except Exception:
            pass

    dataset = [
        ("summarize the data", "profiling"),
        ("show me statistics", "profiling"),
        ("describe the dataset", "profiling"),
        ("what are the data types", "profiling"),
        ("give me a profile of this data", "profiling"),
        ("what columns are present", "profiling"),
        ("are there any missing values", "quality"),
        ("find duplicates in the data", "quality"),
        ("what is the data quality score", "quality"),
        ("detect outliers", "quality"),
        ("check data quality", "quality"),
        ("how did sales change over the years", "trend"),
        ("show me the monthly trend", "trend"),
        ("plot the progression over time", "trend"),
        ("compare the performance across regions", "comparison"),
        ("show the differences between sectors", "comparison"),
        ("comparison matrix", "comparison"),
        ("what is the total value", "aggregation"),
        ("give me the exact number", "aggregation"),
        ("calculate the average", "aggregation"),
        ("find the maximum", "aggregation"),
        ("count the records", "aggregation"),
        ("how many rows", "aggregation"),
    ]

    df = pd.DataFrame(dataset, columns=["Text", "Intent"])
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    X = vectorizer.fit_transform(df["Text"])

    clf = MultinomialNB()
    clf.fit(X, df["Intent"])

    with open(MODEL_PATH, "wb") as model_file:
        pickle.dump(clf, model_file)
    with open(VECTORIZER_PATH, "wb") as vec_file:
        pickle.dump(vectorizer, vec_file)

    return clf, vectorizer


pipeline_clf, pipeline_vec = train_and_load_model()


def classify_intent_nlp(query: str) -> str:
    X_query = pipeline_vec.transform([query.lower()])
    prediction = pipeline_clf.predict(X_query)
    return prediction[0]


def _normalise(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(text).lower())


def _find_column_match(query: str, df: Optional[pd.DataFrame]) -> Optional[str]:
    if df is None or df.empty:
        return None

    query_norm = _normalise(query)
    if not query_norm:
        return None

    matches: list[tuple[int, str]] = []
    for col in df.columns:
        col_norm = _normalise(col)
        if not col_norm:
            continue
        if col_norm in query_norm:
            matches.append((len(col_norm), col))

    if matches:
        matches.sort(reverse=True)
        return matches[0][1]
    return None


def process_query(query: str, df: Optional[pd.DataFrame] = None, dataset_meta: Optional[dict] = None) -> dict:
    """Parse a user query using both the ML classifier and live dataset context."""
    query_lower = query.lower().strip()
    dataset_meta = dataset_meta or {}
    result = {
        "intent": classify_intent_nlp(query),
        "filters": {},
        "metric": None,
        "operation": None,
        "column": None,
        "dataset_type": dataset_meta.get("dataset_type", "generic"),
    }

    if any(phrase in query_lower for phrase in ("what columns", "which columns", "list columns", "dataset columns", "fields")):
        result["intent"] = "schema"
    elif any(phrase in query_lower for phrase in ("how many records", "how many rows", "row count", "number of records", "number of rows")):
        result["intent"] = "aggregation"
        result["metric"] = "records"
        result["operation"] = "count"
    elif any(phrase in query_lower for phrase in ("missing", "null", "duplicate", "quality", "outlier")):
        result["intent"] = "quality"
    elif any(phrase in query_lower for phrase in ("profile", "summary", "summarize", "describe", "statistics", "data types")):
        result["intent"] = "profiling"

    operations = {
        "average": "average", "avg": "average", "mean": "average",
        "sum": "sum", "total": "sum",
        "max": "max", "highest": "max", "largest": "max",
        "min": "min", "lowest": "min", "smallest": "min",
        "count": "count",
    }
    for word, op in operations.items():
        if re.search(rf"\b{word}\b", query_lower):
            result["operation"] = op
            break

    metric_aliases = {
        "sales": "Sales",
        "revenue": "Sales",
        "profit": "Profit",
        "orders": "Order ID",
        "order": "Order ID",
        "region": "Region",
        "category": "Category",
        "date": "Order Date",
    }
    for alias, metric in metric_aliases.items():
        if re.search(rf"\b{alias}\b", query_lower):
            result["metric"] = metric
            break

    matched_column = _find_column_match(query, df)
    if matched_column:
        result["column"] = matched_column
        if result["metric"] is None:
            result["metric"] = matched_column

    regions = ["north", "south", "east", "west", "usa", "europe", "asia", "uk", "india"]
    for region in regions:
        if re.search(rf"\b{region}\b", query_lower):
            result["filters"]["region"] = region
            break

    year_match = re.search(r"\b(20\d{2})\b", query_lower)
    if year_match:
        result["filters"]["year"] = year_match.group(1)

    return result
