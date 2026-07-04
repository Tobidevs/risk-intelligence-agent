from typing import NotRequired, TypedDict
from pydantic import BaseModel, Field
from typing import Literal

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
    # individual risk factors, each a {"title", "summary", "category",
    # "verbatim_text"}
    # dict; Item 7 (MD&A) is kept as a single verbatim blob.
    current_year_risk_factors: NotRequired[list[dict[str, str]]]
    prior_year_risk_factors: NotRequired[list[dict[str, str]]]
    current_year_mda: NotRequired[str]
    prior_year_mda: NotRequired[str]


RiskCategory = Literal[
    "Market Risk",
    "Credit Risk",
    "Operational Risk",
    "Regulatory/Compliance Risk",
    "Strategic Risk",
    "Reputational Risk",
]


class RiskFactor(BaseModel):
    """A single, discrete risk factor within the Item 1A section.

    Apple lists each risk factor as a bold summary sentence followed by one or
    more explanatory paragraphs. The field descriptions double as extraction
    instructions, telling the model where one factor ends and the next begins.
    """

    title: str = Field(
        description=(
            "A concise, client-facing title for this risk factor (roughly 3-8 "
            "words), written by you as a heading in clear, plain language a "
            "reader assessing this risk can understand at a glance — not the "
            'verbatim summary sentence. For example, a factor whose summary '
            'sentence reads "The Company\'s future performance depends in part '
            'on support from third-party developers." might be titled "Reliance '
            'on Third-Party Developers".'
        )
    )
    summary: str = Field(
        description=(
            "A concise, client-facing summary of this risk factor (roughly 2-4 "
            "sentences) that you compose in plain language for a reader "
            "assessing the risk. Explain what the risk is and why it matters to "
            "the company in accessible terms — do not quote the filing "
            "verbatim; paraphrase and clarify."
        )
    )
    category: RiskCategory = Field(
        description=(
            "The single category that best classifies this risk factor, chosen "
            "from the allowed set."
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