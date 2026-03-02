"""Pydantic Settings loading from .env"""
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://sehra:sehra_pass@localhost:5432/sehra_db"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24h
    cors_origins: str = "http://localhost:3000"
    openai_api_key: str = ""
    groq_api_key: str = ""
    anthropic_api_key: str = ""
    log_level: str = "INFO"
    app_url: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
