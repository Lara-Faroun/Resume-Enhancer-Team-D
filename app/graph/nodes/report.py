"""
Report node: aggregate all ChangeReason entries from FullEnhancementOutput
into a flat list stored on state.change_report.

This node does not call an LLM; it is pure aggregation logic to support
human-in-the-loop review of changes.
"""
import logging
from typing import Any, List

from graph.state import ResumeEnhancerState
from schemas.enhancement import FullEnhancementOutput, ChangeReason

logger = logging.getLogger(__name__)


def _get_full_output(state: ResumeEnhancerState) -> FullEnhancementOutput:
    """
    Extract full_enhancement_output from state, with validation.
    """
    full_output = (
        state.full_enhancement_output
        if not isinstance(state, dict)
        else state.get("full_enhancement_output")
    )

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


def report_node(state: ResumeEnhancerState) -> dict[str, Any]:
    """
    Build a flat change_report list from FullEnhancementOutput.

    Input:
    - state.full_enhancement_output: FullEnhancementOutput

    Output:
    - state.change_report: List[ChangeReason]
    """
    logger.info("report_node: starting")
    try:
        full_output = _get_full_output(state)
        reasons = _collect_reasons(full_output)
    except Exception as e:
        logger.exception("report_node: failed to build change_report: %s", e)
        raise

    logger.info("report_node: done reasons_count=%s", len(reasons))
    return {"change_report": reasons}

