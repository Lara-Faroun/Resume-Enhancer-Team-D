"""
Enhance API: run the resume enhancer graph with Resume + JobDescription schemas.

For testing: POST JSON body with resume and job_description; returns final state.
Supports legacy mode (single response), incremental mode (real-time SSE streaming),
and sectional mode (per-section with fallbacks).
"""
import logging
import asyncio
import json
from typing import Any, Dict, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from schemas.resume import Resume
from schemas.job_description import JobDescription
from schemas.enhancement import FullEnhancementOutput
from graph.graph import run_resume_enhancer_async
from graph.nodes.enhance_streaming import stream_all_sections
from graph.nodes.mapping import mapping_node
from graph.nodes.format import format_node
from graph.nodes.report import report_node

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
async def enhance(request: Request, body: EnhanceRequest):
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
        raise HTTPException(
            status_code=503,
            detail="Enhancement graph not initialized. Please try again later.",
        )

    if mode == "sectional":
        logger.info("enhance: invoking graph (sectional mode)")
        initial_state = {
            "resume": body.resume,
            "job_description": body.job_description,
            "mode": "sectional",
        }
        state = await graph.ainvoke(initial_state)
    else:
        logger.info("enhance: invoking graph (legacy mode)")
        try:
            state = await run_resume_enhancer_async(
                graph,
                body.resume,
                body.job_description,
            )
        except Exception as exc:
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
        "enhance: done mode=%s keys=%s has_enhanced=%s has_feedback=%s",
        mode,
        list(jsonable.keys()),
        bool(jsonable.get("enhanced_resume")),
        bool(jsonable.get("feedback_message")),
    )
    return jsonable


async def enhance_incremental_stream(request: Request, body: EnhanceRequest):
    """
    Stream enhancement progress via Server-Sent Events (SSE) with real-time token streaming.
    
    This provides a chat-like experience where text appears as it's generated:
    - section_start: Section processing begins
    - section_delta: Partial text chunks (every 200-500ms)
    - section_complete: Section finished with final aggregated text
    - complete: All processing done with final state
    
    Yields:
        SSE-formatted events (data: {json}\n\n)
    """
    llm = getattr(request.app.state, "llm", None)
    if llm is None:
        logger.error("enhance_incremental_stream: app.state.llm not set")
        yield f"data: {json.dumps({'event_type': 'error', 'error_message': 'LLM not initialized'})}\n\n"
        return
    
    logger.info("enhance_incremental_stream: starting real-time streaming")
    start_time = datetime.utcnow()
    
    try:
        # Step 1: Run mapping (async)
        yield f"data: {json.dumps({'event_type': 'mapping_start', 'status': 'in_progress', 'timestamp': datetime.utcnow().isoformat() + 'Z'})}\n\n"
        
        mapping_state = {
            "resume": body.resume,
            "job_description": body.job_description,
        }
        
        mapping_result_dict = await mapping_node(mapping_state, llm)
        mapping_result = mapping_result_dict.get("mapping_result")
        
        if mapping_result is None:
            yield f"data: {json.dumps({'event_type': 'error', 'error_message': 'Mapping failed'})}\n\n"
            return
        
        yield f"data: {json.dumps({'event_type': 'mapping_complete', 'status': 'complete', 'match_score': mapping_result.match_score, 'timestamp': datetime.utcnow().isoformat() + 'Z'})}\n\n"
        
        # Check score threshold for feedback path
        from core.config import get_settings
        settings = get_settings()
        if mapping_result.match_score < settings.SCORE_THRESHOLD:
            # Feedback path - not enough alignment
            from graph.nodes.feedback import feedback_node
            feedback_state = {
                "resume": body.resume,
                "job_description": body.job_description,
                "mapping_result": mapping_result,
            }
            feedback_result = await feedback_node(feedback_state, llm)
            
            final_state = {
                "resume": body.resume.model_dump(mode="json"),
                "job_description": body.job_description.model_dump(mode="json"),
                "mapping_result": mapping_result.model_dump(mode="json"),
                "feedback_message": feedback_result.get("feedback_message"),
            }
            
            yield f"data: {json.dumps({'event_type': 'complete', 'status': 'feedback', 'state': final_state, 'timestamp': datetime.utcnow().isoformat() + 'Z'})}\n\n"
            return
        
        # Step 2: Stream enhancement with real-time deltas
        full_enhancement_output = None
        section_timings = {}
        all_events = []
        
        async for event in stream_all_sections(
            resume=body.resume,
            mapping_result=mapping_result,
            llm=llm,
        ):
            # Handle internal results event (not sent to client)
            if event.get("event_type") == "_internal_results":
                full_enhancement_output = event.get("full_enhancement_output")
                section_timings = event.get("section_timings", {})
                continue
            
            # Stream the event to client immediately
            all_events.append(event)
            yield f"data: {json.dumps(event)}\n\n"
        
        # Step 3: Run format node (sync — run in executor)
        if full_enhancement_output is None:
            full_enhancement_output = FullEnhancementOutput()
        
        format_state = {
            "resume": body.resume,
            "full_enhancement_output": full_enhancement_output,
        }
        
        loop = asyncio.get_event_loop()
        format_result = await loop.run_in_executor(
            None,
            format_node,
            format_state
        )
        enhanced_resume = format_result.get("enhanced_resume")
        
        # Step 4: Run report node (async)
        report_state = {
            "resume": body.resume,
            "enhanced_resume": enhanced_resume,
            "full_enhancement_output": full_enhancement_output,
        }
        
        report_result = await report_node(report_state, llm)
        report_summary = report_result.get("report_summary")
        
        # Build final state
        final_state = {
            "resume": body.resume.model_dump(mode="json"),
            "job_description": body.job_description.model_dump(mode="json"),
            "mapping_result": mapping_result.model_dump(mode="json"),
            "full_enhancement_output": full_enhancement_output.model_dump(mode="json") if full_enhancement_output else None,
            "enhanced_resume": enhanced_resume.model_dump(mode="json") if enhanced_resume else None,
            "report_summary": report_summary,
            "section_timings": section_timings,
            "mode": "incremental",
        }
        
        # Final complete event
        final_event = {
            "event_type": "complete",
            "status": "complete",
            "state": final_state,
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
