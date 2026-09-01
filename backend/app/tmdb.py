"""
Thin wrapper around the TMDB (The Movie Database) v3 API.

Used to enrich a title from our local model with a poster image, a
polished overview, and current rating info -- things the 1990s-2017
snapshot in movies_metadata.csv doesn't reliably have for newer titles.

Docs: https://developer.themoviedb.org/reference/search-movie
"""
import os
import time
import requests

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

# Simple in-memory cache so the same title isn't looked up on every request.
# Fine for a single-process demo deploy; swap for Redis if you scale this out.
_cache: dict[str, dict] = {}
_CACHE_TTL_SECONDS = 60 * 60 * 12  # 12h


def _cache_get(key: str):
    hit = _cache.get(key)
    if not hit:
        return None
    if time.time() - hit["_ts"] > _CACHE_TTL_SECONDS:
        _cache.pop(key, None)
        return None
    return hit["data"]


def _cache_set(key: str, data: dict):
    _cache[key] = {"data": data, "_ts": time.time()}


def fetch_movie_details(title: str) -> dict:
    """
    Looks up `title` on TMDB and returns poster/overview/rating info.
    Always returns a dict (with poster_url=None etc.) instead of raising,
    so a TMDB outage or an unmatched title never breaks a recommendation
    response -- it just falls back to whatever the local dataset has.
    """
    cached = _cache_get(title)
    if cached is not None:
        return cached

    result = {
        "tmdb_id": None,
        "poster_url": None,
        "overview": None,
        "release_date": None,
        "tmdb_rating": None,
    }

    if not TMDB_API_KEY:
        return result

    try:
        resp = requests.get(
            f"{TMDB_BASE_URL}/search/movie",
            params={"api_key": TMDB_API_KEY, "query": title, "include_adult": "false"},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results") or []
        if results:
            best = results[0]
            result["tmdb_id"] = best.get("id")
            result["overview"] = best.get("overview") or None
            result["release_date"] = best.get("release_date") or None
            result["tmdb_rating"] = best.get("vote_average")
            poster_path = best.get("poster_path")
            if poster_path:
                result["poster_url"] = f"{TMDB_IMAGE_BASE}{poster_path}"
    except requests.RequestException:
        # Network hiccup / TMDB down -- degrade gracefully, don't 500 the API.
        pass

    _cache_set(title, result)
    return result
