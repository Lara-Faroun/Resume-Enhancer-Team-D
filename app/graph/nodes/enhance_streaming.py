"""
Real-time streaming enhancement for incremental mode.

This module provides true token-by-token streaming for the enhancement process,
emitting section_delta events as text is generated (every 200-500ms).

Key features:
- Uses LLM streaming to get tokens as they're generated
- Emits section_delta events with partial text chunks
- Emits section_complete events with final aggregated text
- Works with asyncio for non-blocking streaming
"""
import logging
import time
import json
import asyncio
from typing import Any, Dict, List, AsyncGenerator, Optional
from datetime import datetime

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from schemas.resume import Resume
from schemas.mapping_result import MappingResult
from schemas.enhancement import (
    FullEnhancementOutput,
    SummaryEnhancementOutput,
    ExperiencesEnhancementOutput,
    EducationsEnhancementOutput,
    SkillsEnhancementOutput,
    CertificationsEnhancementOutput,
    LanguagesEnhancementOutput,
    ProjectsEnhancementOutput,
)
from llm.prompts.enhance import ENHANCE_SYSTEM

logger = logging.getLogger(__name__)

# Section order and their corresponding output schemas
STREAMING_SECTIONS: List[tuple] = [
    ("summary", SummaryEnhancementOutput),
    ("experiences", ExperiencesEnhancementOutput),
    ("educations", EducationsEnhancementOutput),
    ("skills", SkillsEnhancementOutput),
    ("certifications", CertificationsEnhancementOutput),
    ("languages", LanguagesEnhancementOutput),
    ("projects", ProjectsEnhancementOutput),
]

# Streaming configuration
DELTA_INTERVAL_MS = 250  # Emit delta every 250ms (200-500ms range)
MIN_CHUNK_SIZE = 10  # Minimum characters before emitting a delta
MAX_RETRIES = 2
RETRY_DELAY = 1


def _build_streaming_section_prompt(
    section_name: str,
    resume_json: str,
    mapping_result_json: str
) -> str:
    """Build prompt for streaming a single section."""
    section_display = section_name.replace("_", " ").title()
    
    return f"""## Resume (structured)
{resume_json}

## Mapping result (structured)
{mapping_result_json}

## Task
Enhance ONLY the '{section_display}' section of the resume following these rules:

1. Do NOT invent or fabricate information
2. Do NOT add technologies not in the original resume  
3. You may:
   - Rephrase for clarity and impact
   - Reorder content to highlight relevance
   - Emphasize matches with the job description
4. Keep all facts consistent with the original
5. If the section is empty in the original, leave it empty
6. For date fields (issue_date, start_date, end_date), use ISO format: YYYY-MM-DD or YYYY-MM. Do NOT use formats like "May 2023" or "August 2023".
7. For proficiency_level in languages, use ONLY: A1, A2, B1, B2, C1, C2, or Native. Do NOT use forms like "Advanced (C1)" or "C1 - Advanced".
8. Do NOT change start_date, end_date. Preserve them exactly as in the original resume (same format and value).

Return your response as valid JSON with this exact structure:
{{
  "enhanced": <the enhanced {section_display} content>,
  "reasons": [
    {{"field_or_location": "<what changed>", "reason": "<why>"}},
    ...
  ]
}}

For summary, "enhanced" should be a string.
For other sections (experiences, skills, etc.), "enhanced" should be an array.

Output ONLY the JSON, no other text."""


def _create_streaming_event(
    event_type: str,
    section: str = None,
    section_index: int = None,
    status: str = None,
    delta_text: str = None,
    accumulated_text: str = None,
    partial_payload: Dict[str, Any] = None,
    elapsed_ms: float = 0,
    progress_percent: float = None,
    error_message: str = None,
) -> Dict[str, Any]:
    """Create a streaming event dict."""
    event = {
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "elapsed_ms": round(elapsed_ms, 2),
    }
    
    if section is not None:
        event["section"] = section
    if section_index is not None:
        event["section_index"] = section_index
    if status is not None:
        event["status"] = status
    if delta_text is not None:
        event["delta_text"] = delta_text
    if accumulated_text is not None:
        event["accumulated_text"] = accumulated_text
    if partial_payload is not None:
        event["partial_payload"] = partial_payload
    if progress_percent is not None:
        event["progress_percent"] = round(progress_percent, 1)
    if error_message is not None:
        event["error_message"] = error_message
    
    return event


def _parse_section_json(raw_text: str, section_name: str, output_class) -> Optional[BaseModel]:
    """
    Try to parse the accumulated text as JSON and validate against schema.
    Returns None if parsing fails.
    """
    try:
        # Clean up the text - remove markdown code blocks if present
        text = raw_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        # Try to parse as JSON
        data = json.loads(text)
        
        # Validate against the output class
        result = output_class(**data)
        return result
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.debug("_parse_section_json: failed to parse %s: %s", section_name, e)
        return None


async def stream_section_enhancement(
    section_name: str,
    section_index: int,
    output_class,
    resume_json: str,
    mapping_result_json: str,
    llm: BaseChatModel,
    start_time: float,
    total_sections: int,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Stream the enhancement of a single section with delta events.
    
    Yields:
        - section_start event
        - section_delta events (every DELTA_INTERVAL_MS with accumulated text)
        - section_complete event (with final parsed result)
        OR
        - error event (if enhancement fails)
    """
    section_start_time = time.time()
    elapsed_so_far = (section_start_time - start_time) * 1000
    progress_base = (section_index / total_sections) * 100
    
    # Emit section_start
    yield _create_streaming_event(
        event_type="section_start",
        section=section_name,
        section_index=section_index,
        status="streaming",
        elapsed_ms=elapsed_so_far,
        progress_percent=progress_base,
    )
    
    logger.info(f"stream_section_enhancement: {section_name} starting")
    
    # Build the prompt
    user_message = _build_streaming_section_prompt(
        section_name=section_name,
        resume_json=resume_json,
        mapping_result_json=mapping_result_json,
    )
    
    messages = [
        SystemMessage(content=ENHANCE_SYSTEM),
        HumanMessage(content=user_message),
    ]
    
    accumulated_text = ""
    last_delta_time = time.time()
    last_sent_length = 0
    result = None
    last_error = None
    
    for attempt in range(MAX_RETRIES):
        try:
            accumulated_text = ""
            last_delta_time = time.time()
            last_sent_length = 0
            
            # Use streaming LLM call
            async for chunk in llm.astream(messages):
                # Extract text content from chunk
                chunk_text = ""
                if hasattr(chunk, 'content'):
                    chunk_text = chunk.content or ""
                elif isinstance(chunk, str):
                    chunk_text = chunk
                elif isinstance(chunk, dict):
                    chunk_text = chunk.get('content', '') or chunk.get('text', '')
                
                if chunk_text:
                    accumulated_text += chunk_text
                
                # Check if it's time to emit a delta
                now = time.time()
                time_since_last = (now - last_delta_time) * 1000
                new_chars = len(accumulated_text) - last_sent_length
                
                if time_since_last >= DELTA_INTERVAL_MS and new_chars >= MIN_CHUNK_SIZE:
                    # Emit section_delta with the new chunk
                    delta_text = accumulated_text[last_sent_length:]
                    elapsed_ms = (now - start_time) * 1000
                    
                    # Calculate progress within section (estimate based on typical response length)
                    section_progress = min(0.9, len(accumulated_text) / 2000)  # Cap at 90%
                    progress_percent = progress_base + (section_progress / total_sections) * 100
                    
                    yield _create_streaming_event(
                        event_type="section_delta",
                        section=section_name,
                        section_index=section_index,
                        status="streaming",
                        delta_text=delta_text,
                        accumulated_text=accumulated_text,
                        elapsed_ms=elapsed_ms,
                        progress_percent=progress_percent,
                    )
                    
                    last_delta_time = now
                    last_sent_length = len(accumulated_text)
            
            # Streaming complete - try to parse the result
            result = _parse_section_json(accumulated_text, section_name, output_class)
            
            if result is not None:
                # Success
                break
            else:
                # Parsing failed - might need retry
                last_error = f"Failed to parse LLM response as valid JSON for {section_name}"
                logger.warning(f"stream_section_enhancement: {last_error}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)
                    
        except Exception as e:
            last_error = str(e)
            logger.warning(
                f"stream_section_enhancement: {section_name} attempt {attempt + 1}/{MAX_RETRIES} failed: {e}"
            )
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAY)
    
    section_elapsed = (time.time() - section_start_time) * 1000
    total_elapsed = (time.time() - start_time) * 1000
    progress_percent = ((section_index + 1) / total_sections) * 100
    
    if result is not None:
        # Emit final section_complete with parsed result
        yield _create_streaming_event(
            event_type="section_complete",
            section=section_name,
            section_index=section_index,
            status="complete",
            partial_payload={section_name: result.model_dump(mode="json")},
            elapsed_ms=total_elapsed,
            progress_percent=progress_percent,
        )
        logger.info(f"stream_section_enhancement: {section_name} complete in {section_elapsed:.0f}ms")
    else:
        # Emit error event
        yield _create_streaming_event(
            event_type="error",
            section=section_name,
            section_index=section_index,
            status="error",
            error_message=last_error or "Unknown error",
            elapsed_ms=total_elapsed,
        )
        logger.error(f"stream_section_enhancement: {section_name} failed: {last_error}")


async def stream_all_sections(
    resume: Resume,
    mapping_result: MappingResult,
    llm: BaseChatModel,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Stream enhancement for all sections sequentially.
    
    Yields events for each section including:
    - section_start
    - section_delta (multiple, every 200-500ms)
    - section_complete or error
    
    Returns the final FullEnhancementOutput via the last complete event.
    """
    start_time = time.time()
    total_sections = len(STREAMING_SECTIONS)
    
    # Prepare JSON representations
    resume_json = resume.model_dump_json(indent=2)
    mapping_result_json = mapping_result.model_dump_json(indent=2)
    
    # Accumulator for results
    full_output = FullEnhancementOutput()
    section_timings: Dict[str, float] = {}
    
    logger.info("stream_all_sections: starting real-time streaming")
    
    for section_index, (section_name, output_class) in enumerate(STREAMING_SECTIONS):
        section_start = time.time()
        section_result = None
        
        # Stream this section
        async for event in stream_section_enhancement(
            section_name=section_name,
            section_index=section_index,
            output_class=output_class,
            resume_json=resume_json,
            mapping_result_json=mapping_result_json,
            llm=llm,
            start_time=start_time,
            total_sections=total_sections,
        ):
            yield event
            
            # Capture the result from section_complete
            if event.get("event_type") == "section_complete":
                payload = event.get("partial_payload", {})
                if section_name in payload:
                    try:
                        section_result = output_class(**payload[section_name])
                    except Exception as e:
                        logger.warning(f"Failed to reconstruct {section_name}: {e}")
        
        # Store result if we got one
        if section_result is not None:
            setattr(full_output, section_name, section_result)
            section_timings[section_name] = (time.time() - section_start) * 1000
    
    total_elapsed = (time.time() - start_time) * 1000
    logger.info(
        f"stream_all_sections: done in {total_elapsed:.0f}ms, "
        f"sections_completed={len(section_timings)}/{total_sections}"
    )
    
    # Return accumulated results via state (for downstream nodes)
    yield {
        "event_type": "_internal_results",
        "full_enhancement_output": full_output,
        "section_timings": section_timings,
    }
