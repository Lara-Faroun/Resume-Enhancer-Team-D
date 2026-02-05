from schemas.resume import Resume
from llm.service import LLMService

async def parse_resume(resume_text: str, llm_service: LLMService) -> Resume:
    """
    Parse raw resume text into a Resume model using the unified LLMService.

    This delegates to LLMService.parse_resume, which uses LangChain
    structured output with the Resume schema.
    """
    return await llm_service.parse_resume(resume_text)
