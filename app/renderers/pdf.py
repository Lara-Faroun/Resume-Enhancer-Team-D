"""
PDF export utilities for the Resume schema.

This module is responsible only for:
- Normalizing a `Resume` into a template-ready dict.
- Rendering the HTML template with Jinja2.
- Converting the rendered HTML into a PDF using WeasyPrint.

It does NOT contain any business logic or LLM calls.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from core.normalization import normalize_resume_for_template
from schemas.resume import Resume


# Resolve the templates directory relative to this file:
_BASE_DIR = Path(__file__).resolve().parent.parent
_TEMPLATES_DIR = _BASE_DIR / "templates"

# Jinja2 environment for rendering HTML templates.
_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_resume_pdf(resume: Resume) -> bytes:
    """
    Render a Resume as a PDF document using Jinja2 + WeasyPrint.

    Steps:
    1. Normalize the Resume into a primitive dict structure.
    2. Render `resume_template.html` with Jinja2.
    3. Convert the HTML to PDF bytes using WeasyPrint.
    """
    context: dict[str, Any] = normalize_resume_for_template(resume)

    template = _jinja_env.get_template("resume_template.html")
    html_content: str = template.render(**context)

    # base_url is required so that relative URLs (e.g. for fonts/images)
    # in the template can be resolved correctly if added later.
    pdf_bytes: bytes = HTML(string=html_content, base_url=str(_TEMPLATES_DIR)).write_pdf()
    return pdf_bytes

