from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date, datetime


class Experience(BaseModel):
    """Shared by professional_experience and volunteer_experience. Matches template: exp.role_title, company_name, start_date, end_date, description."""

    role_title: str = Field(..., description="The title of the role")
    company_name: str = Field(..., description="The name of the company or organization")
    start_date: datetime = Field(..., description="The start date of the experience")
    end_date: Optional[datetime] = Field(None, description="The end date of the experience")
    description: List[str] = Field(..., description="The description of the experience")
    is_volunteer: bool = Field(False, description="Whether the experience is volunteer or professional")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
