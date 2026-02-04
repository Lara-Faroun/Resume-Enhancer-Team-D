from app.schemas.job_description import JobDescription
from app.llm.gemini_client import gemini_client
from app.llm.prompts.job_parser import job_text_to_json_prompt


async def parse_job_description(job_text: str) -> JobDescription:
    prompt = job_text_to_json_prompt(job_text)

    parsed_dict = await gemini_client.generate_json_dict(prompt)

    return JobDescription(**parsed_dict)
