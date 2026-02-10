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
- Use empty lists for matched_skills, matched_requirements, or gaps when none apply.

Matching Rules:
- Only consider a job requirement fully matched if it is clearly and explicitly
  supported by evidence in the resume.
- For matched_requirements, each item must include BOTH:
  - a short quote or paraphrase of the job requirement (from the job description),
  - and a short description of the specific resume evidence (role + bullet or
    section) that satisfies it.
- If a requirement is only implied or partially supported, treat it as matched
  with lower confidence and reflect this by either:
  - including it with wording that shows it is partially or implicitly covered,
    and/or
  - listing it in gaps with an explanation of what is missing.
- Do NOT assume perfection unless every core responsibility and key requirement
  in the job description is directly supported by the resume content.

Skill Mapping Rules:
- Only include a skill in matched_skills if:
  - it appears in job_description.required_skills or preferred_skills
    (or a very close synonym, such as "LLM" vs "LLMs"), AND
  - it is explicitly present in the resume (skills list, experience bullets,
    projects, or certifications).
- Do NOT add matched_skills that are only loosely related or not clearly
  present in BOTH the job description and the resume.

Gaps:
- gaps entries must be understandable to HR and hiring managers.
- Each gap string should clearly state what the job asks for and what is missing
  or only partially covered in the resume.

Soft cap for perfect scores:
- Avoid assigning a match_score of 10/10 unless the resume meets or exceeds
  essentially all core job requirements and responsibilities.
- When in doubt between 9 and 10, choose the lower score.
"""

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
