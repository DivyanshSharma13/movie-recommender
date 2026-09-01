"""
Builds the model artifacts the API serves at runtime.
"""
import argparse
import ast
import re
import pickle
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS

MODEL_DIR = Path(__file__).parent / "model"


def preprocess_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-zA-Z\s]", "", text)
    words = [w for w in text.split() if w not in ENGLISH_STOP_WORDS]
    return " ".join(words)


def build(csv_path: str):
    df = pd.read_csv(csv_path, low_memory=False)
    df = df.drop_duplicates().reset_index(drop=True)
    df = df[["title", "overview", "genres", "tagline", "vote_average", "vote_count", "popularity", "original_language"]]
    df = df.dropna(subset=["title"])
    df["overview"] = df["overview"].fillna("")
    df["tagline"] = df["tagline"].fillna("")
    df["vote_average"] = df["vote_average"].fillna(0)
    df["vote_count"] = df["vote_count"].fillna(0)
    df["original_language"] = df["original_language"].fillna("unknown")
    df["genres"] = df["genres"].apply(
        lambda x: " ".join([i["name"] for i in ast.literal_eval(x)]) if pd.notna(x) else ""
    )
    df = df.reset_index(drop=True)

    df["tags"] = df["overview"] + " " + (df["genres"] + " ") * 3 + df["tagline"]
    df["tags"] = df["tags"].apply(preprocess_text)

    C = df["vote_average"].mean()
    m = df["vote_count"].quantile(0.90)

    def weighted_rating(row, m=m, C=C):
        v, R = row["vote_count"], row["vote_average"]
        return (v / (v + m) * R) + (m / (v + m) * C)

    df["weighted_rating"] = df.apply(weighted_rating, axis=1)

    by_votes = df.sort_values("vote_count", ascending=False)
    indices = pd.Series(by_votes.index, index=by_votes["title"])
    indices = indices[~indices.index.duplicated(keep="first")]

    tfidf = TfidfVectorizer(
        max_features=50000,
        ngram_range=(1, 2),
        stop_words="english",
        sublinear_tf=True,
        min_df=2,
        max_df=0.85,
    )
    tfidf_matrix = tfidf.fit_transform(df["tags"])

    MODEL_DIR.mkdir(exist_ok=True)
    df.to_pickle(MODEL_DIR / "df.pkl")
    pickle.dump(tfidf, open(MODEL_DIR / "tfidf.pkl", "wb"))
    pickle.dump(tfidf_matrix, open(MODEL_DIR / "tfidf_matrix.pkl", "wb"))
    pickle.dump(indices, open(MODEL_DIR / "indices.pkl", "wb"))

    print(f"Saved artifacts to {MODEL_DIR} ({len(df)} movies)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="movies_metadata.csv")
    args = parser.parse_args()
    build(args.csv)
