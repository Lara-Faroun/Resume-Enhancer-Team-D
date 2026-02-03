"""
LangGraph state for the resume enhancer workflow.
Raw inputs (resume_raw, job_description_text) are pre-input: parsing happens
outside the graph. Only structured data and derived outputs live in state.
"""
from typing import List, Optional

from pydantic import BaseModel, Field

from schemas.resume import Resume
from schemas.job_description import JobDescription
from schemas.mapping_result import MappingResult
from schemas.enhancement import FullEnhancementOutput, ChangeReason


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
    change_report: List[ChangeReason] = Field(
        default_factory=list,
        description="All change reasons across sections for the report.",
    )

    # --- Feedback path (when score < threshold) ---
    feedback_message: Optional[str] = Field(None, description="User feedback when score below threshold.")

    class Config:
        arbitrary_types_allowed = True
        populate_by_name = True
