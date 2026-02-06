import os

# Optional: load .env if python-dotenv is installed (e.g. in FastAPI monorepo)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class AppConfig:
    APP_TITLE = "CV Personalization Engine"
    APP_ICON = "🎯"
    FOOTER_TEXT = "🎯 AI CV Personalization Engine | Powered by Advanced AI | Secure & Confidential"
    
    API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000").rstrip("/")
    API_PARSE_ENDPOINT = "/api/v1/parse"
    API_ENHANCE_ENDPOINT = "/api/v1/enhance"
    API_EXPORT_RESUME_ENDPOINT = "/api/v1/export/resume"
    API_TIMEOUT = int(os.environ.get("API_TIMEOUT", "120"))
    
    MIN_MATCH_SCORE = 6.0
    MAX_FILE_SIZE_MB = 10
    MIN_JOB_DESC_LENGTH = 50
    
    VALID_FILE_TYPES = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ]
    VALID_FILE_EXTENSIONS = ['.pdf', '.docx']
