"""
Mapping node: compares JD schema vs Resume schema and produces
matched_skills, matched_requirements, gaps, and match_score (1-10).

This node is provider-agnostic: it expects a LangChain chat model instance,
which is created once at app startup in main.py (Gemini or OpenAI) and
passed into the graph when wiring nodes.
"""
import logging
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from graph.utils import log_node_timing
from schemas.mapping_result import MappingResult
from schemas.resume import Resume
from schemas.job_description import JobDescription
from graph.state import ResumeEnhancerState, normalize_state
from llm.prompts.mapping import MAP_RESUME_JD_SYSTEM, build_mapping_prompt_user

logger = logging.getLogger(__name__)


def _validate_and_normalize_mapping_result(result: MappingResult) -> MappingResult:
    """
    Validate mapping result and ensure list fields are present (default to empty).
    Makes mapping output deterministic and safe for downstream nodes.
    """
    if not (1 <= result.match_score <= 10):
        logger.error(
            "mapping_node: match_score out of range [1, 10], got %s",
            result.match_score,
        )
        raise ValueError(
            f"mapping_node: match_score must be between 1 and 10, got {result.match_score}"
        )
    matched_skills = result.matched_skills if result.matched_skills is not None else []
    matched_requirements = (
        result.matched_requirements if result.matched_requirements is not None else []
    )
    gaps = result.gaps if result.gaps is not None else []
    return MappingResult(
        matched_skills=matched_skills,
        matched_requirements=matched_requirements,
        gaps=gaps,
        match_score=result.match_score,
    )


def _get_resume_and_jd(state: ResumeEnhancerState) -> tuple[Resume, JobDescription]:
    """Extract resume and job_description from state."""
    resume = state.resume
    job_description = state.job_description
    if resume is None:
        logger.error("mapping_node: state.resume is missing")
        raise ValueError("mapping_node requires state.resume")
    if job_description is None:
        logger.error("mapping_node: state.job_description is missing")
        raise ValueError("mapping_node requires state.job_description")
    return resume, job_description


@log_node_timing("mapping")
async def mapping_node(state: ResumeEnhancerState, llm: BaseChatModel) -> dict[str, Any]:
    """
    Compare resume to job description and produce MappingResult.

    Inputs:
    - state.resume: Resume
    - state.job_description: JobDescription
    - llm: LangChain chat model (Gemini or OpenAI), initialized once in main.py

    Output:
    - state.mapping_result: MappingResult
    """
    logger.info("mapping_node: starting")
    state = normalize_state(state)
    resume, job_description = _get_resume_and_jd(state)

    if llm is None:
        logger.error("mapping_node: llm instance is None")
        raise ValueError("mapping_node requires a non-None llm instance")

    structured_llm = llm.with_structured_output(MappingResult)

    job_description_json = job_description.model_dump_json()
    resume_json = resume.model_dump_json()
    user_message = build_mapping_prompt_user(job_description_json, resume_json)

    try:
        result = await structured_llm.ainvoke(
            [
                SystemMessage(content=MAP_RESUME_JD_SYSTEM),
                HumanMessage(content=user_message),
            ]
        )
    except Exception as e:
        logger.exception("mapping_node: LLM call failed: %s", e)
        raise

    if not isinstance(result, MappingResult):
        logger.error(
            "mapping_node: LLM did not return MappingResult, got %s", type(result)
        )
        raise ValueError("mapping_node: LLM must return MappingResult")

    result = _validate_and_normalize_mapping_result(result)

    logger.info(
        "mapping_node: done score=%s matched_skills=%s matched_reqs=%s gaps=%s",
        result.match_score,
        len(result.matched_skills),
        len(result.matched_requirements),
        len(result.gaps),
    )
    return {"mapping_result": result}
