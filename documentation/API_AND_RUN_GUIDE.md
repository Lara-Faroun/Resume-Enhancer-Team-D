## How to Run the Project

### 1. Prerequisites

- Python 3.10+ installed
- A virtual environment (recommended)
- At least one LLM API key configured (Google Gemini or OpenAI)

### 2. Install dependencies

From the project root:

```bash
python -m venv .venv
# Activate your venv (PowerShell example)
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 3. Configure environment

Copy `app/env.example` (or `.env.example` if present) to `.env` in the project root and set:

- `APP_NAME`, `APP_VERSION`
- `GOOGLE_API_KEY` and `GEMINI_LLM_MODEL` **or**
- `OPENAI_API_KEY` and `OPENAI_LLM_MODEL`
- `SCORE_THRESHOLD`

The FastAPI app reads these via `core.config.Settings`.

### 4. Run the API server

From the project root:

```bash
uvicorn app.main:app --reload
```

The server will start on `http://localhost:8000` by default.

### 5. Explore with Swagger UI

Open:

- `http://localhost:8000/docs` for Swagger UI
- `http://localhost:8000/health` for a simple health check


## API Overview

All API routes are mounted under the `/api/v1` prefix unless otherwise noted.

### Health Check

- **Method**: `GET`
- **Path**: `/health`
- **Description**: Simple liveness check that also returns the app version.
- **Response (200)**:

  ```json
  { "status": "ok", "version": "x.y.z" }
  ```

---

### Enhance Resume

- **Method**: `POST`
- **Path**: `/api/v1/enhance`
- **Body model**: `EnhanceRequest`

  ```json
  {
    "resume": { /* Resume schema */ },
    "job_description": { /* JobDescription schema */ }
  }
  ```

- **Description**:
  - Runs the LangGraph workflow:
    - parses inputs (already done before this endpoint),
    - maps resume ↔ job description,
    - enhances sections when score ≥ threshold,
    - produces an enhanced resume and a change report, **or**
    - returns feedback when the match score is too low.

- **Success response (200)**:
  - Returns the final graph state as JSON, including some or all of:
    - `resume`
    - `job_description`
    - `mapping_result`
    - `full_enhancement_output`
    - `enhanced_resume`
    - `report_summary`
    - `feedback_message`

- **Error handling**:
  - `503` if the enhancement graph is not initialized at startup.
  - `500` if the graph execution fails or returns an unexpected format.

---

### Export Resume as PDF (simple route)

- **Method**: `POST`
- **Path**: `/api/v1/export/pdf`
- **Body model**: `Resume`

  ```json
  { /* Resume schema */ }
  ```

- **Description**:
  - Normalizes the `Resume` schema via `normalize_resume_for_template`.
  - Renders `resume_template.html` with Jinja2.
  - Generates a PDF with WeasyPrint.

- **Response (200)**:
  - `Content-Type: application/pdf`
  - `Content-Disposition: attachment; filename="<derived_from_name>_resume.pdf"`
  - Body: binary PDF bytes.

---

### Export Resume as DOCX (simple route)

- **Method**: `POST`
- **Path**: `/api/v1/export/docx`
- **Body model**: `Resume`

- **Description**:
  - Uses the same normalization pipeline as the PDF export.
  - Builds a `.docx` document using `python-docx` with a layout that mirrors the HTML template and the Word template.

- **Response (200)**:
  - `Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document`
  - `Content-Disposition: attachment; filename="<derived_from_name>_resume.docx"`
  - Body: binary DOCX bytes.

---

### Unified Export Endpoint (PDF or DOCX)

- **Method**: `POST`
- **Path**: `/api/v1/export/resume`
- **Query parameter**:

  - `type` (alias for `file_type`, required enum): `"pdf"` or `"docx"`.
  - Defaults to `"pdf"` if omitted.

- **Body model**: `Resume`

  ```json
  { /* Resume schema */ }
  ```

- **Description**:
  - Single endpoint to export the resume as either PDF or DOCX.
  - Internally dispatches to:
    - `render_resume_pdf` when `type=pdf`
    - `render_resume_docx` when `type=docx`

- **Success responses (200)**:
  - For `type=pdf`:

    - `Content-Type: application/pdf`
    - `Content-Disposition: attachment; filename="<derived_from_name>_resume.pdf"`

  - For `type=docx`:

    - `Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document`
    - `Content-Disposition: attachment; filename="<derived_from_name>_resume.docx"`

- **Error handling**:
  - `400` is prevented at schema level via `Literal["pdf", "docx"]` on the `type` query param.
  - `500` if PDF/DOCX rendering fails (e.g. template issues, unexpected data).


## Notes on Data Flow

- All APIs that touch resumes accept **structured `Resume` and `JobDescription` schemas**.
- The **normalization layer** (`core/normalization.py`) is the single source of truth for how resume data is presented in templates and exports.
- Exporters (`renderers/pdf.py`, `renderers/docx.py`) contain no business logic or LLM calls—only rendering.

