from typing import List, Optional
from pydantic import BaseModel, EmailStr

class PersonalInfo(BaseModel):
    """Matches template: cv.personal_info.full_name, email_address, phone_number, linkedin, personal_website."""
    full_name: str
    phone_number: str
    email_address: EmailStr
    linkedin: Optional[str] = None
    personal_website: Optional[str] = None

    class Config:
        populate_by_name = True
