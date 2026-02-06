"""
Report node: collect all ChangeReason entries from FullEnhancementOutput,
pass them to the LLM, and store the resulting summary in state.report_summary
for human-in-the-loop review.
"""
import logging
from typing import Any, List

from langchain_core.language_models.chat_models import BaseChatModel
from graph.utils import log_node_timing
from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import ResumeEnhancerState, normalize_state
from llm.prompts import FEEDBACK_REPORT_SYSTEM, build_report_prompt_user
from schemas.enhancement import FullEnhancementOutput, ChangeReason

logger = logging.getLogger(__name__)


def _get_full_output(state: ResumeEnhancerState) -> FullEnhancementOutput:
    """
    Extract full_enhancement_output from state, with validation.
    """
    full_output = state.full_enhancement_output
    if full_output is None:
        logger.error("report_node: state.full_enhancement_output is missing")
        raise ValueError("report_node requires state.full_enhancement_output")

    return full_output


def _collect_reasons(full_output: FullEnhancementOutput) -> List[ChangeReason]:
    """
    Collect ChangeReason entries from all sections in FullEnhancementOutput.
    """
    reasons: List[ChangeReason] = []

    # Summary
    if full_output.summary is not None:
        reasons.extend(full_output.summary.reasons)

    # Experiences
    if full_output.experiences is not None:
        reasons.extend(full_output.experiences.reasons)

    # Educations
    if full_output.educations is not None:
        reasons.extend(full_output.educations.reasons)

    # Skills
    if full_output.skills is not None:
        reasons.extend(full_output.skills.reasons)

    # Certifications
    if full_output.certifications is not None:
        reasons.extend(full_output.certifications.reasons)

    # Languages
    if full_output.languages is not None:
        reasons.extend(full_output.languages.reasons)

    # Projects
    if full_output.projects is not None:
        reasons.extend(full_output.projects.reasons)

    return reasons


def _reasons_to_text(reasons: List[ChangeReason]) -> str:
    """Format the list of ChangeReason for the LLM (one change per line)."""
    if not reasons:
        return ""
    lines = []
    for r in reasons:
        lines.append(f"- {r.field_or_location}: {r.reason}")
    return "\n".join(lines)


@log_node_timing("report")
async def report_node(state: ResumeEnhancerState, llm: BaseChatModel) -> dict[str, Any]:
    """
    Collect change reasons from FullEnhancementOutput, ask the LLM to
    summarize them, and store only the summary in state.report_summary.

    Input:
    - state.full_enhancement_output: FullEnhancementOutput
    - llm: LangChain chat model (injected by graph)

    Output:
    - state.report_summary: str (LLM-generated summary)
    """
    logger.info("report_node: starting")
    state = normalize_state(state)
    try:
        full_output = _get_full_output(state)
        reasons = _collect_reasons(full_output)
    except Exception as e:
        logger.exception("report_node: failed to collect reasons: %s", e)
        raise

    logger.info("report_node: reasons_count=%s", len(reasons))

    report_summary = None
    if llm is not None and reasons:
        try:
            change_reasons_text = _reasons_to_text(reasons)
            user_message = build_report_prompt_user(change_reasons_text)
            result = await llm.ainvoke(
                [
                    SystemMessage(content=FEEDBACK_REPORT_SYSTEM),
                    HumanMessage(content=user_message),
                ]
            )
            message_text = getattr(result, "content", None)
            if isinstance(message_text, str) and message_text.strip():
                report_summary = message_text.strip()
            else:
                logger.warning(
                    "report_node: LLM returned empty or non-string content, using empty summary"
                )
        except Exception as e:
            logger.exception("report_node: LLM summary failed: %s", e)

    return {"report_summary": report_summary}
