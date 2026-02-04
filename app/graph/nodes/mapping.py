"""
Mapping node: compares JD schema vs Resume schema and produces
matched_skills, matched_requirements, gaps, and match_score (1-10).

This node is provider-agnostic: it expects a LangChain chat model instance,
which is created once at app startup in main.py (Gemini or OpenAI) and
passed into the graph when wiring nodes.
"""
import logging
from typing import Any
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
from schemas.mapping_result import MappingResult
from schemas.resume import Resume
from schemas.job_description import JobDescription
from graph.state import ResumeEnhancerState
from llm.prompts.mapping import MAP_RESUME_JD_SYSTEM, build_mapping_prompt_user

logger = logging.getLogger(__name__)


def _get_resume_and_jd(state: ResumeEnhancerState) -> tuple[Resume, JobDescription]:
    """Extract resume and job_description from state (dict or Pydantic)."""
    if isinstance(state, dict):
        resume = state.get("resume")
        job_description = state.get("job_description")
    else:
        resume = getattr(state, "resume", None)
        job_description = getattr(state, "job_description", None)
    if resume is None:
        logger.error("mapping_node: state.resume is missing")
        raise ValueError("mapping_node requires state.resume")
    if job_description is None:
        logger.error("mapping_node: state.job_description is missing")
        raise ValueError("mapping_node requires state.job_description")
    return resume, job_description


def mapping_node(state: ResumeEnhancerState, llm: BaseChatModel) -> dict[str, Any]:
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
    resume, job_description = _get_resume_and_jd(state)

    if llm is None:
        logger.error("mapping_node: llm instance is None")
        raise ValueError("mapping_node requires a non-None llm instance")

    structured_llm = llm.with_structured_output(MappingResult)

    job_description_json = job_description.model_dump_json(indent=2)
    resume_json = resume.model_dump_json(indent=2)
    user_message = build_mapping_prompt_user(job_description_json, resume_json)

    try:
        result = structured_llm.invoke(
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

    logger.info(
        "mapping_node: done score=%s matched_skills=%s matched_reqs=%s gaps=%s",
        result.match_score,
        len(result.matched_skills),
        len(result.matched_requirements),
        len(result.gaps),
    )
    return {"mapping_result": result}
