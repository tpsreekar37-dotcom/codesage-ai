import os
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    PORT: int = 8000
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "ai_code_review_db"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: str

    # Redis
    REDIS_HOST: str = "cache"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://cache:6379/0"

    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # Uploads/Clones
    UPLOAD_DIR: str = "/app/data/uploads"
    CLONE_DIR: str = "/app/data/cloned"
    MAX_UPLOAD_SIZE_MB: int = 25

    # Security
    FRONTEND_URL: str = "http://localhost:5173"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, v: str, info) -> str:
        if v:
            return v
        user = info.data.get("POSTGRES_USER")
        password = info.data.get("POSTGRES_PASSWORD")
        host = info.data.get("POSTGRES_HOST")
        port = info.data.get("POSTGRES_PORT")
        db = info.data.get("POSTGRES_DB")
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"

settings = Settings()
