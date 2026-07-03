import asyncio

from langgraph.graph import END, START, StateGraph

from agent.nodes import (
    extract_filing_sections,
    retrieve_company_filings,
    retrieve_filing_index,
)
from agent.state import WorkflowState


def build_graph():
    """Build and compile the risk intelligence agent graph."""
    builder = StateGraph(WorkflowState)

    builder.add_node("retrieve_company_filings", retrieve_company_filings)
    builder.add_node("retrieve_filing_index", retrieve_filing_index)
    builder.add_node("extract_filing_sections", extract_filing_sections)

    builder.add_edge(START, "retrieve_company_filings")
    builder.add_edge("retrieve_company_filings", "retrieve_filing_index")
    builder.add_edge("retrieve_filing_index", "extract_filing_sections")
    builder.add_edge("extract_filing_sections", END)

    return builder.compile()


graph = build_graph()


async def run_test() -> WorkflowState:
    """Run the full graph for Apple's FY2020 (current) and FY2019 (prior) 10-Ks.

    Manual smoke test of the end-to-end workflow: SEC filing lookup, HTML
    retrieval, and sec-api.io section extraction with LLM risk-factor
    decomposition, wired together as a graph. Uses ainvoke because
    retrieve_filing_index and extract_filing_sections are async nodes.
    """
    initial_state: WorkflowState = {
        "company_cik": "320193",  # Apple Inc.
        "current_year": 2020,
        "prior_year": 2019,
    }
    return await graph.ainvoke(initial_state)


if __name__ == "__main__":
    from app.core.tracing import init_tracing

    init_tracing()

    result = asyncio.run(run_test())

    for rf_key, mda_key in (
        ("current_year_risk_factors", "current_year_mda"),
        ("prior_year_risk_factors", "prior_year_mda"),
    ):
        print(f"\n===== {rf_key}: {len(result[rf_key])} risk factors =====")
        for i, factor in enumerate(result[rf_key], 1):
            print(f"[{i}] {' '.join(factor['title'].split())}")
        print(f"\n{mda_key}: {len(result[mda_key]):,} chars")
