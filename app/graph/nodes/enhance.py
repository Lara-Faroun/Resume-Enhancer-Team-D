"""
Enhance node: takes resume + mapping_result and produces
FullEnhancementOutput (enhanced sections + reasons).

This node is provider-agnostic: it expects a LangChain chat model instance,
which is created once at app startup in main.py (Gemini or OpenAI) and passed
into the graph when wiring nodes.
"""
import logging
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import ResumeEnhancerState
from llm.prompts import ENHANCE_SYSTEM, build_enhance_prompt_user
from schemas.enhancement import FullEnhancementOutput

logger = logging.getLogger(__name__)


def _get_enhancement_inputs(
    state: ResumeEnhancerState,
) -> tuple[Any, Any]:
    """Extract resume and mapping_result from state."""
    resume = state.resume if not isinstance(state, dict) else state.get("resume")
    mapping_result = (
        state.mapping_result
        if not isinstance(state, dict)
        else state.get("mapping_result")
    )

    if resume is None:
        logger.error("enhance_node: state.resume is missing")
        raise ValueError("enhance_node requires state.resume")
    if mapping_result is None:
        logger.error("enhance_node: state.mapping_result is missing")
        raise ValueError("enhance_node requires state.mapping_result")

    return resume, mapping_result


def enhance_node(state: ResumeEnhancerState, llm: BaseChatModel) -> dict[str, Any]:
    """
    Enhance resume sections according to the mapping_result.

    Inputs:
    - state.resume: Resume
    - state.mapping_result: MappingResult
    - llm: LangChain chat model (Gemini or OpenAI), initialized once in main.py

    Output:
    - state.full_enhancement_output: FullEnhancementOutput
    """
    logger.info("enhance_node: starting")
    resume, mapping_result = _get_enhancement_inputs(state)
    
    # Extract reflection feedback if available
    feedback = state.reflection_feedback if not isinstance(state, dict) else state.get("reflection_feedback")

    if llm is None:
        logger.error("enhance_node: llm instance is None")
        raise ValueError("enhance_node requires a non-None llm instance")


    structured_llm = llm.with_structured_output(FullEnhancementOutput)

    resume_json = resume.model_dump_json(indent=2)
    mapping_result_json = mapping_result.model_dump_json(indent=2)
    user_message = build_enhance_prompt_user(
        resume_json=resume_json,
        mapping_result_json=mapping_result_json,
        feedback=feedback
    )

    try:
        result = structured_llm.invoke(
            [
                SystemMessage(content=ENHANCE_SYSTEM),
                HumanMessage(content=user_message),
            ]
        )
    except Exception as e:
        logger.exception("enhance_node: LLM call failed: %s", e)
        raise

    if not isinstance(result, FullEnhancementOutput):
        logger.error(
            "enhance_node: LLM did not return FullEnhancementOutput, got %s",
            type(result),
        )
        raise ValueError("enhance_node: LLM must return FullEnhancementOutput")

    # Basic logging about what was enhanced (presence of sections)
    logger.info(
        "enhance_node: done summary=%s experiences=%s educations=%s "
        "skills=%s certifications=%s languages=%s projects=%s",
        result.summary is not None,
        result.experiences is not None,
        result.educations is not None,
        result.skills is not None,
        result.certifications is not None,
        result.languages is not None,
        result.projects is not None,
    )

    return {"full_enhancement_output": result}

