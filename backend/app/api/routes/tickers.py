"""Ticker search route backed by the SEC company directory."""

from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services import tickers

router = APIRouter(prefix="/tickers", tags=["tickers"])


class Company(BaseModel):
    """A ticker search result."""

    ticker: str
    title: str
    cik: str


@router.get("/search", response_model=list[Company])
async def search_tickers(
    q: Annotated[str, Query(description="Company name or ticker fragment.")],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> list[dict[str, str]]:
    """Return companies whose ticker or name matches ``q``, best matches first."""
    return await tickers.search(q, limit=limit)
