from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class JobDescription(BaseModel):
    """Matches template: job_description.job_title, job_description, job_requirements."""
    job_title: str = Field(..., description="The title of the job")
    company_name: Optional[str] = Field(None, description="The name of the company")
    responsibilities: List[str] = Field(..., description="The responsibilities of the job")
    requirements: List[str] = Field(..., description="The requirements of the job such as the study field, experience..etc")
    required_skills: List[str] = Field(..., description="The skills required for the job")
    preferred_skills: List[str] = Field(..., description="The skills preferred for the job")
    seniority_level: Literal["junior", "mid", "senior", "lead"] = Field(default="mid", description="Seniority level (junior, mid, senior, lead)")
    soft_skills: Optional[List[str]] = Field(default_factory=list, description="Soft skills mentioned")
    class Config:
        populate_by_name = True
