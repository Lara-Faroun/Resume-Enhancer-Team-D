"""
Format node: merge the original Resume with FullEnhancementOutput
to produce a final enhanced Resume instance suitable for export.

This node does NOT call an LLM. It is pure, deterministic Python code that
respects the CV schema as the single source of truth.
"""
import logging
from typing import Any

from graph.state import ResumeEnhancerState, normalize_state
from graph.utils import log_node_timing
from schemas.resume import Resume
from schemas.enhancement import FullEnhancementOutput
from utils.validation import validate_projects, validate_experiences, validate_educations

logger = logging.getLogger(__name__)


def _get_format_inputs(
    state: ResumeEnhancerState,
) -> tuple[Resume, FullEnhancementOutput]:
    """
    Extract resume and full_enhancement_output from state, with validation.
    """
    resume = state.resume
    full_output = state.full_enhancement_output
    if resume is None:
        logger.error("format_node: state.resume is missing")
        raise ValueError("format_node requires state.resume")
    if full_output is None:
        logger.error("format_node: state.full_enhancement_output is missing")
        raise ValueError("format_node requires state.full_enhancement_output")

    return resume, full_output


def _build_enhanced_resume(
    resume: Resume, full_output: FullEnhancementOutput
) -> Resume:
    """
    Merge original resume with enhanced sections.

    - personal_info is kept as-is (no enhancement for now).
    - summary and each list section are replaced only if an enhanced
      version is present in FullEnhancementOutput; otherwise the
      original values are preserved.
    """
    # Summary: fallback to original if not enhanced
    if full_output.summary is not None:
        summary = full_output.summary.enhanced
    else:
        summary = resume.summary

    # Experiences (with validation)
    if full_output.experiences is not None:
        experiences = validate_experiences(
            full_output.experiences.enhanced,
            resume.experiences
        )
    else:
        experiences = resume.experiences

    # Educations (with validation)
    if full_output.educations is not None:
        educations = validate_educations(
            full_output.educations.enhanced,
            resume.educations
        )
    else:
        educations = resume.educations

    # Skills
    if full_output.skills is not None:
        skills = full_output.skills.enhanced
    else:
        skills = resume.skills

    # Certifications
    if full_output.certifications is not None:
        certifications = full_output.certifications.enhanced
    else:
        certifications = resume.certifications

    # Languages
    if full_output.languages is not None:
        languages = full_output.languages.enhanced
    else:
        languages = resume.languages

    # Projects (with validation)
    if full_output.projects is not None:
        projects = validate_projects(
            full_output.projects.enhanced,
            resume.projects
        )
    else:
        projects = resume.projects

    # Construct a new Resume instance; do not mutate the original
    enhanced_resume = Resume(
        personal_info=resume.personal_info,
        summary=summary,
        educations=educations,
        experiences=experiences,
        skills=skills,
        certifications=certifications,
        languages=languages,
        projects=projects,
    )

    return enhanced_resume


@log_node_timing("format")
def format_node(state: ResumeEnhancerState) -> dict[str, Any]:
    """
    Build the final enhanced resume from the original resume and
    FullEnhancementOutput.

    Inputs:
    - state.resume: Resume
    - state.full_enhancement_output: FullEnhancementOutput

    Output:
    - state.enhanced_resume: Resume
    """
    logger.info("format_node: starting")
    state = normalize_state(state)
    try:
        resume, full_output = _get_format_inputs(state)
        enhanced_resume = _build_enhanced_resume(resume, full_output)
    except Exception as e:
        logger.exception("format_node: failed to build enhanced resume: %s", e)
        raise

    logger.info(
        "format_node: done summary_changed=%s experiences_changed=%s "
        "educations_changed=%s skills_changed=%s certifications_changed=%s "
        "languages_changed=%s projects_changed=%s",
        full_output.summary is not None,
        full_output.experiences is not None,
        full_output.educations is not None,
        full_output.skills is not None,
        full_output.certifications is not None,
        full_output.languages is not None,
        full_output.projects is not None,
    )

    return {"enhanced_resume": enhanced_resume}

