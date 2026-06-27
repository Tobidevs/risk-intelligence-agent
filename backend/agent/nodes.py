import asyncio

import httpx
import requests

from agent.state import WorkflowState

SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik_padded}.json"
SEC_ARCHIVE_DOC_URL = (
    "https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no_dashes}/{filename}"
)
# SEC requires a descriptive User-Agent identifying the requester.
SEC_USER_AGENT = "risk-intelligence-agent tobiakere05@gmail.com"


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

    response = requests.get(url, headers={"User-Agent": SEC_USER_AGENT}, timeout=30)
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
    by retrieve_company_filings, then fetches both 10-K HTML documents from the
    SEC archive concurrently. Returns a state update with the raw HTML for each
    year.
    """
    cik = str(int(state["company_cik"]))  # archive paths use the unpadded CIK

    async with httpx.AsyncClient(
        headers={"User-Agent": SEC_USER_AGENT}, timeout=30
    ) as client:
        current_html, prior_html = await asyncio.gather(
            _fetch_10k_html(
                client,
                cik,
                state["current_year_accession"],
                state["current_year_primary_doc"],
            ),
            _fetch_10k_html(
                client,
                cik,
                state["prior_year_accession"],
                state["prior_year_primary_doc"],
            ),
        )

    return {
        "current_year_html": current_html,
        "prior_year_html": prior_html,
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
    print("current_year_html head:", test_state["current_year_html"][:120])
