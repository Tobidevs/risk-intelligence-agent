from typing import NotRequired, TypedDict


class WorkflowState(TypedDict):
    """State for the risk intelligence agent graph."""

    company_cik: str
    current_year: int
    prior_year: int

    # Populated by retrieve_company_filings.
    current_year_accession: NotRequired[str]
    prior_year_accession: NotRequired[str]
    current_year_primary_doc: NotRequired[str]
    prior_year_primary_doc: NotRequired[str]

    # Populated by retrieve_filing_index.
    current_year_html: NotRequired[str]
    prior_year_html: NotRequired[str]
