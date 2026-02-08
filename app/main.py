import logging
from contextlib import asynccontextmanager
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from graph.graph import build_graph
from llm.service import LLMService

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "resume_enhancer.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Settings (load once for app metadata and middleware)
# -----------------------------------------------------------------------------
settings = get_settings()


# -----------------------------------------------------------------------------
# Lifespan: startup / shutdown (init resources here, e.g. LangGraph later)
# -----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Config initialized")

    # Try initializing Gemini first, fallback to OpenAI if it fails
    llm = None

    # Attempt to use Gemini
    if settings.GOOGLE_API_KEY:
        try:
            logger.info(f"Attempting to initialize Gemini model: {settings.GEMINI_LLM_MODEL}")
            llm = ChatGoogleGenerativeAI(
                model=settings.GEMINI_LLM_MODEL,
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=0,
                convert_system_message_to_human=True,  # Gemini doesn't support system messages natively
            )

            logger.info(f"✓ Gemini LLM initialized successfully: {settings.GEMINI_LLM_MODEL}")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini: {e}")
            logger.info("Falling back to OpenAI...")
            llm = None

    # Fallback to OpenAI if Gemini failed or no API key
    if llm is None:
        if not settings.OPENAI_API_KEY:
            logger.error("Neither GOOGLE_API_KEY nor OPENAI_API_KEY is set!")
            raise ValueError("At least one LLM API key (GOOGLE_API_KEY or OPENAI_API_KEY) must be configured")

        logger.info(f"Initializing OpenAI model: {settings.OPENAI_LLM_MODEL}")

        llm = ChatOpenAI(
            model=settings.OPENAI_LLM_MODEL,
            api_key=settings.OPENAI_API_KEY,
            openai_api_base="https://openrouter.ai/api/v1",

            temperature=0,
            max_tokens=4096,
        )
        logger.info(f"✓ OpenAI LLM initialized successfully: {settings.OPENAI_LLM_MODEL}")
    
    # Expose raw LangChain LLM and the higher-level LLMService.
    app.state.llm = llm
    app.state.llm_service = LLMService(llm)

    # Compile LangGraph once per app instance, reusing the shared LLM.
    try:
        app.state.graph = build_graph(llm)
        logger.info("✓ LangGraph workflow compiled successfully")
    except Exception as e:
        logger.exception("Failed to compile LangGraph workflow: %s", e)
        raise
    yield
    # Shutdown
    logger.info("Shutting down")


# -----------------------------------------------------------------------------
# App
# -----------------------------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered resume personalization: Structure → Reason → Rewrite → Review → Render",
    lifespan=lifespan,
)

# -----------------------------------------------------------------------------
# CORS (configure in main; adjust origins for production)
# -----------------------------------------------------------------------------
CORS_ORIGINS: list[str] = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Routers (add as you implement them)
# -----------------------------------------------------------------------------
from routers.enhance import router as enhance_router
from routers.parse import router as parse_router
from routers.export import router as export_router

app.include_router(enhance_router, prefix="/api/v1", tags=["enhance"])
app.include_router(parse_router, prefix="/api/v1", tags=["parse"])
app.include_router(export_router, prefix="/api/v1", tags=["export"])
# -----------------------------------------------------------------------------
# Global endpoints
# -----------------------------------------------------------------------------
@app.get("/health")
def health():
    """Health check for deployment and monitoring."""
    return {"status": "ok", "version": settings.APP_VERSION}
