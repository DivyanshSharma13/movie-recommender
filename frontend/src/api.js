const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function get(path, params = {}) {
  const url = new URL(path, API_BASE);
  Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  const res = await fetch(url);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export const api = {
  searchTitles: (q, limit = 8) => get("/api/titles", { q, limit }),
  recommend: (title, { n = 15, alpha = 0.7, minVotes = 20 } = {}) =>
    get("/api/recommend", { title, n, alpha, min_votes: minVotes }),
  movieDetail: (title) => get(`/api/movie/${encodeURIComponent(title)}`),
};