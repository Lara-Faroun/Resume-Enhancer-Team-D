from typing import List
from pydantic import BaseModel, Field
from schemas.personal_info import PersonalInfo
from schemas.education import Education
from schemas.experience import Experience
from schemas.skill import Skill
from schemas.certification import Certification
from schemas.language import Language
from schemas.project import Project


class Resume(BaseModel):
    """CV schema: single source of truth. Attribute names match resume_template.html (cv.*)."""
    personal_info: PersonalInfo = Field(..., description="The personal information of the user")
    summary: str = Field(..., description="The summary of the user")
    educations: List[Education] = Field(..., description="The list of educations the user has")
    experiences: List[Experience] = Field(..., description="The list of experiences the user has")
    skills: List[Skill] = Field(..., description="The list of skills the user has")
    certifications: List[Certification] = Field(..., description="The list of certifications the user has")
    languages: List[Language] = Field(..., description="The list of languages the user has")
    projects: List[Project] = Field(..., description="The list of projects the user has")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

