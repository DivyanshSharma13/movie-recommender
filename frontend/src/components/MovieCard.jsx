const PLACEHOLDER =
  "data:image/svg+xml;utf8," +
  encodeURIComponent(
    "<svg xmlns='http://www.w3.org/2000/svg' width='300' height='450'>" +
      "<rect width='100%' height='100%' fill='#1a1c27'/>" +
      "<text x='50%' y='50%' fill='#555' font-family='sans-serif' font-size='16' " +
      "text-anchor='middle' dominant-baseline='middle'>No poster</text>" +
      "</svg>"
  );

export default function MovieCard({ movie, rank }) {
  const rating = movie.tmdb_rating ?? movie.vote_average;
  const overview = movie.tmdb_overview || movie.overview;
  const year = (movie.release_date || "").slice(0, 4);

  return (
    <div className="movie-card">
      <div className="poster-wrap">
        <img src={movie.poster_url || PLACEHOLDER} alt={movie.title} loading="lazy" />
        {rank && <span className="rank-badge">#{rank}</span>}
        {rating > 0 && <span className="rating-badge">★ {rating.toFixed(1)}</span>}
        <div className="poster-overlay">
          <p className="overview">{overview || "No description available."}</p>
        </div>
      </div>
      <div className="movie-card-body">
        <h3>{movie.title}</h3>
        <div className="movie-meta">
          {year && <span className="year">{year}</span>}
          <span className="genres">{movie.genres}</span>
        </div>
      </div>
    </div>
  );
}