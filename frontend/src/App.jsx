import { useState } from "react";
import SearchBar from "./components/SearchBar";
import MovieCard from "./components/MovieCard";
import { api } from "./api";
import "./App.css";

// Fixed blend: 70% text similarity, 30% quality score. Not exposed in the UI --
// keeps the app simple to demo (search a movie, get recommendations) while the
// backend still does the same hybrid ranking under the hood.
const ALPHA = 0.85;

export default function App() {
  const [selectedTitle, setSelectedTitle] = useState(null);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const runSearch = async (title) => {
    setSelectedTitle(title);
    setLoading(true);
    setError(null);
    try {
      const data = await api.recommend(title, { n: 15, alpha: ALPHA });
      setResults(data.results);
    } catch (e) {
      setError(e.message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="hero">
        <div className="hero-glow" />
        <p className="eyebrow">Content-based recommender</p>
        <h1>Find your next favorite movie</h1>
        <p className="subtitle">
          Search a movie you love — we'll match it by story and genre.
        </p>
        <SearchBar onSelect={(title) => runSearch(title)} />
      </header>

      {error && <p className="status error">{error}</p>}

      {loading && (
        <div className="movie-grid">
          {Array.from({ length: 10 }).map((_, i) => (
            <div className="movie-card skeleton" key={i}>
              <div className="skeleton-poster" />
              <div className="skeleton-line" />
              <div className="skeleton-line short" />
            </div>
          ))}
        </div>
      )}

      {!loading && results.length > 0 && (
        <>
          <h2>
            Because you liked <span className="highlight">{selectedTitle}</span>
          </h2>
          <div className="movie-grid">
            {results.map((movie, i) => (
              <MovieCard key={movie.title} movie={movie} rank={i + 1} />
            ))}
          </div>
        </>
      )}

      {!loading && !error && selectedTitle && results.length === 0 && (
        <p className="status">No recommendations found for that title.</p>
      )}

      {!selectedTitle && (
        <p className="status hint">Try searching "Avatar", "Inception", or "The Matrix" to start.</p>
      )}
    </div>
  );
}