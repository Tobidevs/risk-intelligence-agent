import asyncio
import time

import httpx
import requests
from llama_cloud import LlamaCloud
from pydantic import BaseModel, Field

from agent.cache import read_cache, write_cache
from agent.state import WorkflowState
from app.core.config import get_settings

SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik_padded}.json"
SEC_ARCHIVE_DOC_URL = (
    "https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no_dashes}/{filename}"
)


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


async def _fetch_10k_html(
    client: httpx.AsyncClient, cik: str, accession: str, filename: str
) -> str:
    """Fetch the raw HTML of a single 10-K primary document from the archive."""
    accession_no_dashes = accession.replace("-", "")
    url = SEC_ARCHIVE_DOC_URL.format(
        cik=cik, accession_no_dashes=accession_no_dashes, filename=filename
    )
    response = await client.get(url)
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


class TenKSections(BaseModel):
    """LlamaExtract target schema for the two 10-K sections we care about.

    The field descriptions double as extraction instructions for the model, so
    they spell out exactly which content to capture and that it must be verbatim
    rather than summarized. Item 1A is decomposed into individual risk factors
    (a repeating entity), while Item 7 is kept as a single section blob.
    """

    item_1a_risk_factors: list[RiskFactor] = Field(
        description=(
            "Every individual risk factor disclosed under 'Item 1A. Risk "
            "Factors', in the order they appear. Each entry is one discrete risk "
            "factor. Do not include the section's introductory preamble as a risk "
            "factor, and do not omit any risk factor."
        )
    )
    item_7_mda: str = Field(
        description=(
            "The complete, verbatim text of the \"Item 7. Management's Discussion "
            "and Analysis of Financial Condition and Results of Operations\" "
            "(MD&A) section of the 10-K, from the section heading up to (but not "
            "including) the next item heading. Preserve the wording exactly; do "
            "not summarize or paraphrase."
        )
    )


# A LlamaCloud extract job is done once it leaves PENDING; these are the
# terminal states we stop polling on. SUCCESS / PARTIAL_SUCCESS carry results.
_EXTRACT_TERMINAL_STATUSES = {"SUCCESS", "PARTIAL_SUCCESS", "ERROR", "CANCELLED"}


def _extract_sections_from_html(
    client: LlamaCloud, html: str, filename: str
) -> dict:
    """Run LlamaExtract over one 10-K's HTML and return the extracted sections.

    The cached HTML bytes are uploaded directly (no re-download), an extraction
    job is created against the TenKSections schema, and the job is polled until
    it reaches a terminal status. The filename gives LlamaCloud the .htm hint it
    needs to parse the markup rather than treat it as plain text.
    """
    file_obj = client.files.create(
        file=(filename, html.encode("utf-8")),
        purpose="extract",
    )

    job = client.extract.create(
        file_input=file_obj.id,
        configuration={
            "data_schema": TenKSections.model_json_schema(),
            "extraction_target": "per_doc",
            "tier": "agentic",
        },
    )

    while job.status not in _EXTRACT_TERMINAL_STATUSES:
        time.sleep(2)
        job = client.extract.get(job.id)

    if job.status not in ("SUCCESS", "PARTIAL_SUCCESS"):
        raise RuntimeError(
            f"LlamaExtract job for {filename} ended in {job.status}: "
            f"{job.error_message}"
        )

    return job.extract_result


def extract_filing_sections(state: WorkflowState) -> dict:
    """Extract Item 1A risk factors and Item 7 (MD&A) from both 10-Ks.

    Uses the LlamaCloud (v2) Extract API on the raw 10-K HTML already fetched
    into state by retrieve_filing_index. Item 1A is decomposed into a list of
    individual risk factors (each with a title and verbatim text) via the
    repeating-entity TenKSections schema, and Item 7 is captured as a single
    blob. Each year's cached HTML is uploaded and extracted, then the job is
    polled to completion. Returns a state update with, per year, the list of
    risk factors and the MD&A text.
    """
    client = LlamaCloud(api_key=get_settings().llama_cloud_api_key)

    current = _extract_sections_from_html(
        client, state["current_year_html"], state["current_year_primary_doc"]
    )
    prior = _extract_sections_from_html(
        client, state["prior_year_html"], state["prior_year_primary_doc"]
    )

    return {
        "current_year_risk_factors": current["item_1a_risk_factors"],
        "prior_year_risk_factors": prior["item_1a_risk_factors"],
        "current_year_mda": current["item_7_mda"],
        "prior_year_mda": prior["item_7_mda"],
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

    print("\nExtracting sections with LlamaExtract (this calls LlamaCloud)...")
    test_state.update(extract_filing_sections(test_state))

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
