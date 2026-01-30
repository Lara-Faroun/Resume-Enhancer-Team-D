from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Certification(BaseModel):
    """Matches template: cert.certification_name, issuing_organization, date."""
    certification_name: str = Field(..., description="The name of the certification")
    issuing_organization: str = Field(..., description="The organization that issued the certification")
    issue_date: Optional[datetime] = Field(None, description="The date the certification was issued")

    class Config:
        populate_by_name = True
    