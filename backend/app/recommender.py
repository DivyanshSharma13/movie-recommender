"""
Loads the artifacts produced by train_model.py once at startup and
exposes the hybrid recommend() function.
"""
import pickle
from pathlib import Path

import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

MODEL_DIR = Path(__file__).parent.parent / "model"

df: pd.DataFrame = pd.read_pickle(MODEL_DIR / "df.pkl")
tfidf = pickle.load(open(MODEL_DIR / "tfidf.pkl", "rb"))
tfidf_matrix = pickle.load(open(MODEL_DIR / "tfidf_matrix.pkl", "rb"))
indices: pd.Series = pickle.load(open(MODEL_DIR / "indices.pkl", "rb"))

ALL_TITLES = sorted(df["title"].dropna().unique().tolist())


def search_titles(query: str, limit: int = 10) -> list[str]:
    q = query.strip().lower()
    if not q:
        return []
    starts = [t for t in ALL_TITLES if t.lower().startswith(q)]
    contains = [t for t in ALL_TITLES if q in t.lower() and t not in starts]
    return (starts + contains)[:limit]


def recommend(title: str, n: int = 15, alpha: float = 0.7, min_votes: int = 20):
    if title not in indices:
        raise ValueError(f"'{title}' not found in the dataset")

    idx = indices[title]
    if isinstance(idx, pd.Series):
        idx = idx.iloc[0]

    query_genres = set(df.loc[idx, "genres"].split())
    query_language = df.loc[idx, "original_language"]

    sim_scores = cosine_similarity(tfidf_matrix[idx], tfidf_matrix).flatten()

    candidates = df.copy()
    candidates["sim_score"] = sim_scores
    candidates = candidates[candidates.index != idx]
    candidates = candidates[candidates["vote_count"] >= min_votes]
    candidates = candidates[candidates["sim_score"] > 0]

    if candidates.empty:
        return []

    sim_norm = (candidates["sim_score"] - candidates["sim_score"].min()) / (
        candidates["sim_score"].max() - candidates["sim_score"].min() + 1e-9
    )
    wr_norm = (candidates["weighted_rating"] - candidates["weighted_rating"].min()) / (
        candidates["weighted_rating"].max() - candidates["weighted_rating"].min() + 1e-9
    )
    genre_bonus = candidates["genres"].apply(
        lambda g: len(query_genres & set(g.split())) / max(len(query_genres), 1)
    ) * 0.15
    language_bonus = (candidates["original_language"] == query_language).astype(float) * 0.20

    candidates["final_score"] = alpha * sim_norm + (1 - alpha) * wr_norm + genre_bonus + language_bonus

    top = candidates.sort_values("final_score", ascending=False).head(n)

    return [
        {
            "title": row["title"],
            "genres": row["genres"],
            "overview": row["overview"],
            "vote_average": float(row["vote_average"]),
            "vote_count": int(row["vote_count"]),
            "original_language": row["original_language"],
            "final_score": round(float(row["final_score"]), 4),
        }
        for _, row in top.iterrows()
    ]
