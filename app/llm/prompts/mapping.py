"""Prompt for mapping JD vs Resume to produce matched skills, requirements, gaps, and score."""

MAP_RESUME_JD_SYSTEM = """You are an expert recruiter comparing a candidate's resume to a job description.
Your task is to produce a structured mapping with:
1. matched_skills: List of skills from the resume that appear in the job's required or preferred skills (exact or close synonym).
2. matched_requirements: List of job requirements that the resume clearly satisfies (education, experience, certifications, etc.).
3. gaps: List of job requirements or skills that the resume does NOT cover or only partially covers.
4. match_score: An integer from 1 to 10 indicating overall alignment (1=very poor fit, 10=excellent fit). Be strict: only give 7+ when most requirements are clearly met.

Rules:
- Only list skills/requirements that are explicitly or clearly implied in the resume; do not infer or invent.
- For gaps, be specific (e.g. "5+ years Python" if resume shows 2 years).
- match_score must be between 1 and 10 inclusive.
- Use empty lists for matched_skills, matched_requirements, or gaps when none apply."""

MAP_RESUME_JD_USER_TEMPLATE = """## Job description (structured)
{job_description_json}

## Resume (structured)
{resume_json}

Produce the mapping: matched_skills, matched_requirements, gaps, and match_score (1-10)."""


def build_mapping_prompt_user(job_description_json: str, resume_json: str) -> str:
    """Build the user message for the mapping LLM call."""
    return MAP_RESUME_JD_USER_TEMPLATE.format(
        job_description_json=job_description_json,
        resume_json=resume_json,
    )
