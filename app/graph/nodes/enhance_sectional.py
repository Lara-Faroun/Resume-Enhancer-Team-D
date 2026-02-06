"""
Sectional enhancement node: enhances resume section-by-section sequentially
with per-section error handling and safe fallbacks.

This mode is non-streaming and returns a single final JSON response with:
- Enhanced sections that succeeded
- Original sections as fallback for any that failed
- Section-level error tracking for diagnostics

Key features:
- One LLM prompt per section (summary, experiences, skills, projects, etc.)
- Each section prompt only modifies its own section
- Reuses the mapping result as shared context
- Sequential execution with graceful degradation
- Safe fallback: if a section fails, use original data
"""
import logging
import time
from typing import Any, Dict, List, Optional, Type
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

logger = logging.getLogger(__name__)

# Section order and their corresponding output schemas
SECTIONAL_SECTIONS: List[tuple] = [
    ("summary", SummaryEnhancementOutput),
    ("experiences", ExperiencesEnhancementOutput),
    ("educations", EducationsEnhancementOutput),
    ("skills", SkillsEnhancementOutput),
    ("certifications", CertificationsEnhancementOutput),
    ("languages", LanguagesEnhancementOutput),
    ("projects", ProjectsEnhancementOutput),
]

# Retry configuration for transient errors (rate limits, timeouts)
SECTIONAL_MAX_RETRIES = 2
SECTIONAL_RETRY_DELAYS = [1, 3]  # seconds between retries

# Per-section timeout (seconds)
SECTIONAL_TIMEOUT = 15


# Sectional-specific system prompt emphasizing single-section focus
SECTIONAL_SYSTEM_PROMPT = """You are an expert resume writer helping a candidate tailor
their resume to a specific job description.

Your task is to enhance ONLY the specified section of the resume while strictly following
these rules:

- Do NOT invent or fabricate experience, skills, certifications, or projects.
- Do NOT add technologies or information that are not present in the original resume.
- Focus ONLY on the section specified in the task. Do NOT modify other sections.
- You may:
  - Rephrase bullet points and descriptions for clarity and impact.
  - Reorder content to better highlight relevance to the job.
  - Emphasize experiences, skills, and projects that match the job description
    and the provided mapping.
- Keep all facts consistent with the original resume.
- If the section is empty in the original resume, you MUST leave it empty.

You will receive the full resume for context, but you must ONLY return the enhanced
version of the specified section along with reasons for any changes made.
"""


def _build_sectional_prompt(
    section_name: str,
    resume_json: str,
    mapping_result_json: str
) -> str:
    """
    Build a focused prompt for enhancing a single section.
    
    The prompt provides full resume and mapping context but explicitly
    instructs the LLM to only modify the specified section.
    """
    section_display = section_name.replace("_", " ").title()
    output_class_name = f"{section_name.capitalize()}EnhancementOutput"
    
    return f"""## Full Resume (for context only)
{resume_json}

## Mapping Result (job description alignment)
{mapping_result_json}

## Your Task
Enhance ONLY the '{section_display}' section of the resume.

**Critical Rules:**
1. Do NOT invent or fabricate any information
2. Do NOT add technologies or skills not already in the original resume
3. Focus ONLY on improving the '{section_display}' section
4. Preserve all factual information from the original
5. If the original '{section_display}' section is empty, return it empty

**What you CAN do:**
- Rephrase for clarity, impact, and professional tone
- Reorder items to highlight relevance to the job description
- Emphasize content that aligns with matched_skills and matched_requirements
- Add action verbs and quantifiable achievements where data exists

Return a {output_class_name} object with:
- enhanced: The improved {section_display} content (same structure as original)
- reasons: List of ChangeReason objects explaining each modification
"""


def _extract_inputs_sectional(state: ResumeEnhancerState) -> tuple:
    """Extract resume and mapping_result from state (dict or Pydantic)."""
    if isinstance(state, dict):
        resume = state.get("resume")
        mapping_result = state.get("mapping_result")
    else:
        resume = state.resume
        mapping_result = state.mapping_result
    
    if resume is None:
        raise ValueError("enhance_sectional_node requires state.resume")
    if mapping_result is None:
        raise ValueError("enhance_sectional_node requires state.mapping_result")
    
    return resume, mapping_result


def _enhance_single_section(
    section_name: str,
    output_class: Type[BaseModel],
    resume_json: str,
    mapping_result_json: str,
    llm: BaseChatModel,
) -> tuple[Optional[BaseModel], Optional[str]]:
    """
    Enhance a single section with retry logic.
    
    Returns:
        Tuple of (result, error_message)
        - On success: (SectionEnhancementOutput, None)
        - On failure: (None, error_message)
    """
    last_error = None
    
    for attempt in range(SECTIONAL_MAX_RETRIES):
        try:
            # Build section-specific prompt
            user_message = _build_sectional_prompt(
                section_name=section_name,
                resume_json=resume_json,
                mapping_result_json=mapping_result_json,
            )
            
            # Call LLM with structured output
            structured_llm = llm.with_structured_output(output_class)
            result = structured_llm.invoke(
                [
                    SystemMessage(content=SECTIONAL_SYSTEM_PROMPT),
                    HumanMessage(content=user_message),
                ],
                config={"timeout": SECTIONAL_TIMEOUT}
            )
            
            # Validate result type
            if not isinstance(result, output_class):
                raise ValueError(
                    f"LLM returned {type(result).__name__} instead of {output_class.__name__}"
                )
            
            # Success
            return result, None
            
        except Exception as e:
            last_error = str(e)
            logger.warning(
                f"enhance_sectional: {section_name} attempt {attempt + 1}/{SECTIONAL_MAX_RETRIES} failed: {e}"
            )
            
            if attempt < SECTIONAL_MAX_RETRIES - 1:
                # Wait before retry (handles rate limits)
                time.sleep(SECTIONAL_RETRY_DELAYS[attempt])
    
    # All retries exhausted
    return None, last_error


def enhance_sectional_node(
    state: ResumeEnhancerState,
    llm: BaseChatModel
) -> Dict[str, Any]:
    """
    Enhance resume section-by-section with per-section error handling.
    
    This is a non-streaming mode that processes all sections sequentially
    and returns a single comprehensive result.
    
    Inputs:
    - state.resume: Resume
    - state.mapping_result: MappingResult
    - llm: LangChain chat model
    
    Outputs:
    - state.full_enhancement_output: FullEnhancementOutput (with successful sections)
    - state.section_errors: Dict[str, str] (section_name -> error message)
    - state.section_timings: Dict[str, float] (ms per section)
    - state.sectional_metadata: Dict with processing summary
    
    Behavior:
    - Processes each section independently
    - If a section fails, applies safe fallback (keeps original)
    - Continues processing remaining sections on failure
    - Returns combined result with error tracking
    """
    logger.info("enhance_sectional_node: starting")
    start_time = time.time()
    
    try:
        resume, mapping_result = _extract_inputs_sectional(state)
    except ValueError as e:
        logger.error(f"enhance_sectional_node: {e}")
        raise
    
    if llm is None:
        raise ValueError("enhance_sectional_node requires a non-None llm instance")
    
    # Initialize accumulators
    full_output = FullEnhancementOutput()
    section_errors: Dict[str, str] = {}
    section_timings: Dict[str, float] = {}
    sections_succeeded: List[str] = []
    sections_failed: List[str] = []
    
    # Prepare JSON representations (reused for all sections)
    resume_json = resume.model_dump_json(indent=2)
    mapping_result_json = mapping_result.model_dump_json(indent=2)
    
    total_sections = len(SECTIONAL_SECTIONS)
    
    # Process each section sequentially
    for section_index, (section_name, output_class) in enumerate(SECTIONAL_SECTIONS):
        section_start = time.time()
        
        logger.info(
            f"enhance_sectional_node: processing {section_name} "
            f"(section {section_index + 1}/{total_sections})"
        )
        
        # Attempt to enhance this section
        result, error = _enhance_single_section(
            section_name=section_name,
            output_class=output_class,
            resume_json=resume_json,
            mapping_result_json=mapping_result_json,
            llm=llm,
        )
        
        section_elapsed = (time.time() - section_start) * 1000
        section_timings[section_name] = section_elapsed
        
        if result is not None:
            # Success - store enhanced section
            setattr(full_output, section_name, result)
            sections_succeeded.append(section_name)
            logger.info(
                f"enhance_sectional_node: {section_name} completed "
                f"in {section_elapsed:.0f}ms"
            )
        else:
            # Failure - record error, original will be used as fallback by format node
            section_errors[section_name] = error or "Unknown error"
            sections_failed.append(section_name)
            logger.warning(
                f"enhance_sectional_node: {section_name} failed after "
                f"{section_elapsed:.0f}ms - will use original as fallback"
            )
    
    total_elapsed = (time.time() - start_time) * 1000
    
    # Build metadata summary
    sectional_metadata = {
        "mode": "sectional",
        "total_sections": total_sections,
        "sections_succeeded": len(sections_succeeded),
        "sections_failed": len(sections_failed),
        "succeeded_list": sections_succeeded,
        "failed_list": sections_failed,
        "total_time_ms": round(total_elapsed, 2),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    
    logger.info(
        f"enhance_sectional_node: completed in {total_elapsed:.0f}ms - "
        f"succeeded={len(sections_succeeded)}/{total_sections}, "
        f"failed={len(sections_failed)}"
    )
    
    if sections_failed:
        logger.warning(
            f"enhance_sectional_node: failed sections will use original data: "
            f"{sections_failed}"
        )
    
    return {
        "full_enhancement_output": full_output,
        "section_errors": section_errors,
        "section_timings": section_timings,
        "sectional_metadata": sectional_metadata,
    }
