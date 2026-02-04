from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel , Field

class Education(BaseModel):
    """Matches template: edu.degree, major, start_date, end_date, university_name, city, country."""
    degree: str = Field(..., description="The degree of the education")
    major: str = Field(..., description="The major of the education")
    university_name: str = Field(..., description="The name of the university")
    city: str = Field(..., description="The city of the education")
    country: str = Field(..., description="The country of the education")
    start_date: datetime = Field(..., description="The start date of the education")
    end_date: Optional[datetime] = Field(None, description="The end date of the education")

    class Config:
        populate_by_name = True
