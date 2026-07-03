"""Application configuration via pydantic-settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings, overridable via environment variables or a .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "FilingLens API"
    app_version: str = "0.1.0"
    debug: bool = False

    # Origins allowed to call the API. The Next.js dev server runs on :3000.
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # SEC publishes a free ticker -> company name + CIK map. No API key needed,
    # but they require a descriptive User-Agent identifying the caller.
    # See https://www.sec.gov/os/webmaster-faq#developers
    sec_tickers_url: str = "https://www.sec.gov/files/company_tickers.json"
    sec_user_agent: str = "FilingLens tobiakere05@gmail.com"

    # Directory where downloaded 10-K HTML is cached. Relative to the backend
    # working directory; override via .env if needed. SEC filings are immutable,
    # so cached copies never go stale.
    cache_dir: Path = Path(".cache") / "filings"

    # sec-api.io API key, used by the Extractor API to pull Item 1A and Item 7
    # text directly out of a 10-K filing by section. Read from the
    # SEC_API_API_KEY env var / .env entry.
    sec_api_api_key: str | None = Field(
        default=None, validation_alias="SEC_API_API_KEY"
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
