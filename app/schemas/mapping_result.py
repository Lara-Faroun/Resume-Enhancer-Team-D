from typing import List
from pydantic import BaseModel, Field


class MappingResult(BaseModel):
    """
    Result of mapping JD schema to Resume schema.
    Used to gate enhancement (score < threshold → feedback only) and to drive section-level rewriting.
    """

    matched_skills: List[str] = Field(
        default_factory=list,
        description="Skills from the resume that match JD required or preferred skills.",
    )
    matched_requirements: List[str] = Field(
        default_factory=list,
        description="JD requirements that are satisfied by the resume.",
    )
    gaps: List[str] = Field(
        default_factory=list,
        description="JD requirements or skills not covered by the resume.",
    )
    match_score: int = Field(
        ...,
        ge=1,
        le=10,
        description="Overall alignment score from 1 to 10.",
    )

    class Config:
        populate_by_name = True
