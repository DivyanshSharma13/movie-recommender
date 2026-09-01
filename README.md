# Movie Recommender — Full Stack

A content-based movie recommender (TF-IDF + hybrid quality ranking, from your
notebook) served as a real API, with a React frontend that shows posters and
descriptions pulled live from TMDB.

```
movie-recommender/
├── backend/            FastAPI service (the model + the API)
│   ├── app/
│   │   ├── main.py         API routes
│   │   ├── recommender.py  loads the model, hybrid recommend() logic
│   │   └── tmdb.py         TMDB poster/overview lookup
│   ├── model/               <- generated .pkl artifacts (not in git, see below)
│   ├── train_model.py      run once to build model/ from movies_metadata.csv
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
└── frontend/           React (Vite) app
    ├── src/
    │   ├── App.jsx
    │   ├── api.js           talks to the backend
    │   └── components/      SearchBar, MovieCard
    └── .env.example
```

**How the pieces connect:** the React app calls the FastAPI backend over
HTTP (`fetch`, using the URL in `VITE_API_URL`). The backend does the TF-IDF
similarity ranking itself (that's your model, nothing external), and for
each recommended title it separately calls the TMDB API to grab a poster
image and an up-to-date overview, then returns everything as one JSON
response. TMDB is *only* called by the backend — your API key never reaches
the browser.

---

## 1. Set up in VS Code

**Prerequisites:** Python 3.11+, Node.js 18+, and the CSV file
(`movies_metadata.csv`) you already have.

Open the `movie-recommender/` folder in VS Code (`File → Open Folder`). You'll
run two terminals side by side — VS Code's integrated terminal supports this
with the `+` split button (`` Ctrl+Shift+5 `` / `` Cmd+Shift+5 ``).

### Terminal 1 — backend

```bash
cd backend
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt

# copy your CSV in here (same folder as train_model.py), then:
python train_model.py --csv movies_metadata.csv

cp .env.example .env
# open .env and paste your real TMDB_API_KEY in
```

Get a free TMDB key at https://www.themoviedb.org/settings/api if you don't
already have one on hand — go to Settings → API → create a key ("Developer"
use is fine for this). **Treat it like a password**: it goes in `.env`
(already gitignored), never directly in code, never committed, never pasted
into a public issue/chat again once you've rotated it.

> You shared a key in our conversation — since it's now visible in chat
> history, it's good practice to regenerate/rotate it from your TMDB account
> settings before you rely on this in anything real.

Run the server:

```bash
uvicorn app.main:app --reload --port 8000
```

Check it's alive: open http://localhost:8000/api/health — you should see
`{"status":"ok","movies_loaded":45443}`. Interactive API docs (auto-generated
by FastAPI) are at http://localhost:8000/docs — useful for testing
`/api/recommend` by hand before touching the frontend.

### Terminal 2 — frontend

```bash
cd frontend
npm install
cp .env.example .env    # VITE_API_URL=http://localhost:8000 — already correct for local dev
npm run dev
```

Open the URL it prints (typically http://localhost:5173). Search a movie,
pick a suggestion, and you should see recommendation cards with posters.

**Recommended VS Code extensions:** Python (ms-python.python), Pylance,
ESLint, and Prettier — VS Code will usually prompt you to install these when
you open the respective folders.

---

## 2. How the recommend flow works, end to end

1. You type in the search box → frontend debounces (250ms) and calls
   `GET /api/titles?q=...` for autocomplete suggestions.
2. You pick a title → frontend calls
   `GET /api/recommend?title=...&n=12&alpha=0.7`.
3. Backend computes TF-IDF cosine similarity + weighted rating + genre bonus
   (same logic as your notebook) to get the top N titles.
4. Backend fires off parallel requests to TMDB's `search/movie` endpoint for
   each of those N titles, to get a poster URL and fresh overview.
5. Backend merges the local model output with the TMDB data and returns one
   JSON response.
6. Frontend renders `MovieCard`s. If TMDB has no match for a title, or the
   request fails, the card just falls back to the local overview and a
   placeholder image — nothing breaks.

The "Similarity vs. Popularity" slider in the UI directly controls `alpha` —
drag it and the same title re-queries with a different blend, so you can see
the ranking shift in real time.

---

## 3. Deploying it for real

**Backend → Render** (has a real free tier for small services like this):

1. Push `backend/` to a GitHub repo (root of the repo, or set Render's "Root
   Directory" to `backend` if you keep both folders in one repo).
2. On [render.com](https://render.com): New → Web Service → connect your repo.
3. Build command: `pip install -r requirements.txt && python train_model.py --csv movies_metadata.csv`
   — this means `movies_metadata.csv` needs to be in the repo too (or
   uploaded to Render's disk / pulled from cloud storage — a few hundred MB
   CSV in git isn't ideal long-term, but it's the simplest path to get
   deployed today).
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Environment → add `TMDB_API_KEY` (your real key) and `ALLOWED_ORIGINS`
   (set this to your Vercel frontend URL once you have it, e.g.
   `https://your-app.vercel.app` — comma-separate multiple origins).
6. Deploy. Note the URL Render gives you, e.g. `https://movie-rec-api.onrender.com`.

*(Docker alternative: `backend/Dockerfile` is ready to go if you'd rather
deploy as a container — Render, Fly.io, and Railway all support "deploy from
Dockerfile" directly. Same env vars apply. Note the Dockerfile expects
`model/` to already contain the `.pkl` files — run `train_model.py` locally
and either commit the output or add it as a build step.)*

**Frontend → Vercel:**

1. Push `frontend/` to GitHub (same repo is fine).
2. On [vercel.com](https://vercel.com): New Project → import the repo → set
   "Root Directory" to `frontend`.
3. Environment variable: `VITE_API_URL` = your Render backend URL from above.
4. Deploy. Vercel gives you a URL like `https://your-app.vercel.app`.
5. Go back to Render and set `ALLOWED_ORIGINS` to that exact URL (this is
   what stops random other sites from calling your API from a browser).

Once both are live, open the Vercel URL — that's your deployed app, frontend
talking to backend talking to TMDB.

**Free-tier gotcha:** Render's free web services spin down after inactivity
and take ~30-60s to wake up on the next request. Fine for a portfolio demo;
if that's annoying, Render's cheapest paid tier removes it.

---

## 4. What to tell me next

Some natural next steps, if you want to keep going:
- Collaborative filtering (needs `ratings.csv` from the same dataset) for
  actual personalization instead of "similar to one movie you picked."
- A "trending now" row on the homepage using TMDB's `/trending` endpoint,
  independent of any search.
- User accounts + watchlist (would need a real database — Postgres via
  Render or Supabase).
- Caching TMDB responses in Redis instead of the in-memory dict, so it
  survives restarts and works across multiple backend instances.
