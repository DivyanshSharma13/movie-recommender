import { useEffect, useRef, useState } from "react";
import { api } from "../api";

export default function SearchBar({ onSelect }) {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const debounceRef = useRef(null);
  const skipNextFetch = useRef(false);
  const containerRef = useRef(null);
  const itemRefs = useRef([]);

  useEffect(() => {
    if (skipNextFetch.current) {
      skipNextFetch.current = false;
      return;
    }
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!query.trim()) {
      setSuggestions([]);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      try {
        const data = await api.searchTitles(query);
        setSuggestions(data.results);
        setActiveIndex(-1);
        setOpen(data.results.length > 0);
      } catch {
        setSuggestions([]);
      }
    }, 250);
    return () => clearTimeout(debounceRef.current);
  }, [query]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (activeIndex >= 0 && itemRefs.current[activeIndex]) {
      itemRefs.current[activeIndex].scrollIntoView({ block: "nearest" });
    }
  }, [activeIndex]);

  const pick = (title) => {
    skipNextFetch.current = true;
    setQuery(title);
    setOpen(false);
    setActiveIndex(-1);
    onSelect(title);
  };

  const handleKeyDown = (e) => {
    if (!open || suggestions.length === 0) {
      if (e.key === "Enter" && query.trim()) pick(query.trim());
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => (i + 1) % suggestions.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => (i <= 0 ? suggestions.length - 1 : i - 1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      pick(activeIndex >= 0 ? suggestions[activeIndex] : query.trim());
    } else if (e.key === "Escape") {
      setOpen(false);
      setActiveIndex(-1);
    }
  };

  return (
    <div className="search-bar" ref={containerRef}>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => suggestions.length && setOpen(true)}
        onKeyDown={handleKeyDown}
        placeholder="Search a movie you like (e.g. Avatar)..."
      />
      {open && suggestions.length > 0 && (
        <ul className="suggestions">
          {suggestions.map((title, i) => (
            <li
              key={title}
              ref={(el) => (itemRefs.current[i] = el)}
              className={i === activeIndex ? "active" : ""}
              onMouseEnter={() => setActiveIndex(i)}
              onClick={() => pick(title)}
            >
              {title}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}