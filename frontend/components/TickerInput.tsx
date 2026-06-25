"use client";

import { useEffect, useId, useRef, useState } from "react";
import { searchTickers, type Company } from "../lib/tickers";

type TickerInputProps = {
  selected: Company | null;
  onSelect: (company: Company | null) => void;
};

const DEBOUNCE_MS = 180;

export default function TickerInput({ selected, onSelect }: TickerInputProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Company[]>([]);
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  const listboxId = useId();
  const containerRef = useRef<HTMLDivElement>(null);

  // Debounced, cancellable search against the backend as the user types.
  useEffect(() => {
    const trimmed = query.trim();
    // When the box mirrors the current selection, don't re-search.
    if (!trimmed || (selected && trimmed === selected.title)) {
      setResults([]);
      setLoading(false);
      setError(false);
      return;
    }

    const controller = new AbortController();
    setLoading(true);
    setError(false);
    const timer = setTimeout(async () => {
      try {
        const matches = await searchTickers(trimmed, controller.signal);
        setResults(matches);
        setHighlight(0);
        setOpen(true);
      } catch (err) {
        if (!controller.signal.aborted) {
          setResults([]);
          setError(true);
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }, DEBOUNCE_MS);

    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [query, selected]);

  // Close the dropdown when clicking outside the component.
  useEffect(() => {
    const onClickAway = (e: MouseEvent) => {
      if (!containerRef.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onClickAway);
    return () => document.removeEventListener("mousedown", onClickAway);
  }, []);

  const choose = (company: Company) => {
    onSelect(company);
    setQuery(company.title);
    setResults([]);
    setOpen(false);
  };

  const handleChange = (value: string) => {
    setQuery(value);
    if (selected) onSelect(null); // editing invalidates a prior selection
    setOpen(true);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!open || results.length === 0) {
      if (e.key === "ArrowDown" && results.length > 0) setOpen(true);
      return;
    }
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setHighlight((h) => (h + 1) % results.length);
        break;
      case "ArrowUp":
        e.preventDefault();
        setHighlight((h) => (h - 1 + results.length) % results.length);
        break;
      case "Enter":
        e.preventDefault();
        choose(results[highlight]);
        break;
      case "Escape":
        setOpen(false);
        break;
    }
  };

  const showDropdown = open && (loading || error || results.length > 0);

  return (
    <div className="flex flex-col gap-2" ref={containerRef}>
      <label
        htmlFor="ticker"
        className="font-mono text-xs uppercase tracking-widest text-text-muted"
      >
        Company / Ticker
      </label>

      <div className="relative">
        <input
          id="ticker"
          type="text"
          role="combobox"
          aria-expanded={showDropdown}
          aria-controls={listboxId}
          aria-autocomplete="list"
          value={query}
          onChange={(e) => handleChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => results.length > 0 && setOpen(true)}
          placeholder="Search e.g. Apple or AAPL"
          autoComplete="off"
          spellCheck={false}
          className="w-full rounded-sm border border-border-subtle bg-bg-elevated px-4 py-3 font-mono text-lg tracking-wide text-text-primary placeholder:text-text-muted focus:border-accent-primary focus:outline-none focus:ring-1 focus:ring-accent-primary"
        />

        {showDropdown && (
          <ul
            id={listboxId}
            role="listbox"
            className="absolute z-20 mt-1 max-h-72 w-full overflow-auto rounded-sm border border-border-default bg-bg-elevated shadow-lg shadow-black/40"
          >
            {loading && results.length === 0 && (
              <li className="px-4 py-3 font-mono text-sm text-text-muted">
                Searching…
              </li>
            )}
            {error && (
              <li className="px-4 py-3 font-mono text-sm text-accent-danger">
                Search unavailable. Is the API running?
              </li>
            )}
            {results.map((company, i) => (
              <li
                key={`${company.ticker}-${company.cik}`}
                role="option"
                aria-selected={i === highlight}
                onMouseDown={(e) => {
                  e.preventDefault();
                  choose(company);
                }}
                onMouseEnter={() => setHighlight(i)}
                className={`flex items-center justify-between gap-4 px-4 py-2.5 cursor-pointer ${
                  i === highlight ? "bg-accent-primary/15" : ""
                }`}
              >
                <span className="font-mono text-sm font-medium tracking-wider text-text-accent">
                  {company.ticker}
                </span>
                <span className="truncate text-right text-sm text-text-secondary">
                  {company.title}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="flex items-center justify-between pt-1">
        <span className="font-mono text-xs uppercase tracking-widest text-text-muted">
          Resolved Entity
        </span>
        {selected ? (
          <span className="flex items-center gap-1.5 font-mono text-sm text-text-accent">
            <svg
              className="h-3.5 w-3.5 text-accent-success"
              viewBox="0 0 20 20"
              fill="currentColor"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M16.704 5.29a1 1 0 0 1 .006 1.414l-7.07 7.13a1 1 0 0 1-1.42.002l-3.54-3.54a1 1 0 1 1 1.415-1.414l2.83 2.83 6.364-6.417a1 1 0 0 1 1.415-.005Z"
                clipRule="evenodd"
              />
            </svg>
            {selected.ticker} · {selected.title}
          </span>
        ) : (
          <span className="font-mono text-sm text-text-muted">—</span>
        )}
      </div>
    </div>
  );
}
