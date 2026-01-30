from pydantic_settings import BaseSettings , SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str


    class Config(SettingsConfigDict):
        env_file = ".env"

def get_settings():
    return Settings()
    