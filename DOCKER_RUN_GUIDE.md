# Docker Run Guide

## Layout

- **Backend:** FastAPI in `app/`, built with `Dockerfile.backend` (WeasyPrint + system libs).
- **Frontend:** Streamlit in `cv_app_project/`, built with `Dockerfile.frontend`.
- **Env:** Backend reads `app/.env` (copy from `app/env.example`). Frontend uses `API_BASE_URL` (set in Compose).

## Prerequisites

- Docker and Docker Compose (v2+).
- Backend `.env`: `cp app/env.example app/.env` then set at least one of `OPENAI_API_KEY` or `GOOGLE_API_KEY`.

## Production

```bash
# From repo root (Resume-Enhancer-Team-D)
docker compose -f docker-compose.yml up -d --build
```

- API: http://localhost:8000  
- Docs: http://localhost:8000/docs  
- Streamlit: http://localhost:8501  

Stop: `docker compose -f docker-compose.yml down`

## Development (hot reload)

```bash
docker compose -f docker-compose.dev.yml up --build
```

- Backend: `uvicorn --reload`; code in `app/` is mounted.
- Frontend: Streamlit with `--server.runOnSave=true`; code in `cv_app_project/` is mounted.

Stop with Ctrl+C. Remove volumes if needed: `docker compose -f docker-compose.dev.yml down -v`

## Single-service runs

```bash
# Backend only (production)
docker build -f Dockerfile.backend -t resume-api . && docker run -p 8000:8000 --env-file app/.env resume-api

# Frontend only (needs API at api:8000 or set API_BASE_URL to host URL)
docker build -f Dockerfile.frontend -t resume-streamlit . && docker run -p 8501:8501 -e API_BASE_URL=http://host.docker.internal:8000 resume-streamlit
```

## Notes

- WeasyPrint and system libraries (Pango, Cairo, etc.) are installed only in the backend image.
- No Windows-specific dependencies are used in the containers; everything runs on Linux in Docker.


<!-- docker compose -f docker-compose.dev.yml up --build -->