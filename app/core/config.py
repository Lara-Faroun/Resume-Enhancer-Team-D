from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str

    OPENAI_API_KEY : str
    GOOGLE_API_KEY :str
    GEMINI_LLM_MODEL :str
    OPENAI_LLM_MODEL :str 
    OPENAI_API_BASE :str | None = None

    SCORE_THRESHOLD :int

    class Config(SettingsConfigDict):
        env_file = ".env"


def get_settings():
    return Settings()
    