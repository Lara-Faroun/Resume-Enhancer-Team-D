from pydantic import BaseModel, Field
from enums import SkillType


class Skill(BaseModel):
    """Matches template: skill.skill_name, skill_type (compare by .value in template: technical / soft)."""
    skill_name: str = Field(..., description="Skill name")
    skill_type: SkillType = Field(..., description="technical or soft")

    class Config:
        populate_by_name = True