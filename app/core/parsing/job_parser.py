from schemas.job_description import JobDescription
from llm.service import LLMService


async def parse_job_description(job_text: str, llm_service: LLMService) -> JobDescription:
    """
    Parse raw job description text into a JobDescription model using LLMService.

    This delegates to LLMService.parse_job, which uses LangChain structured
    output with the JobDescription schema.
    """
    return await llm_service.parse_job(job_text)
