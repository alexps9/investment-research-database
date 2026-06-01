from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_knowledge"
    database_url_sync: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/ai_knowledge"
    app_name: str = "AI Intelligence Knowledge Base"
    debug: bool = False
    api_prefix: str = "/api"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
