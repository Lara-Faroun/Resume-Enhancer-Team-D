from typing import List, Optional
from pydantic import BaseModel, Field

from .experience import Experience
from .education import Education
from .skill import Skill
from .certification import Certification
from .language import Language
from .project import Project


class ChangeReason(BaseModel):
    """Explanation for a single change in an enhanced section. Supports human-in-the-loop review."""

    field_or_location: str = Field(
        ...,
        description="Section or field that was changed (e.g. 'experiences[0].description', 'skills').",
    )
    reason: str = Field(
        ...,
        description="Explanation for the change.",
    )

    class Config:
        populate_by_name = True


class SummaryEnhancementOutput(BaseModel):
    """Enhanced summary section plus reasons for changes."""

    enhanced: str = Field(
        ...,
        description="Enhanced summary text.",
    )
    reasons: List[ChangeReason] = Field(
        default_factory=list,
        description="Reasons for changes in this section.",
    )

    class Config:
        populate_by_name = True


class ExperiencesEnhancementOutput(BaseModel):
    """Enhanced experiences section plus reasons for changes."""

    enhanced: List[Experience] = Field(
        default_factory=list,
        description="Enhanced list of experiences.",
    )
    reasons: List[ChangeReason] = Field(
        default_factory=list,
        description="Reasons for changes in this section.",
    )

    class Config:
        populate_by_name = True


class EducationsEnhancementOutput(BaseModel):
    """Enhanced educations section plus reasons for changes."""

    enhanced: List[Education] = Field(
        default_factory=list,
        description="Enhanced list of educations.",
    )
    reasons: List[ChangeReason] = Field(
        default_factory=list,
        description="Reasons for changes in this section.",
    )

    class Config:
        populate_by_name = True


class SkillsEnhancementOutput(BaseModel):
    """Enhanced skills section plus reasons for changes."""

    enhanced: List[Skill] = Field(
        default_factory=list,
        description="Enhanced list of skills.",
    )
    reasons: List[ChangeReason] = Field(
        default_factory=list,
        description="Reasons for changes in this section.",
    )

    class Config:
        populate_by_name = True


class CertificationsEnhancementOutput(BaseModel):
    """Enhanced certifications section plus reasons for changes."""

    enhanced: List[Certification] = Field(
        default_factory=list,
        description="Enhanced list of certifications.",
    )
    reasons: List[ChangeReason] = Field(
        default_factory=list,
        description="Reasons for changes in this section.",
    )

    class Config:
        populate_by_name = True


class LanguagesEnhancementOutput(BaseModel):
    """Enhanced languages section plus reasons for changes."""

    enhanced: List[Language] = Field(
        default_factory=list,
        description="Enhanced list of languages.",
    )
    reasons: List[ChangeReason] = Field(
        default_factory=list,
        description="Reasons for changes in this section.",
    )

    class Config:
        populate_by_name = True


class ProjectsEnhancementOutput(BaseModel):
    """Enhanced projects section plus reasons for changes."""

    enhanced: List[Project] = Field(
        default_factory=list,
        description="Enhanced list of projects.",
    )
    reasons: List[ChangeReason] = Field(
        default_factory=list,
        description="Reasons for changes in this section.",
    )

    class Config:
        populate_by_name = True


class FullEnhancementOutput(BaseModel):
    """
    Aggregated output of section-by-section enhancement.
    Input: CV schema + MappingResult. Output: each section enhanced + reasons.
    Used to build the final enhanced resume and the change report.
    """

    summary: Optional[SummaryEnhancementOutput] = Field(
        None,
        description="Enhanced summary, if this section was processed.",
    )
    experiences: Optional[ExperiencesEnhancementOutput] = Field(
        None,
        description="Enhanced experiences, if this section was processed.",
    )
    educations: Optional[EducationsEnhancementOutput] = Field(
        None,
        description="Enhanced educations, if this section was processed.",
    )
    skills: Optional[SkillsEnhancementOutput] = Field(
        None,
        description="Enhanced skills, if this section was processed.",
    )
    certifications: Optional[CertificationsEnhancementOutput] = Field(
        None,
        description="Enhanced certifications, if this section was processed.",
    )
    languages: Optional[LanguagesEnhancementOutput] = Field(
        None,
        description="Enhanced languages, if this section was processed.",
    )
    projects: Optional[ProjectsEnhancementOutput] = Field(
        None,
        description="Enhanced projects, if this section was processed.",
    )

    class Config:
        populate_by_name = True
