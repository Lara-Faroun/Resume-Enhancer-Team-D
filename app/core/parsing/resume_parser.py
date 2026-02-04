# app/core/parsing/resume_parser.py

from app.schemas.resume import Resume
from app.schemas.personal_info import PersonalInfo
from app.schemas.education import Education
from app.schemas.experience import Experience
from app.schemas.skill import Skill
from app.schemas.certification import Certification
from app.schemas.language import Language
from app.schemas.project import Project
from app.llm.gemini_client import gemini_client
from app.llm.prompts.resume_parser import resume_text_to_json_prompt


import json
from app.schemas.resume import Resume


async def parse_resume(resume_text: str) -> Resume:
    prompt = resume_text_to_json_prompt(resume_text)
    raw_json = await gemini_client.generate_json(prompt)

    if not raw_json:
        raise RuntimeError("Empty response from Gemini")

    try:
        data = json.loads(raw_json)  # يحاول يحول النص لـ dict
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Gemini returned invalid JSON: {e}\nRaw output:\n{raw_json}")

    return Resume.model_validate(data)

