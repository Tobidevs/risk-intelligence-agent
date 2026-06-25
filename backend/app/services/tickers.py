"""Ticker directory backed by the SEC's public company_tickers.json.

The SEC publishes a single JSON document mapping every registrant's ticker to
its company name and CIK number. We fetch it once, cache it in memory, and run
substring/prefix matching locally so the search endpoint stays fast and the SEC
servers are only ever hit once per process.
"""

from __future__ import annotations

import json
import logging
import urllib.request
from dataclasses import asdict, dataclass

import anyio

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Used only when the SEC fetch fails (e.g. offline dev) so the UI still works.
_FALLBACK: list[dict[str, object]] = [
    {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corporation"},
    {"cik_str": 1045810, "ticker": "NVDA", "title": "NVIDIA Corporation"},
    {"cik_str": 1652044, "ticker": "GOOGL", "title": "Alphabet Inc."},
    {"cik_str": 1018724, "ticker": "AMZN", "title": "Amazon.com, Inc."},
    {"cik_str": 1326801, "ticker": "META", "title": "Meta Platforms, Inc."},
    {"cik_str": 1318605, "ticker": "TSLA", "title": "Tesla, Inc."},
]


@dataclass(frozen=True, slots=True)
class Company:
    """A single ticker entry exposed to the frontend."""

    ticker: str
    title: str
    cik: str  # zero-padded 10-digit CIK, the canonical EDGAR form

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


# Module-level cache. Populated lazily on first search; reused thereafter.
_companies: list[Company] | None = None
_load_lock = anyio.Lock()


def _parse(raw: dict[str, dict[str, object]]) -> list[Company]:
    """Normalise the raw SEC payload into Company records."""
    companies: list[Company] = []
    for entry in raw.values():
        ticker = str(entry.get("ticker", "")).strip().upper()
        title = str(entry.get("title", "")).strip()
        if not ticker or not title:
            continue
        cik = str(entry.get("cik_str", "")).zfill(10)
        companies.append(Company(ticker=ticker, title=title, cik=cik))
    return companies


def _fetch_blocking() -> list[Company]:
    """Download and parse the SEC ticker map. Blocking; run off the event loop."""
    settings = get_settings()
    request = urllib.request.Request(
        settings.sec_tickers_url,
        headers={"User-Agent": settings.sec_user_agent, "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=15) as response:  # noqa: S310 (trusted SEC URL)
        payload = json.loads(response.read().decode("utf-8"))
    companies = _parse(payload)
    if not companies:
        raise ValueError("SEC ticker payload contained no usable entries")
    return companies


async def _load() -> list[Company]:
    """Return the cached company list, fetching from the SEC on first use."""
    global _companies
    if _companies is not None:
        return _companies
    async with _load_lock:
        if _companies is not None:  # another task populated it while we waited
            return _companies
        try:
            _companies = await anyio.to_thread.run_sync(_fetch_blocking)
            logger.info("Loaded %d tickers from the SEC", len(_companies))
        except Exception:  # noqa: BLE001 - degrade gracefully to the fallback set
            logger.warning(
                "Failed to fetch SEC ticker map; using built-in fallback list",
                exc_info=True,
            )
            _companies = _parse({str(i): e for i, e in enumerate(_FALLBACK)})
        return _companies


def _score(company: Company, query: str) -> int | None:
    """Rank a company against the query. Lower is better; None means no match."""
    ticker = company.ticker.lower()
    title = company.title.lower()
    if ticker == query:
        return 0
    if ticker.startswith(query):
        return 1
    if title.startswith(query):
        return 2
    if query in ticker:
        return 3
    if query in title:
        return 4
    return None


async def search(query: str, limit: int = 20) -> list[dict[str, str]]:
    """Find companies whose ticker or name matches the query, best matches first."""
    cleaned = query.strip().lower()
    if not cleaned:
        return []

    companies = await _load()
    scored: list[tuple[int, str, Company]] = []
    for company in companies:
        rank = _score(company, cleaned)
        if rank is not None:
            # Secondary sort by ticker keeps results stable and predictable.
            scored.append((rank, company.ticker, company))

    scored.sort(key=lambda item: (item[0], item[1]))
    return [company.as_dict() for _, _, company in scored[:limit]]
