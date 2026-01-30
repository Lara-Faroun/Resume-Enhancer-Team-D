from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Project(BaseModel):
    """Matches template: project.project_name, description, project_link. Description can be multiple lines (list joined in template)."""

    project_name: str = Field(..., description="The name of the project")
    description: List[str] = Field(..., description="The description of the project")
    project_link: Optional[str] = Field(None, description="The link to the project")

    class Config:
        populate_by_name = True
