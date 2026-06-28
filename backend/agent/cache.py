"""Filesystem cache for downloaded 10-K HTML documents.

SEC filings are immutable once accepted, so a document keyed by its accession
number and filename never changes. That makes caching here simple: fetch each
document from the network once, save it to disk, and read it locally forever
after. No expiry or invalidation is ever required.
"""

import os

from app.core.config import get_settings


def cached_path(accession: str, filename: str):
    """Return the on-disk path for a cached filing document.

    The accession number's dashes are stripped so each filing gets its own
    sub-folder, mirroring SEC's archive layout, e.g.
    ``<cache_dir>/000032019320000096/aapl-20200926.htm``.
    """
    accession_no_dashes = accession.replace("-", "")
    return get_settings().cache_dir / accession_no_dashes / filename


def read_cache(accession: str, filename: str) -> str | None:
    """Return the cached HTML if present (a cache hit), else None (a miss)."""
    path = cached_path(accession, filename)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None


def write_cache(accession: str, filename: str, html: str) -> None:
    """Save HTML to the cache using an atomic write.

    The content is written to a temporary file first, then renamed into place.
    Rename is atomic, so a crash mid-write can never leave a partially written
    file that a later run would mistake for a valid cache entry.
    """
    path = cached_path(accession, filename)
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(html, encoding="utf-8")
    os.replace(tmp_path, path)
