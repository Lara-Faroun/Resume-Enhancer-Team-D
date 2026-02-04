"""
Normalization utilities for rendering a Resume into templates.

This module defines a pure function:

    normalize_resume_for_template(resume: Resume) -> dict

that converts the structured `Resume` Pydantic model into a
template-ready dictionary of only primitives / lists / dicts.

The normalized shape is aligned with `resume_template.html` and
keeps names close to the schema while ensuring:

- Dates are formatted as strings (`YYYY-MM`), with `"Present"` when
  `end_date` is `None`.
- Enums are converted to their `.value` representation.
- Sections use empty lists / containers instead of `None`.
- Experiences are split into professional and volunteer groups.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple

from schemas.resume import Resume
from schemas.experience import Experience
from schemas.skill import Skill
from schemas.language import Language


def _format_date(dt: datetime | None) -> str:
    """
    Format a datetime as a string in global resume format.

    - If `dt` is None, the caller should decide what to display (e.g. "Present").
    - Otherwise, returns "YYYY-MM".
    """
    if dt is None:
        return ""
    # ISO-like year-month; no timezone handling needed because schema
    # should already contain aware/naive datetimes consistently.
    return dt.strftime("%Y-%m")


def _format_period(start: datetime, end: datetime | None) -> Tuple[str, str]:
    """
    Format a (start, end) period for display.

    - Start is always formatted as "YYYY-MM".
    - End is "YYYY-MM" if provided, otherwise "Present".
    """
    start_str = _format_date(start)
    end_str = _format_date(end) if end is not None else "Present"
    return start_str, end_str


def _split_experiences(experiences: List[Experience]) -> Tuple[List[Experience], List[Experience]]:
    """
    Split experiences into (professional, volunteer) based on `is_volunteer`.
    """
    professional: List[Experience] = []
    volunteer: List[Experience] = []
    for exp in experiences:
        if exp.is_volunteer:
            volunteer.append(exp)
        else:
            professional.append(exp)
    return professional, volunteer


def _group_skills(skills: List[Skill]) -> Dict[str, List[str]]:
    """
    Group skills into technical and soft buckets by SkillType.

    Returns:
        {
            "technical": [skill_name, ...],
            "soft": [skill_name, ...],
        }
    """
    technical: List[str] = []
    soft: List[str] = []

    for skill in skills:
        # Compare using .value to avoid depending on enum class path here
        kind = getattr(skill.skill_type, "value", None)
        if kind == "technical":
            technical.append(skill.skill_name)
        elif kind == "soft":
            soft.append(skill.skill_name)

    return {
        "technical": technical,
        "soft": soft,
    }


def _normalize_languages(languages: List[Language]) -> List[Dict[str, Any]]:
    """
    Convert Language models into dicts with primitive values.
    """
    out: List[Dict[str, Any]] = []
    for lang in languages:
        out.append(
            {
                "language": lang.language,
                "proficiency_level": getattr(lang.proficiency_level, "value", str(lang.proficiency_level)),
            }
        )
    return out

def _normalize_experience_list(src: List[Experience]) -> List[Dict[str, Any]]:
    """
    Normalize a list of Experience models into a list of dicts.
    """
    items: List[Dict[str, Any]] = []
    for exp in src:
        start_str, end_str = _format_period(exp.start_date, exp.end_date)
        items.append(
            {
                "role_title": exp.role_title,
                "company_name": exp.company_name,
                "start_date": start_str,
                "end_date": end_str,
                "description": list(exp.description or []),
            }
        )
    return items

   
def normalize_resume_for_template(resume: Resume) -> Dict[str, Any]:
    """
    Normalize a `Resume` instance into a dict ready for Jinja2 templates.

    The returned structure matches `resume_template.html`:

    - personal_info: { full_name, email_address, phone_number, linkedin, personal_website }
    - summary: str
    - educations: [
          {
              degree, major, university_name, city, country,
              start_date: "YYYY-MM", end_date: "YYYY-MM" | "Present",
          },
      ]
    - professional_experiences: [
          {
              role_title, company_name,
              start_date: "YYYY-MM", end_date: "YYYY-MM" | "Present",
              description: [str, ...],
          },
      ]
    - volunteer_experiences: same shape as professional_experiences
    - projects: [
          { project_name, description: [str, ...], project_link },
      ]
    - certifications: [
          {
              certification_name,
              issuing_organization,
              issue_date: "YYYY-MM" or "",
          },
      ]
    - skills_grouped: { technical: [str, ...], soft: [str, ...] }
    - languages: [
          { language, proficiency_level },
      ]
    """

    # Personal info: keep schema names; all fields are already primitives
    personal = resume.personal_info
    personal_info_dict = {
        "full_name": personal.full_name,
        "phone_number": personal.phone_number,
        "email_address": str(personal.email_address),
        "linkedin": personal.linkedin,
        "personal_website": personal.personal_website,
    }

    # Educations: format dates and keep schema field names
    educations_list: List[Dict[str, Any]] = []
    for edu in resume.educations:
        start_str, end_str = _format_period(edu.start_date, edu.end_date)
        educations_list.append(
            {
                "degree": edu.degree,
                "major": edu.major,
                "university_name": edu.university_name,
                "city": edu.city,
                "country": edu.country,
                "start_date": start_str,
                "end_date": end_str,
            }
        )

    # Experiences: split into professional and volunteer and format periods
    professional_exps_raw, volunteer_exps_raw = _split_experiences(resume.experiences or [])

    professional_experiences = _normalize_experience_list(professional_exps_raw)
    volunteer_experiences = _normalize_experience_list(volunteer_exps_raw)

    # Projects: mostly pass-through; ensure lists are concrete
    projects_list: List[Dict[str, Any]] = []
    for proj in resume.projects or []:
        projects_list.append(
            {
                "project_name": proj.project_name,
                "description": list(proj.description or []),
                "project_link": proj.project_link,
            }
        )

    # Certifications: format issue_date
    certifications_list: List[Dict[str, Any]] = []
    for cert in resume.certifications or []:
        issue_str = _format_date(cert.issue_date) if cert.issue_date is not None else ""
        certifications_list.append(
            {
                "certification_name": cert.certification_name,
                "issuing_organization": cert.issuing_organization,
                "issue_date": issue_str,
            }
        )

    # Skills: group into technical / soft by enum value
    skills_grouped = _group_skills(resume.skills or [])

    # Languages: normalize enums to primitive values
    languages_list = _normalize_languages(resume.languages or [])

    normalized: Dict[str, Any] = {
        "personal_info": personal_info_dict,
        "summary": resume.summary,
        "educations": educations_list,
        "professional_experiences": professional_experiences,
        "volunteer_experiences": volunteer_experiences,
        "projects": projects_list,
        "certifications": certifications_list,
        "skills_grouped": skills_grouped,
        "languages": languages_list,
    }

    return normalized

