"""
Feedback node (low-score path).

When the mapping score is below the configured SCORE_THRESHOLD, this node
calls the LLM to build a friendly, encouraging feedback message explaining
why the profile is not yet a strong match and what gaps to work on.
"""
import logging
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from graph.utils import log_node_timing
from langchain_core.messages import HumanMessage, SystemMessage

from core.config import get_settings
from graph.state import ResumeEnhancerState, normalize_state
from llm.prompts import FEEDBACK_SYSTEM, build_feedback_prompt_user
from schemas.mapping_result import MappingResult

logger = logging.getLogger(__name__)


def _get_mapping_result(state: ResumeEnhancerState) -> MappingResult:
    """
    Extract mapping_result from state, with validation.
    """
    mapping_result = state.mapping_result
    if mapping_result is None:
        logger.error("feedback_node: state.mapping_result is missing")
        raise ValueError("feedback_node requires state.mapping_result")

    return mapping_result


@log_node_timing("feedback")
async def feedback_node(state: ResumeEnhancerState, llm: BaseChatModel) -> dict[str, Any]:
    """
    Low-score feedback path.

    Input:
    - state.mapping_result: MappingResult (score < SCORE_THRESHOLD)
    - llm: LangChain chat model (Gemini or OpenAI), initialized once in main.py

    Output:
    - state.feedback_message: str

    No enhancement state is written on this path; enhanced_resume and
    report_summary remain unset.
    """
    logger.info("feedback_node: starting")
    state = normalize_state(state)
    try:
        mapping_result = _get_mapping_result(state)

        if llm is None:
            logger.error("feedback_node: llm instance is None")
            raise ValueError("feedback_node requires a non-None llm instance")

        score = mapping_result.match_score
        threshold = get_settings().SCORE_THRESHOLD
        mapping_result_json = mapping_result.model_dump_json()
        user_message = build_feedback_prompt_user(
            mapping_result_json=mapping_result_json,
            score=score,
            threshold=threshold,
        )

        result = await llm.ainvoke(
            [
                SystemMessage(content=FEEDBACK_SYSTEM),
                HumanMessage(content=user_message),
            ]
        )

        # LangChain chat models typically return a message object; extract content.
        message_text = getattr(result, "content", None)
        if not isinstance(message_text, str) or not message_text.strip():
            logger.error(
                "feedback_node: LLM returned empty or non-string content, type=%s",
                type(result),
            )
            raise ValueError("feedback_node: LLM must return non-empty text content")

    except Exception as e:
        logger.exception("feedback_node: failed to build feedback: %s", e)
        raise

    logger.info(
        "feedback_node: done score=%s threshold=%s gaps_count=%s",
        mapping_result.match_score,
        threshold,
        len(mapping_result.gaps or []),
    )
    return {"feedback_message": message_text}

