

from __future__ import annotations

import re

from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Response

from renderers.pdf import render_resume_pdf
from renderers.docx import render_resume_docx
from schemas.resume import Resume


router = APIRouter()


def _build_filename_from_name(full_name: str | None, extension: str) -> str:
    """
    Build a simple, safe filename from a person's full name.

    Example:
        "Jane Doe" -> "jane_doe_resume.pdf"
    """
    if not full_name:
        return f"resume.{extension}"

    # Lowercase, replace non-alphanumeric with underscores, collapse repeats.
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", full_name.strip().lower()).strip("_")
    if not slug:
        slug = "resume"
    return f"{slug}_resume.{extension}"


@router.post("/export/resume")
def export_resume(
    resume: Resume,
    file_type: Literal["pdf", "docx"] = Query(
        "pdf",
        alias="type",
        description="Export type: 'pdf' or 'docx'. Defaults to 'pdf'.",
    ),
) -> Response:
    """
    Export the given Resume schema as either PDF or DOCX.

    - type=pdf  -> application/pdf
    - type=docx -> application/vnd.openxmlformats-officedocument.wordprocessingml.document

    Includes basic validation and error handling around the rendering step.
    """
    try:
        if file_type == "pdf":
            content_bytes = render_resume_pdf(resume)
            media_type = "application/pdf"
            extension = "pdf"
        else:
            content_bytes = render_resume_docx(resume)
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            extension = "docx"
    except Exception as exc:
        # Log at a higher level (FastAPI / app logger) if desired; here we surface a safe message.
        raise HTTPException(
            status_code=500,
            detail=f"Failed to render {file_type.upper()} resume.",
        ) from exc

    filename = _build_filename_from_name(resume.personal_info.full_name, extension)

    return Response(
        content=content_bytes,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.post("/export/pdf")
def export_resume_pdf(resume: Resume) -> Response:
    """
    Export the given Resume schema as a PDF.

    This endpoint is intentionally simple: it receives a structured Resume,
    uses the shared normalization + HTML template pipeline, and returns
    a binary PDF response suitable for download.
    """
    pdf_bytes = render_resume_pdf(resume)
    filename = _build_filename_from_name(resume.personal_info.full_name, "pdf")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.post("/export/docx")
def export_resume_docx(resume: Resume) -> Response:
    """
    Export the given Resume schema as a DOCX document.

    Layout is intentionally simple and mirrors the HTML template,
    relying on the shared normalization layer.
    """
    docx_bytes = render_resume_docx(resume)
    filename = _build_filename_from_name(resume.personal_info.full_name, "docx")

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )

