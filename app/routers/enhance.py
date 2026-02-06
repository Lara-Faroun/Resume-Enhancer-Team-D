"""
Enhance API: run the resume enhancer graph with Resume + JobDescription schemas.

For testing: POST JSON body with resume and job_description; returns final state.
"""
import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from schemas.resume import Resume
from schemas.job_description import JobDescription
from graph.graph import run_resume_enhancer_async

logger = logging.getLogger(__name__)

router = APIRouter()


class EnhanceRequest(BaseModel):
    """Request body: resume and job description as Pydantic schemas."""

    resume: Resume
    job_description: JobDescription


def _state_to_jsonable(state: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively convert state (may contain Pydantic models) to JSON-serializable dict."""
    out: Dict[str, Any] = {}
    for key, value in state.items():
        if value is None:
            out[key] = None
        elif isinstance(value, BaseModel):
            out[key] = value.model_dump(mode="json")
        elif isinstance(value, list):
            out[key] = [
                item.model_dump(mode="json") if isinstance(item, BaseModel) else item
                for item in value
            ]
        elif isinstance(value, dict):
            out[key] = _state_to_jsonable(value)
        else:
            out[key] = value
    return out


@router.post("/enhance", response_model=None)
async def enhance(request: Request, body: EnhanceRequest):
    """
    Run the LangGraph workflow with the given Resume and JobDescription.

    Returns the final graph state as JSON:
    - On enhance path: resume, job_description, mapping_result,
      full_enhancement_output, enhanced_resume, report_summary.
    - On feedback path: resume, job_description, mapping_result,
      feedback_message.
    """
    graph = getattr(request.app.state, "graph", None)
    if graph is None:
        logger.error("enhance: app.state.graph not set")
        raise HTTPException(
            status_code=503,
            detail="Enhancement graph not initialized. Please try again later.",
        )

    logger.info("enhance: invoking graph with provided resume and job_description")

    try:
        state = await run_resume_enhancer_async(
            graph,
            body.resume,
            body.job_description,
        )
    except Exception as exc:
        # Log full stack trace for operators; return safe message to client.
        logger.exception("enhance: graph invocation failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Failed to run resume enhancement workflow.",
        ) from exc

    if not isinstance(state, dict):
        logger.error("enhance: unexpected graph result type: %s", type(state))
        raise HTTPException(
            status_code=500,
            detail="Unexpected enhancement result format.",
        )

    jsonable = _state_to_jsonable(state)
    logger.info(
        "enhance: done keys=%s has_enhanced=%s has_feedback=%s",
        list(jsonable.keys()),
        bool(jsonable.get("enhanced_resume")),
        bool(jsonable.get("feedback_message")),
    )
    return jsonable
