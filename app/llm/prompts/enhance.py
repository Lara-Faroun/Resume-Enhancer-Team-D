"""Prompts for enhancing resume sections against a mapping (no JD needed here)."""

ENHANCE_SYSTEM = """You are an expert resume writer helping a candidate tailor
their resume to a specific job description.

Your task is to enhance the existing resume sections while strictly following
these rules:

- Do NOT invent or fabricate experience, skills, certifications, or projects.
- Do NOT add technologies that are not present in the original resume.
- You may:
  - Rephrase bullet points and descriptions for clarity and impact.
  - Reorder content to better highlight relevance to the job.
  - Emphasize experiences, skills, and projects that match the job description
    and the provided mapping.
- Keep all facts consistent with the original resume.
- If a section is empty in the original resume, you MUST leave it empty.

You will receive:
- A structured resume.
- A structured mapping_result with matched_skills, matched_requirements, gaps,
  and match_score.

You must return a structured FullEnhancementOutput object with:
- summary (optional): enhanced summary + reasons for changes.
- experiences (optional): enhanced list of experiences + reasons.
- educations (optional): enhanced list of educations + reasons.
- skills (optional): enhanced skills list + reasons.
- certifications (optional): enhanced certifications + reasons.
- languages (optional): enhanced languages + reasons.
- projects (optional): enhanced projects + reasons.

For each change you make, add a concise ChangeReason explaining WHY the change
improves alignment with the job description or clarity for the reader.
"""

ENHANCE_USER_TEMPLATE = """## Resume (structured)
{resume_json}

## Mapping result (structured)
{mapping_result_json}

Enhance the resume section by section following the rules and return a
FullEnhancementOutput object."""


def build_enhance_prompt_user(resume_json: str, mapping_result_json: str) -> str:
    """Build the user message for the enhancement LLM call."""
    return ENHANCE_USER_TEMPLATE.format(
        resume_json=resume_json,
        mapping_result_json=mapping_result_json,
    )


def build_section_prompt_user(
    section_name: str,
    resume_json: str,
    mapping_result_json: str
) -> str:
    """
    Build prompt for enhancing a single section.
    
    Args:
        section_name: One of: summary, experiences, educations, skills,
                      certifications, languages, projects
        resume_json: Full resume as JSON string
        mapping_result_json: Mapping result as JSON string
    
    Returns:
        Prompt string for the LLM
    """
    section_display = section_name.replace("_", " ").title()
    
    return f"""## Resume (structured)
{resume_json}

## Mapping result (structured)
{mapping_result_json}

## Task
Enhance ONLY the '{section_display}' section of the resume following these rules:

1. Do NOT invent or fabricate information
2. Do NOT add technologies not in the original resume
3. You may:
   - Rephrase for clarity and impact
   - Reorder content to highlight relevance
   - Emphasize matches with the job description
4. Keep all facts consistent with the original
5. If the section is empty in the original, leave it empty

Return a {section_name.capitalize()}EnhancementOutput object with:
- enhanced: The enhanced {section_display} content
- reasons: List of ChangeReason objects explaining each change
"""
