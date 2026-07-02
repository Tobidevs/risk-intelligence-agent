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

    # Populated by extract_filing_sections. Item 1A is decomposed into a list of
    # individual risk factors, each a {"title", "verbatim_text"} dict; Item 7
    # (MD&A) is kept as a single verbatim blob.
    current_year_risk_factors: NotRequired[list[dict[str, str]]]
    prior_year_risk_factors: NotRequired[list[dict[str, str]]]
    current_year_mda: NotRequired[str]
    prior_year_mda: NotRequired[str]
