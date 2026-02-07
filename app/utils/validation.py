"""Post-LLM validation to prevent field corruption."""
import logging
from typing import List

from schemas.project import Project
from schemas.experience import Experience
from schemas.education import Education

logger = logging.getLogger(__name__)


def validate_projects(
    enhanced: List[Project],
    original: List[Project]
) -> List[Project]:
    """
    Ensure project_name remains a title, not a URL.
    
    Args:
        enhanced: Enhanced projects from LLM
        original: Original projects from user
    
    Returns:
        Validated projects with corrections applied
    """
    for i, proj in enumerate(enhanced):
        if i >= len(original):
            break
        
        # project_name must not be a URL
        if proj.project_name.startswith(("http://", "https://")):
            logger.warning(
                f"Validation: project[{i}].project_name is URL, reverting to original",
                extra={"invalid_value": proj.project_name, "original_value": original[i].project_name}
            )
            proj.project_name = original[i].project_name
        
        # project_link must be a URL (if present)
        if proj.project_link and not proj.project_link.startswith(("http://", "https://")):
            logger.warning(
                f"Validation: project[{i}].project_link is not URL, reverting to original",
                extra={"invalid_value": proj.project_link, "original_value": original[i].project_link}
            )
            proj.project_link = original[i].project_link
    
    return enhanced


def validate_experiences(
    enhanced: List[Experience],
    original: List[Experience]
) -> List[Experience]:
    """
    Ensure dates, company_name, role_title are unchanged.
    
    Args:
        enhanced: Enhanced experiences from LLM
        original: Original experiences from user
    
    Returns:
        Validated experiences with corrections applied
    """
    for i, exp in enumerate(enhanced):
        if i >= len(original):
            break
        
        # Dates must not change
        if exp.start_date != original[i].start_date:
            logger.warning(
                f"Validation: experience[{i}].start_date changed, reverting to original",
                extra={"invalid_value": exp.start_date, "original_value": original[i].start_date}
            )
            exp.start_date = original[i].start_date
        
        if exp.end_date != original[i].end_date:
            logger.warning(
                f"Validation: experience[{i}].end_date changed, reverting to original",
                extra={"invalid_value": exp.end_date, "original_value": original[i].end_date}
            )
            exp.end_date = original[i].end_date
        
        # Identifiers must not change
        if exp.company_name != original[i].company_name:
            logger.warning(
                f"Validation: experience[{i}].company_name changed, reverting to original",
                extra={"invalid_value": exp.company_name, "original_value": original[i].company_name}
            )
            exp.company_name = original[i].company_name
        
        if exp.role_title != original[i].role_title:
            logger.warning(
                f"Validation: experience[{i}].role_title changed, reverting to original",
                extra={"invalid_value": exp.role_title, "original_value": original[i].role_title}
            )
            exp.role_title = original[i].role_title
    
    return enhanced


def validate_educations(
    enhanced: List[Education],
    original: List[Education]
) -> List[Education]:
    """
    Ensure dates and institution names are unchanged.
    
    Args:
        enhanced: Enhanced educations from LLM
        original: Original educations from user
    
    Returns:
        Validated educations with corrections applied
    """
    for i, edu in enumerate(enhanced):
        if i >= len(original):
            break
        
        # Dates must not change
        if edu.start_date != original[i].start_date:
            logger.warning(
                f"Validation: education[{i}].start_date changed, reverting to original",
                extra={"invalid_value": edu.start_date, "original_value": original[i].start_date}
            )
            edu.start_date = original[i].start_date
        
        if edu.end_date != original[i].end_date:
            logger.warning(
                f"Validation: education[{i}].end_date changed, reverting to original",
                extra={"invalid_value": edu.end_date, "original_value": original[i].end_date}
            )
            edu.end_date = original[i].end_date
        
        # Identifiers must not change
        if edu.university_name != original[i].university_name:
            logger.warning(
                f"Validation: education[{i}].university_name changed, reverting to original",
                extra={"invalid_value": edu.university_name, "original_value": original[i].university_name}
            )
            edu.university_name = original[i].university_name
        
        if edu.degree != original[i].degree:
            logger.warning(
                f"Validation: education[{i}].degree changed, reverting to original",
                extra={"invalid_value": edu.degree, "original_value": original[i].degree}
            )
            edu.degree = original[i].degree
    
    return enhanced
