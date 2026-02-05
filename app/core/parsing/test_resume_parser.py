import asyncio

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from core.config import get_settings
from core.parsing.text_extractor import extract_text_from_file
from core.parsing.resume_parser import parse_resume
from llm.service import LLMService


def _create_llm_service_for_test() -> LLMService:
    """
    Create an LLMService instance for local testing, mirroring main.py logic.
    """
    settings = get_settings()

    llm = None
    if settings.GOOGLE_API_KEY:
        try:
            llm = ChatGoogleGenerativeAI(
                model=settings.GEMINI_LLM_MODEL,
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=0,
                convert_system_message_to_human=True,
            )
        except Exception:
            llm = None

    if llm is None and settings.OPENAI_API_KEY:
        llm = ChatOpenAI(
            model=settings.OPENAI_LLM_MODEL,
            open_api_key=settings.OPENAI_API_KEY,
        )

    if llm is None:
        raise RuntimeError(
            "Failed to create LLM for test: configure GOOGLE_API_KEY or OPENAI_API_KEY"
        )

    return LLMService(llm)


print("🚀 test file started")


async def main():
    # Extract
    text = extract_text_from_file("jane_doe_resume4.pdf")

    # Create LLM service
    llm_service = _create_llm_service_for_test()

    # Parse
    resume = await parse_resume(text, llm_service)
    print("✅ resume parsed")
    print(resume.model_dump())


if __name__ == "__main__":
    asyncio.run(main())
