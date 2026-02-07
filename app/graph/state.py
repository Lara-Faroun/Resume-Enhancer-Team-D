"""
LangGraph state for the resume enhancer workflow.
Raw inputs (resume_raw, job_description_text) are pre-input: parsing happens
outside the graph. Only structured data and derived outputs live in state.

State invariants (which fields are guaranteed non-null after which node):
- At entry: resume, job_description are set by the API before invoke.
- After mapping: mapping_result is set.
- On enhance path after enhance: full_enhancement_output is set.
- On enhance path after format: enhanced_resume is set.
- On enhance path after report: report_summary may be set (or None if no reasons).
- On feedback path: only feedback_message is set; enhanced_resume and report_summary stay unset.
"""
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field

from schemas.resume import Resume
from schemas.job_description import JobDescription
from schemas.mapping_result import MappingResult
from schemas.enhancement import FullEnhancementOutput


def normalize_state(state: Union[Dict[str, Any], "ResumeEnhancerState"]) -> "ResumeEnhancerState":
    """
    Ensure state is a ResumeEnhancerState instance.
    LangGraph may pass a dict; nodes use this so they can rely on attribute access only.
    Only keys present on ResumeEnhancerState are passed through (ignores LangGraph extras).
    """
    if isinstance(state, ResumeEnhancerState):
        return state
    allowed = set(ResumeEnhancerState.model_fields)
    payload = {k: state[k] for k in state if k in allowed}
    return ResumeEnhancerState(**payload)


class ResumeEnhancerState(BaseModel):
    """
    State passed through the resume enhancer graph.
    All fields optional so nodes can return partial updates.
    """

    # --- Input (provided at invoke by API after parsing) ---
    resume: Optional[Resume] = Field(None, description="Parsed resume schema.")
    job_description: Optional[JobDescription] = Field(None, description="Parsed job description schema.")

    # --- After mapping node ---
    mapping_result: Optional[MappingResult] = Field(None, description="JD vs resume mapping and score.")

    # --- Enhancement path (only one of the two branches is populated) ---
    full_enhancement_output: Optional[FullEnhancementOutput] = Field(
        None,
        description="Enhanced sections and reasons, when score >= threshold.",
    )
    enhanced_resume: Optional[Resume] = Field(None, description="Final enhanced resume for export.")
    report_summary: Optional[str] = Field(
        None,
        description="LLM-generated summary of changes for human-in-the-loop review.",
    )

    # --- Feedback path (when score < threshold) ---
    feedback_message: Optional[str] = Field(None, description="User feedback when score below threshold.")

    # --- Mode support (legacy, incremental, sectional) ---
    mode: Optional[str] = Field(
        "legacy",
        description="Enhancement mode: 'legacy' (single call), 'incremental' (SSE streaming), or 'sectional' (per-section with fallbacks)"
    )
    progress_events: Optional[list] = Field(
        default_factory=list,
        description="Event log for incremental mode (section start/complete events)"
    )
    section_timings: Optional[dict] = Field(
        default_factory=dict,
        description="Elapsed time per section in milliseconds"
    )
    token_usage: Optional[dict] = Field(
        default_factory=dict,
        description="Token usage per section: {section: {input: N, output: M}}"
    )

    # --- Sectional mode support ---
    section_errors: Optional[dict] = Field(
        default_factory=dict,
        description="Section-level errors in sectional mode: {section_name: error_message}"
    )
    sectional_metadata: Optional[dict] = Field(
        default_factory=dict,
        description="Processing metadata for sectional mode (counts, timing, status)"
    )

    class Config:
        arbitrary_types_allowed = True
        populate_by_name = True
