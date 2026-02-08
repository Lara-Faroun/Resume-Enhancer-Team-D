from datetime import date, datetime
from typing import List, Optional
import re
from pydantic import BaseModel, Field, field_validator


def _parse_date_lenient(v) -> Optional[datetime]:
    """Parse date strings including ISO and human-readable formats (e.g. 'May 2023')."""
    if v is None or v == "":
        return None
    if isinstance(v, (date, datetime)):
        return datetime.combine(v, datetime.min.time()) if isinstance(v, date) else v
    if not isinstance(v, str):
        return None
    s = v.strip()
    if not s:
        return None
    # ISO formats: YYYY-MM-DD, YYYY-MM
    try:
        if re.match(r"^\d{4}-\d{2}-\d{2}", s):
            return datetime.fromisoformat(s[:10])
        if re.match(r"^\d{4}-\d{2}$", s):
            return datetime.strptime(s, "%Y-%m")
        # Month YYYY (e.g. "May 2023", "August 2023")
        if re.match(r"^[A-Za-z]+\s+\d{4}$", s):
            return datetime.strptime(s, "%B %Y")
        if re.match(r"^[A-Za-z]{3}\s+\d{4}$", s):
            return datetime.strptime(s, "%b %Y")
    except (ValueError, TypeError):
        pass
    return None


class Certification(BaseModel):
    """Matches template: cert.certification_name, issuing_organization, date."""
    certification_name: str = Field(..., description="The name of the certification")
    issuing_organization: str = Field(..., description="The organization that issued the certification")
    issue_date: Optional[datetime] = Field(None, description="The date the certification was issued")

    @field_validator("issue_date", mode="before")
    @classmethod
    def parse_issue_date(cls, v):
        result = _parse_date_lenient(v)
        # Return parsed datetime, or None for empty/unparseable (field is optional)
        return result if result is not None else None

    class Config:
        populate_by_name = True
    