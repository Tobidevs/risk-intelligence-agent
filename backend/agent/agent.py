import asyncio

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from agent.nodes import (
    assess_selected_risk_factors,
    await_risk_factor_selection,
    extract_filing_sections,
    retrieve_company_filings,
    retrieve_filing_index,
)
from agent.state import WorkflowState


def build_graph():
    """Build and compile the risk intelligence agent graph.

    After extract_filing_sections gathers every risk factor, the graph pauses at
    await_risk_factor_selection (a human-in-the-loop interrupt) so the user can
    choose which factors to assess. It then resumes into assess_selected_risk_
    factors. A MemorySaver checkpointer holds the interrupted state between the
    start and resume calls; runs are keyed by thread_id and live only in-process.
    """
    builder = StateGraph(WorkflowState)

    builder.add_node("retrieve_company_filings", retrieve_company_filings)
    builder.add_node("retrieve_filing_index", retrieve_filing_index)
    builder.add_node("extract_filing_sections", extract_filing_sections)
    builder.add_node("await_risk_factor_selection", await_risk_factor_selection)
    builder.add_node("assess_selected_risk_factors", assess_selected_risk_factors)

    builder.add_edge(START, "retrieve_company_filings")
    builder.add_edge("retrieve_company_filings", "retrieve_filing_index")
    builder.add_edge("retrieve_filing_index", "extract_filing_sections")
    builder.add_edge("extract_filing_sections", "await_risk_factor_selection")
    builder.add_edge("await_risk_factor_selection", "assess_selected_risk_factors")
    builder.add_edge("assess_selected_risk_factors", END)

    return builder.compile(checkpointer=MemorySaver())


graph = build_graph()


async def run_test() -> WorkflowState:
    """Run the full graph for Apple's FY2020 (current) and FY2019 (prior) 10-Ks.

    Manual smoke test of the end-to-end human-in-the-loop workflow: SEC filing
    lookup, HTML retrieval, sec-api.io section extraction with LLM risk-factor
    decomposition, then the selection interrupt and assessment resume. To keep
    the smoke test non-interactive it auto-selects every current-year risk
    factor. Uses ainvoke because the retrieval/extraction nodes are async, and a
    thread_id because the graph is compiled with a checkpointer.
    """
    config = {"configurable": {"thread_id": "smoke-test"}}
    initial_state: WorkflowState = {
        "company_cik": "320193",  # Apple Inc.
        "current_year": 2020,
        "prior_year": 2019,
    }

    # Runs up to await_risk_factor_selection, which raises the interrupt.
    paused = await graph.ainvoke(initial_state, config)
    all_factors = paused["current_year_risk_factors"]

    # Resume as the API would, auto-selecting every gathered factor.
    return await graph.ainvoke(Command(resume=all_factors), config)


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

    assessment = result.get("assessment", [])
    print(f"\n===== assessment: {len(assessment)} selected factors =====")
    for i, row in enumerate(assessment, 1):
        print(f"[{i}] {row['title']}  <{row['category']}> — {row['status']}")
