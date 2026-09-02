import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from concurrent.futures import ThreadPoolExecutor

from app import recommender
from app.tmdb import fetch_movie_details

app = FastAPI(title="Movie Recommender API", version="2.0")

allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

_executor = ThreadPoolExecutor(max_workers=8)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "movies_loaded": len(recommender.df),
        "embedding_method_available": recommender.EMBEDDINGS_AVAILABLE,
    }


@app.get("/api/titles")
def titles(q: str = Query(..., min_length=1), limit: int = 10):
    return {"results": recommender.search_titles(q, limit=limit)}


@app.get("/api/recommend")
def recommend(
    title: str,
    n: int = 15,
    alpha: float = 0.7,
    min_votes: int = 20,
    enrich: bool = True,
    method: str = "tfidf",
):
    try:
        results = recommender.recommend(title, n=n, alpha=alpha, min_votes=min_votes, method=method)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if enrich and results:
        titles_to_fetch = [r["title"] for r in results]
        details = list(_executor.map(fetch_movie_details, titles_to_fetch))
        for r, d in zip(results, details):
            r["poster_url"] = d["poster_url"]
            r["tmdb_overview"] = d["overview"]
            r["release_date"] = d["release_date"]
            r["tmdb_rating"] = d["tmdb_rating"]

    return {"query": title, "method": method, "count": len(results), "results": results}


@app.get("/api/movie/{title}")
def movie_detail(title: str):
    if title not in recommender.indices:
        raise HTTPException(status_code=404, detail=f"'{title}' not found")
    row = recommender.df.loc[recommender.indices[title]]
    details = fetch_movie_details(title)
    return {
        "title": row["title"],
        "genres": row["genres"],
        "overview": row["overview"],
        "vote_average": float(row["vote_average"]),
        "vote_count": int(row["vote_count"]),
        **details,
    }
