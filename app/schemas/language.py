from pydantic import BaseModel, Field
from enums import LanguageProficiencyLevel


class Language(BaseModel):
    """Matches template: lang.language, proficiency_level (use .value in template for display)."""
    language: str = Field(..., description="Language name")
    proficiency_level: LanguageProficiencyLevel = Field(..., description="Proficiency level")

    class Config:
        populate_by_name = True