"""Analysis routes: start a risk-intelligence run, then resume it with the
user's chosen risk factors.

The LangGraph workflow (``agent.agent.graph``) gathers every risk factor from a
company's 10-K, then pauses at a human-in-the-loop interrupt. ``/analysis/start``
drives the graph to that pause and returns the factors; the user picks the ones
worth assessing; ``/analysis/{thread_id}/select`` resumes the same run (via the
in-memory checkpointer, keyed by ``thread_id``) through the assessment stage.
"""

from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Path
from langgraph.types import Command
from pydantic import BaseModel, Field

from agent.agent import graph
from agent.state import RiskCategory, WorkflowState

router = APIRouter(prefix="/analysis", tags=["analysis"])


class StartRequest(BaseModel):
    """Kick off a run for one company across two fiscal years."""

    cik: str = Field(description="SEC Central Index Key of the company.")
    current_year: int = Field(description="Fiscal year of the 10-K to analyze.")
    prior_year: int = Field(description="Fiscal year of the 10-K to compare against.")


class RiskFactorOut(BaseModel):
    """A gathered risk factor, tagged with a stable id for selection."""

    id: int = Field(description="Index of this factor within the gathered list.")
    title: str
    summary: str | None = None
    category: RiskCategory | None = None
    verbatim_text: str


class StartResponse(BaseModel):
    """Risk factors gathered before the workflow paused for selection."""

    thread_id: str
    current_year_risk_factors: list[RiskFactorOut]


class SelectRequest(BaseModel):
    """The user's chosen subset, by the ids returned from ``/start``."""

    selected_ids: list[int] = Field(
        description="Ids of the risk factors to assess in depth."
    )


class AssessmentRow(BaseModel):
    """One assessed risk factor (stub output for now)."""

    title: str
    category: RiskCategory | None = None
    status: str
    note: str | None = None


class SelectResponse(BaseModel):
    """Assessment produced after resuming the run with the selected factors."""

    thread_id: str
    assessment: list[AssessmentRow]


def _thread_config(thread_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": thread_id}}


def _to_out(factors: list[dict[str, Any]]) -> list[RiskFactorOut]:
    """Attach an index-based id to each gathered factor for stable selection."""
    return [
        RiskFactorOut(
            id=i,
            title=factor.get("title", ""),
            summary=factor.get("summary"),
            category=factor.get("category"),
            verbatim_text=factor.get("verbatim_text", ""),
        )
        for i, factor in enumerate(factors)
    ]


@router.post("/start", response_model=StartResponse)
async def start_analysis(request: StartRequest) -> StartResponse:
    """Run the workflow up to the selection pause and return the risk factors."""
    thread_id = str(uuid4())
    config = _thread_config(thread_id)
    initial_state: WorkflowState = {
        "company_cik": request.cik,
        "current_year": request.current_year,
        "prior_year": request.prior_year,
    }

    result = await graph.ainvoke(initial_state, config)
    factors = result.get("current_year_risk_factors", [])
    return StartResponse(
        thread_id=thread_id,
        current_year_risk_factors=_to_out(factors),
    )


async def _gathered_factors(thread_id: str) -> list[dict[str, Any]]:
    """Return the gathered current-year factors for a thread, or 404."""
    snapshot = await graph.aget_state(_thread_config(thread_id))
    factors = snapshot.values.get("current_year_risk_factors")
    if not snapshot.values or factors is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No analysis found for thread {thread_id!r}. It may have "
                "expired (state is held in memory and is lost on restart)."
            ),
        )
    return factors


@router.get("/{thread_id}", response_model=StartResponse)
async def get_analysis(
    thread_id: Annotated[str, Path(description="Thread id from /analysis/start.")],
) -> StartResponse:
    """Re-fetch the gathered risk factors so the selection page survives refresh."""
    factors = await _gathered_factors(thread_id)
    return StartResponse(
        thread_id=thread_id,
        current_year_risk_factors=_to_out(factors),
    )


@router.post("/{thread_id}/select", response_model=SelectResponse)
async def select_risk_factors(
    thread_id: Annotated[str, Path(description="Thread id from /analysis/start.")],
    request: SelectRequest,
) -> SelectResponse:
    """Resume the run with the chosen factors and return the assessment."""
    factors = await _gathered_factors(thread_id)

    valid_ids = range(len(factors))
    invalid = [i for i in request.selected_ids if i not in valid_ids]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown risk factor ids for this analysis: {invalid}.",
        )
    if not request.selected_ids:
        raise HTTPException(
            status_code=400, detail="Select at least one risk factor to assess."
        )

    selected = [factors[i] for i in request.selected_ids]
    result = await graph.ainvoke(Command(resume=selected), _thread_config(thread_id))
    return SelectResponse(
        thread_id=thread_id,
        assessment=[AssessmentRow(**row) for row in result.get("assessment", [])],
    )
