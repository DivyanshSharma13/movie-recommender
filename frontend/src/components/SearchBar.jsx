import { useEffect, useRef, useState } from "react";
import { api } from "../api";

export default function SearchBar({ onSelect }) {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [open, setOpen] = useState(false);
  const debounceRef = useRef(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!query.trim()) {
      setSuggestions([]);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      try {
        const data = await api.searchTitles(query);
        setSuggestions(data.results);
        setOpen(true);
      } catch {
        setSuggestions([]);
      }
    }, 250); // debounce so we don't hit the API on every keystroke
    return () => clearTimeout(debounceRef.current);
  }, [query]);

  const pick = (title) => {
    setQuery(title);
    setOpen(false);
    onSelect(title);
  };

  return (
    <div className="search-bar">
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => suggestions.length && setOpen(true)}
        onKeyDown={(e) => e.key === "Enter" && query.trim() && pick(query.trim())}
        placeholder="Search a movie you like (e.g. Avatar)..."
      />
      {open && suggestions.length > 0 && (
        <ul className="suggestions">
          {suggestions.map((title) => (
            <li key={title} onClick={() => pick(title)}>
              {title}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
