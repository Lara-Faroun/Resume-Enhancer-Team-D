from typing import Any, Dict
import logging
import os
import shutil
import tempfile

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, status
from pydantic import BaseModel

from core.parsing.text_extractor import extract_text_from_file
from core.parsing.resume_parser import parse_resume
from core.parsing.job_parser import parse_job_description
from schemas.resume import Resume
from schemas.job_description import JobDescription

logger = logging.getLogger(__name__)
router = APIRouter()


class ParseResponse(BaseModel):
    """Response body: parsed Resume and JobDescription."""

    resume: Resume
    job_description: JobDescription


@router.post("/parse", response_model=ParseResponse)
async def parse_resume_and_job(
    request: Request,
    file: UploadFile = File(...),
    job_description: str = Form(...),
) -> Dict[str, Any]:
    """
    Accept a resume file (PDF/DOCX) and raw job description text, and return
    structured Resume + JobDescription objects.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in {".pdf", ".docx"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Only .pdf and .docx are allowed.",
        )
    llm_service = getattr(request.app.state, "llm_service", None)
    if llm_service is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LLM service not initialized. Please try check the configuration.",
        )

    # Save uploaded file to a temporary location
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save uploaded file: {e}",
        )

    try:
        # 1) Extract text from the resume file
        resume_text = extract_text_from_file(tmp_path)

        # 2) Parse resume text to structured Resume (LLM)
        resume_obj = await parse_resume(resume_text, llm_service)

        # 3) Parse job description text to structured JobDescription (LLM)
        job_obj = await parse_job_description(job_description, llm_service)

        return ParseResponse(resume=resume_obj, job_description=job_obj)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Parse failed: %s", e)
        msg = str(e)
        # User-friendly hint for auth errors (OpenRouter 401 / invalid key)
        if "401" in msg or "AuthenticationError" in type(e).__name__ or "User not found" in msg:
            msg = (
                "LLM authentication failed (401). "
                "Using OpenRouter: get a key at https://openrouter.ai/keys and set OPENAI_API_KEY in app/.env. "
                "Using OpenAI: set OPENAI_API_BASE=https://api.openai.com/v1 and use a valid OpenAI key."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Parse failed: {msg}",
        )
    finally:
        # Cleanup temp file
        try:
            os.remove(tmp_path)
        except OSError:
            pass

