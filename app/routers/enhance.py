"""
Enhance API: run the resume enhancer graph with Resume + JobDescription schemas.

For testing: POST JSON body with resume and job_description; returns final state.
"""
import logging
from typing import Any, Dict

from fastapi import APIRouter, Request
from pydantic import BaseModel

from schemas.resume import Resume
from schemas.job_description import JobDescription
from graph.graph import run_resume_enhancer

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
def enhance(request: Request, body: EnhanceRequest):
    """
    Run the LangGraph workflow with the given Resume and JobDescription.

    Returns the final graph state as JSON:
    - On enhance path: resume, job_description, mapping_result,
      full_enhancement_output, enhanced_resume, change_report.
    - On feedback path: resume, job_description, mapping_result,
      feedback_message.
    """
    graph = getattr(request.app.state, "graph", None)
    if graph is None:
        logger.error("enhance: app.state.graph not set")
        raise RuntimeError("Graph not initialized; check server startup.")

    logger.info("enhance: invoking graph with provided resume and job_description")
    state = run_resume_enhancer(graph, body.resume, body.job_description)
    jsonable = _state_to_jsonable(state)
    logger.info(
        "enhance: done keys=%s has_enhanced=%s has_feedback=%s",
        list(jsonable.keys()),
        bool(jsonable.get("enhanced_resume")),
        bool(jsonable.get("feedback_message")),
    )
    return jsonable
