"""
Enhance API: run the resume enhancer graph with Resume + JobDescription schemas.

For testing: POST JSON body with resume and job_description; returns final state.
Supports both legacy mode (single response) and incremental mode (SSE streaming).
"""
import logging
import asyncio
import json
from typing import Any, Dict, Optional
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from schemas.resume import Resume
from schemas.job_description import JobDescription
from graph.graph import run_resume_enhancer

logger = logging.getLogger(__name__)

router = APIRouter()


class EnhanceRequest(BaseModel):
    """Request body: resume and job description as Pydantic schemas."""

    resume: Resume
    job_description: JobDescription
    mode: Optional[str] = Field(
        "legacy",
        description="Enhancement mode: 'legacy', 'incremental', or 'sectional'"
    )


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
    
    Modes:
    - legacy (default): Returns full state as JSON after completion
    - incremental: Streams progress events via Server-Sent Events (SSE)
    - sectional: Non-streaming per-section processing with graceful degradation
    
    Query param alternative: ?mode=incremental or ?mode=sectional
    
    Returns the final graph state as JSON (legacy/sectional) or SSE stream (incremental):
    - On enhance path: resume, job_description, mapping_result,
      full_enhancement_output, enhanced_resume, report_summary.
    - On feedback path: resume, job_description, mapping_result,
      feedback_message.
    - Sectional mode additionally includes: section_errors, sectional_metadata.
    """
    # Allow mode override via query param
    mode = request.query_params.get("mode", body.mode)
    
    if mode == "incremental":
        # Return SSE stream
        return StreamingResponse(
            enhance_incremental_stream(request, body),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            }
        )
    
    # Non-streaming modes: legacy and sectional
    graph = getattr(request.app.state, "graph", None)
    if graph is None:
        logger.error("enhance: app.state.graph not set")
        raise RuntimeError("Graph not initialized; check server startup.")

    if mode == "sectional":
        logger.info("enhance: invoking graph (sectional mode)")
        state = _run_sectional_mode(graph, body.resume, body.job_description)
    else:
        logger.info("enhance: invoking graph (legacy mode)")
        state = run_resume_enhancer(graph, body.resume, body.job_description)
    
    jsonable = _state_to_jsonable(state)
    logger.info(
        "enhance: done mode=%s keys=%s has_enhanced=%s has_feedback=%s",
        mode,
        list(jsonable.keys()),
        bool(jsonable.get("enhanced_resume")),
        bool(jsonable.get("feedback_message")),
    )
    return jsonable


def _run_sectional_mode(graph, resume: "Resume", job_description: "JobDescription") -> Dict[str, Any]:
    """
    Run the graph in sectional mode.
    
    Sectional mode processes each section independently with fallbacks,
    returning a comprehensive result including any section-level errors.
    """
    initial_state: Dict[str, Any] = {
        "resume": resume,
        "job_description": job_description,
        "mode": "sectional",
    }
    return graph.invoke(initial_state)


async def enhance_incremental_stream(request: Request, body: EnhanceRequest):
    """
    Stream enhancement progress via Server-Sent Events (SSE).
    
    Yields:
        SSE-formatted events (data: {json}\n\n)
    """
    graph = getattr(request.app.state, "graph", None)
    if graph is None:
        logger.error("enhance_incremental_stream: app.state.graph not set")
        yield f"data: {json.dumps({'event_type': 'error', 'error_message': 'Graph not initialized'})}\n\n"
        return
    
    logger.info("enhance_incremental_stream: starting")
    
    # Prepare initial state
    initial_state = {
        "resume": body.resume,
        "job_description": body.job_description,
        "mode": "incremental",
    }
    
    try:
        # Run graph in executor to avoid blocking
        # (LangGraph invoke is synchronous)
        loop = asyncio.get_event_loop()
        state = await loop.run_in_executor(
            None,
            graph.invoke,
            initial_state
        )
        
        # Stream progress events
        progress_events = state.get("progress_events", [])
        for event in progress_events:
            yield f"data: {json.dumps(event)}\n\n"
        
        # Final event with complete state
        final_event = {
            "event_type": "complete",
            "status": "complete",
            "state": _state_to_jsonable(state),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        yield f"data: {json.dumps(final_event)}\n\n"
        
        logger.info("enhance_incremental_stream: done")
    
    except Exception as e:
        logger.exception(f"enhance_incremental_stream: failed: {e}")
        error_event = {
            "event_type": "error",
            "status": "error",
            "error_message": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        yield f"data: {json.dumps(error_event)}\n\n"
