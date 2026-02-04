REFLECTION_SYSTEM = """
You are a Critical Reviewer for a Resume Enhancement System.
Your job is to critique the enhanced resume provided by an AI agent.
You must be strict but fair.
Focus on:
1. Relevance to the Job Description: Does the resume highlight the right skills and experiences?
2. Professional Tone: Is the language professional, action-oriented, and concise?
3. Completeness: Are all sections properly fleshed out?
4. Quantification: Are achievements quantified where possible?

If the resume is excellent and ready for the candidate, output is_sufficient=True.
If there are clear areas for improvement, output is_sufficient=False and provide detailed critique.
"""

REFLECTION_USER_TEMPLATE = """
# Job Description
{job_description}

# Enhanced Resume
{enhanced_resume_json}

# Instructions
Critique the Enhanced Resume against the Job Description.
Is it good enough to receive a high score?
"""

def build_reflection_prompt_user(job_description: str, enhanced_resume_json: str) -> str:
    return REFLECTION_USER_TEMPLATE.format(
        job_description=job_description,
        enhanced_resume_json=enhanced_resume_json
    )
