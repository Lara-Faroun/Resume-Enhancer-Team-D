import logging
from typing import Any, Type

from langchain_core.language_models.chat_models import BaseChatModel

from schemas.resume import Resume
from schemas.job_description import JobDescription
from llm.prompts.resume_parser import resume_text_to_json_prompt
from llm.prompts.job_parser import job_text_to_json_prompt


logger = logging.getLogger(__name__)


class LLMService:
    """
    Unified LLM service.

    - Wraps the LangChain chat model created once in main.py.
    - Provides high-level, schema-aware methods for common tasks.
    - Uses LangChain structured output where appropriate.
    """

    def __init__(self, llm: BaseChatModel):
        if llm is None:
            raise ValueError("LLMService requires a non-None llm instance")
        self._llm = llm

    @property
    def llm(self) -> BaseChatModel:
        """Expose the underlying LangChain model if low-level access is needed."""
        return self._llm

    async def _invoke_structured(
        self,
        schema: Type[Any],
        prompt: str,
    ) -> Any:
        """
        Internal helper to call the LLM with structured output.

        - schema: Pydantic model class (e.g. Resume, JobDescription)
        - prompt: prompt string (system + user instructions already embedded)
        """
        structured_llm = self._llm.with_structured_output(schema)
        try:
            result = await structured_llm.ainvoke(prompt)
        except Exception as e:
            logger.exception(
                "LLMService._invoke_structured: LLM call failed for schema=%s: %s",
                getattr(schema, "__name__", str(schema)),
                e,
            )
            raise

        if not isinstance(result, schema):
            logger.error(
                "LLMService._invoke_structured: expected %s, got %s",
                getattr(schema, "__name__", str(schema)),
                type(result),
            )
            raise ValueError(
                f"LLMService._invoke_structured: LLM must return {schema.__name__}"
            )

        return result

    async def parse_resume(self, resume_text: str) -> Resume:
        """
        Parse raw resume text into a Resume Pydantic model using structured output.
        """
        prompt = resume_text_to_json_prompt(resume_text)
        return await self._invoke_structured(Resume, prompt)

    async def parse_job(self, job_text: str) -> JobDescription:
        """
        Parse raw job description text into a JobDescription Pydantic model
        using structured output.
        """
        prompt = job_text_to_json_prompt(job_text)
        return await self._invoke_structured(JobDescription, prompt)

