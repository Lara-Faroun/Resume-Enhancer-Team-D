"""
Gate / routing logic after the mapping node.

This is used by the LangGraph workflow to decide whether to:
- go to the feedback branch (when score < SCORE_THRESHOLD), or
- proceed to enhancement (when score >= SCORE_THRESHOLD).
"""
import logging

from core.config import get_settings
from graph.state import ResumeEnhancerState, normalize_state

logger = logging.getLogger(__name__)


def route_after_mapping(state: ResumeEnhancerState) -> str:
    """
    Decide next step after mapping based on match_score and SCORE_THRESHOLD.

    Returns:
        "feedback" if mapping_result.match_score < SCORE_THRESHOLD
        "enhance"  otherwise
    """
    state = normalize_state(state)
    mapping_result = state.mapping_result
    if mapping_result is None:
        logger.error("route_after_mapping: mapping_result is missing")
        raise ValueError("route_after_mapping requires state.mapping_result")

    score = mapping_result.match_score
    threshold = get_settings().SCORE_THRESHOLD

    logger.info(
        "route_after_mapping: score=%s threshold=%s -> %s",
        score,
        threshold,
        "feedback" if score < threshold else "enhance",
    )

    if score < threshold:
        return "feedback"
    return "enhance"

