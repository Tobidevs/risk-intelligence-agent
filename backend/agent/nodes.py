import asyncio

import httpx
import requests
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from agent.cache import read_cache, write_cache
from agent.prompts import RISK_FACTOR_EXTRACTION_SYSTEM_PROMPT
from agent.state import WorkflowState
from app.core.config import get_settings

SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik_padded}.json"
SEC_ARCHIVE_DOC_URL = (
    "https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no_dashes}/{filename}"
)
SEC_API_EXTRACTOR_URL = "https://api.sec-api.io/extractor"


def retrieve_company_filings(state: WorkflowState) -> dict:
    """Fetch a company's filing history from SEC EDGAR and extract the 10-K
    accession number and primary document for the current and prior years.

    The CIK is zero-padded to 10 digits, the submissions JSON is retrieved, and
    10-K filings are matched to the target years by their reportDate (the fiscal
    year the filing reports on). Returns a state update with the accession
    numbers and primary document filenames for each year.
    """
    cik_padded = str(state["company_cik"]).zfill(10)
    url = SEC_SUBMISSIONS_URL.format(cik_padded=cik_padded)

    headers = {"User-Agent": get_settings().sec_user_agent}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()

    recent = data["filings"]["recent"]
    target_years = {state["current_year"], state["prior_year"]}
    matches: dict[int, dict] = {}

    for i, form in enumerate(recent["form"]):
        if form != "10-K":
            continue
        report_date = recent["reportDate"][i]
        if not report_date:
            continue
        year = int(report_date[:4])
        if year in target_years and year not in matches:
            matches[year] = {
                "accession_number": recent["accessionNumber"][i],
                "primary_document": recent["primaryDocument"][i],
            }

    current = matches.get(state["current_year"], {})
    prior = matches.get(state["prior_year"], {})

    return {
        "current_year_accession": current.get("accession_number"),
        "prior_year_accession": prior.get("accession_number"),
        "current_year_primary_doc": current.get("primary_document"),
        "prior_year_primary_doc": prior.get("primary_document"),
    }


def _filing_url(cik: str, accession: str, filename: str) -> str:
    """Build the SEC archive URL for a filing's primary document."""
    accession_no_dashes = accession.replace("-", "")
    return SEC_ARCHIVE_DOC_URL.format(
        cik=cik, accession_no_dashes=accession_no_dashes, filename=filename
    )


async def _fetch_10k_html(
    client: httpx.AsyncClient, cik: str, accession: str, filename: str
) -> str:
    """Fetch the raw HTML of a single 10-K primary document from the archive."""
    response = await client.get(_filing_url(cik, accession, filename))
    response.raise_for_status()
    return response.text


async def retrieve_filing_index(state: WorkflowState) -> dict:
    """Retrieve the raw HTML of the current- and prior-year 10-K documents.

    Reads the accession numbers and primary document filenames written to state
    by retrieve_company_filings. Each document is checked against the filesystem
    cache first; only cache misses are downloaded from the SEC archive (those
    fetches still run concurrently), and freshly downloaded HTML is written back
    to the cache. Returns a state update with the raw HTML for each year.
    """
    cik = str(int(state["company_cik"]))  # archive paths use the unpadded CIK

    docs = {
        "current_year_html": (
            state["current_year_accession"],
            state["current_year_primary_doc"],
        ),
        "prior_year_html": (
            state["prior_year_accession"],
            state["prior_year_primary_doc"],
        ),
    }

    results: dict[str, str] = {}
    misses: dict[str, tuple[str, str]] = {}

    # Check the cache first; anything not on disk is a miss to be fetched.
    for key, (accession, filename) in docs.items():
        cached = read_cache(accession, filename)
        if cached is not None:
            results[key] = cached
        else:
            misses[key] = (accession, filename)

    # Download any misses concurrently, then write them to the cache.
    if misses:
        headers = {"User-Agent": get_settings().sec_user_agent}
        async with httpx.AsyncClient(headers=headers, timeout=30) as client:
            fetched = await asyncio.gather(
                *(
                    _fetch_10k_html(client, cik, accession, filename)
                    for accession, filename in misses.values()
                )
            )
        for (key, (accession, filename)), html in zip(misses.items(), fetched):
            write_cache(accession, filename, html)
            results[key] = html

    return {
        "current_year_html": results["current_year_html"],
        "prior_year_html": results["prior_year_html"],
    }


class RiskFactor(BaseModel):
    """A single, discrete risk factor within the Item 1A section.

    Apple lists each risk factor as a bold summary sentence followed by one or
    more explanatory paragraphs. The field descriptions double as extraction
    instructions, telling the model where one factor ends and the next begins.
    """

    title: str = Field(
        description=(
            "The bold summary sentence that introduces this risk factor and "
            "serves as its heading, copied verbatim (e.g. \"The Company's future "
            "performance depends in part on support from third-party developers.\")."
        )
    )
    verbatim_text: str = Field(
        description=(
            "The complete, verbatim body of this single risk factor: its bold "
            "summary sentence plus all explanatory paragraphs that belong to it, "
            "up to (but not including) the next risk factor's summary sentence. "
            "Copy the wording exactly; do not summarize, paraphrase, or merge "
            "adjacent risk factors."
        )
    )


class RiskFactorList(BaseModel):
    """Structured-output target for decomposing Item 1A into risk factors."""

    risk_factors: list[RiskFactor] = Field(
        description=(
            "Every individual risk factor disclosed in the text, in the order "
            "they appear."
        )
    )


async def _extract_item_via_sec_api(
    client: httpx.AsyncClient, filing_url: str, item: str
) -> str:
    """Fetch one 10-K item's clean text via the sec-api.io Extractor API."""
    response = await client.get(
        SEC_API_EXTRACTOR_URL,
        params={
            "url": filing_url,
            "item": item,
            "type": "text",
            "token": get_settings().sec_api_api_key,
        },
    )
    response.raise_for_status()
    return response.text


async def _extract_sections_from_filing(
    client: httpx.AsyncClient, filing_url: str
) -> dict:
    """Fetch Item 1A and Item 7 text for one filing, scoped directly by sec-api.io."""
    item_1a_text, item_7_text = await asyncio.gather(
        _extract_item_via_sec_api(client, filing_url, "1A"),
        _extract_item_via_sec_api(client, filing_url, "7"),
    )
    return {"item_1a_text": item_1a_text, "item_7_text": item_7_text}


def _decompose_risk_factors(model, item_1a_text: str) -> list[dict]:
    """Split one filing's Item 1A text into individual risk factors via an LLM."""
    structured_model = model.with_structured_output(RiskFactorList)
    result = structured_model.invoke(
        [
            SystemMessage(content=RISK_FACTOR_EXTRACTION_SYSTEM_PROMPT),
            HumanMessage(content=item_1a_text),
        ]
    )
    return [risk_factor.model_dump() for risk_factor in result.risk_factors]


async def extract_filing_sections(state: WorkflowState) -> dict:
    """Extract Item 1A risk factors and Item 7 (MD&A) from both 10-Ks.

    Item 1A and Item 7 text are pulled directly from each filing via the
    sec-api.io Extractor API, scoped to just those sections (no whole-document
    search needed). Item 1A is then decomposed into a list of individual risk
    factors (each with a title and verbatim text) by an LLM structured-output
    call; Item 7 is stored verbatim as sec-api.io returns it. Returns a state
    update with, per year, the list of risk factors and the MD&A text.
    """
    cik = str(int(state["company_cik"]))  # archive paths use the unpadded CIK
    current_url = _filing_url(
        cik, state["current_year_accession"], state["current_year_primary_doc"]
    )
    prior_url = _filing_url(
        cik, state["prior_year_accession"], state["prior_year_primary_doc"]
    )

    async with httpx.AsyncClient(timeout=60) as client:
        current_sections, prior_sections = await asyncio.gather(
            _extract_sections_from_filing(client, current_url),
            _extract_sections_from_filing(client, prior_url),
        )

    model = init_chat_model("gpt-5", model_provider="openai")

    return {
        "current_year_risk_factors": _decompose_risk_factors(
            model, current_sections["item_1a_text"]
        ),
        "prior_year_risk_factors": _decompose_risk_factors(
            model, prior_sections["item_1a_text"]
        ),
        "current_year_mda": current_sections["item_7_text"],
        "prior_year_mda": prior_sections["item_7_text"],
    }


if __name__ == "__main__":
    # Quick test: Apple (CIK 320193), 10-K HTML for 2020 and 2019.
    test_state: WorkflowState = {
        "company_cik": "320193",
        "current_year": 2020,
        "prior_year": 2019,
    }

    test_state.update(retrieve_company_filings(test_state))
    print("filings:", {k: v for k, v in test_state.items() if k != "current_year"})

    test_state.update(asyncio.run(retrieve_filing_index(test_state)))
    print("current_year_html length:", len(test_state["current_year_html"]))
    print("prior_year_html length:", len(test_state["prior_year_html"]))

    print("\nExtracting sections via sec-api.io and decomposing risk factors...")
    test_state.update(asyncio.run(extract_filing_sections(test_state)))

    for rf_key, mda_key in (
        ("current_year_risk_factors", "current_year_mda"),
        ("prior_year_risk_factors", "prior_year_mda"),
    ):
        factors = test_state[rf_key]
        print(f"\n===== {rf_key}: {len(factors)} risk factors =====")
        for i, factor in enumerate(factors, 1):
            title = " ".join(factor["title"].split())
            body = " ".join(factor["verbatim_text"].split())
            print(f"\n[{i}] {title}")
            print(f"    ({len(factor['verbatim_text']):,} chars) {body[:200]} ...")
        mda = test_state[mda_key]
        print(f"\n--- {mda_key} ({len(mda):,} chars) ---")
        print(" ".join(mda.split())[:300], "...")
