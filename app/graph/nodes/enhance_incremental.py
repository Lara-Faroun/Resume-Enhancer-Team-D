"""
Incremental enhancement node: enhances resume section-by-section,
emitting progress events after each section completes.
"""
import logging
import time
from typing import Any, Dict, List, Type
from datetime import datetime

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from graph.state import ResumeEnhancerState
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
from llm.prompts.enhance import build_section_prompt_user, ENHANCE_SYSTEM

logger = logging.getLogger(__name__)

# Section order and their corresponding output schemas
SECTIONS: List[tuple] = [
    ("summary", SummaryEnhancementOutput),
    ("experiences", ExperiencesEnhancementOutput),
    ("educations", EducationsEnhancementOutput),
    ("skills", SkillsEnhancementOutput),
    ("certifications", CertificationsEnhancementOutput),
    ("languages", LanguagesEnhancementOutput),
    ("projects", ProjectsEnhancementOutput),
]

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  # seconds


def _extract_inputs(state: ResumeEnhancerState) -> tuple:
    """Extract resume and mapping_result from state (dict or Pydantic)."""
    if isinstance(state, dict):
        resume = state.get("resume")
        mapping_result = state.get("mapping_result")
    else:
        resume = state.resume
        mapping_result = state.mapping_result
    
    if resume is None:
        raise ValueError("enhance_incremental_node requires state.resume")
    if mapping_result is None:
        raise ValueError("enhance_incremental_node requires state.mapping_result")
    
    return resume, mapping_result


def _create_event(
    event_type: str,
    section: str = None,
    status: str = None,
    partial_payload: Dict[str, Any] = None,
    elapsed_ms: float = 0,
    token_usage: Dict[str, int] = None,
    error_message: str = None,
    section_index: int = None,
    progress_percent: float = None,
) -> Dict[str, Any]:
    """Create a progress event dict."""
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
    if partial_payload is not None:
        event["partial_payload"] = partial_payload
    if token_usage is not None:
        event["token_usage"] = token_usage
    if error_message is not None:
        event["error_message"] = error_message
    if progress_percent is not None:
        event["progress_percent"] = round(progress_percent, 1)
    
    return event


def enhance_incremental_node(
    state: ResumeEnhancerState,
    llm: BaseChatModel
) -> Dict[str, Any]:
    """
    Enhance resume section-by-section with progress events.
    
    Inputs:
    - state.resume: Resume
    - state.mapping_result: MappingResult
    - llm: LangChain chat model
    
    Outputs:
    - state.full_enhancement_output: FullEnhancementOutput
    - state.progress_events: List[Dict] (events emitted during processing)
    - state.section_timings: Dict[str, float] (ms per section)
    - state.token_usage: Dict[str, Dict[str, int]] (tokens per section)
    """
    logger.info("enhance_incremental_node: starting")
    
    try:
        resume, mapping_result = _extract_inputs(state)
    except ValueError as e:
        logger.error(f"enhance_incremental_node: {e}")
        raise
    
    if llm is None:
        raise ValueError("enhance_incremental_node requires a non-None llm instance")
    
    # Initialize accumulators
    full_output = FullEnhancementOutput()
    progress_events: List[Dict[str, Any]] = []
    section_timings: Dict[str, float] = {}
    token_usage_dict: Dict[str, Dict[str, int]] = {}
    
    # Prepare JSON representations (reused for all sections)
    resume_json = resume.model_dump_json(indent=2)
    mapping_result_json = mapping_result.model_dump_json(indent=2)
    
    start_time = time.time()
    total_sections = len(SECTIONS)
    
    # Process each section
    for section_index, (section_name, output_class) in enumerate(SECTIONS):
        section_start = time.time()
        elapsed_so_far = (section_start - start_time) * 1000
        progress_percent = (section_index / total_sections) * 100
        
        # Emit section_start event
        start_event = _create_event(
            event_type="section_start",
            section=section_name,
            section_index=section_index,
            status="in_progress",
            elapsed_ms=elapsed_so_far,
            progress_percent=progress_percent,
        )
        progress_events.append(start_event)
        logger.info(f"enhance_incremental_node: {section_name} starting (section {section_index + 1}/{total_sections})")
        
        # Retry logic
        result = None
        last_error = None
        
        for attempt in range(MAX_RETRIES):
            try:
                # Build section-specific prompt
                user_message = build_section_prompt_user(
                    section_name=section_name,
                    resume_json=resume_json,
                    mapping_result_json=mapping_result_json,
                )
                
                # Call LLM with structured output and timeout
                structured_llm = llm.with_structured_output(output_class)
                result = structured_llm.invoke(
                    [
                        SystemMessage(content=ENHANCE_SYSTEM),
                        HumanMessage(content=user_message),
                    ],
                    config={"timeout": 10}  # 10s timeout per section
                )
                
                # Validate result type
                if not isinstance(result, output_class):
                    raise ValueError(
                        f"LLM returned {type(result)} instead of {output_class}"
                    )
                
                # Success - break retry loop
                break
                
            except Exception as e:
                last_error = e
                logger.warning(
                    f"enhance_incremental_node: {section_name} attempt {attempt + 1}/{MAX_RETRIES} failed: {e}"
                )
                
                if attempt < MAX_RETRIES - 1:
                    # Wait before retry
                    time.sleep(RETRY_DELAYS[attempt])
                else:
                    # Final failure
                    logger.error(
                        f"enhance_incremental_node: {section_name} failed after {MAX_RETRIES} attempts"
                    )
        
        # Check if we got a result
        if result is not None:
            # Store in FullEnhancementOutput
            setattr(full_output, section_name, result)
            
            # Calculate timing
            section_elapsed = (time.time() - section_start) * 1000
            section_timings[section_name] = section_elapsed
            
            # TODO: Extract token usage from LLM response metadata
            # For now, placeholder
            token_usage_dict[section_name] = {"input": 0, "output": 0}
            
            # Emit section_complete event
            progress_percent = ((section_index + 1) / total_sections) * 100
            complete_event = _create_event(
                event_type="section_complete",
                section=section_name,
                section_index=section_index,
                status="complete",
                partial_payload={section_name: result.model_dump(mode="json")},
                elapsed_ms=(time.time() - start_time) * 1000,
                token_usage=token_usage_dict[section_name],
                progress_percent=progress_percent,
            )
            progress_events.append(complete_event)
            
            logger.info(
                f"enhance_incremental_node: {section_name} complete "
                f"in {section_elapsed:.0f}ms"
            )
        else:
            # Section failed - emit error event
            error_event = _create_event(
                event_type="error",
                section=section_name,
                section_index=section_index,
                status="error",
                error_message=str(last_error),
                elapsed_ms=(time.time() - start_time) * 1000,
            )
            progress_events.append(error_event)
            
            # Continue with other sections (partial results better than none)
            logger.warning(f"enhance_incremental_node: continuing despite {section_name} failure")
    
    total_elapsed = (time.time() - start_time) * 1000
    logger.info(
        f"enhance_incremental_node: done in {total_elapsed:.0f}ms, "
        f"sections_completed={len(section_timings)}/{len(SECTIONS)}"
    )
    
    return {
        "full_enhancement_output": full_output,
        "progress_events": progress_events,
        "section_timings": section_timings,
        "token_usage": token_usage_dict,
    }
