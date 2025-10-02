from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Dict, Any, List, Union
from functools import lru_cache
import secrets
import os
from pathlib import Path

load_dotenv()

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = Field(default_factory=lambda: os.getenv("SECRET_KEY", secrets.token_urlsafe(32)))
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
    RATE_LIMIT_PER_MINUTE: int = os.getenv("RATE_LIMIT_PER_MINUTE", 100)
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Database
    SQLITE_DB: str = "document_hub.db"
    DATABASE_URL: str = f"sqlite:///{SQLITE_DB}"
    
    # For SQLAlchemy
    SQLALCHEMY_DATABASE_URI: str = DATABASE_URL
    SQL_ECHO: bool = False
    
    # Pydantic v2 config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
