from pydantic import BaseModel, Field

class ReflectionOutput(BaseModel):
    """Output of the reflection/critique step."""
    
    is_sufficient: bool = Field(
        ..., 
        description="Whether the enhanced resume meets the quality standards and requirements."
    )
    critique: str = Field(
        ..., 
        description="Detailed feedback on what needs to be improved if not sufficient."
    )
    score: int = Field(
        ..., 
        description="Quality score from 1-10.",
        ge=1,
        le=10
    )

    class Config:
        populate_by_name = True
