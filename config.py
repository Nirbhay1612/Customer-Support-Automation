
"""
Central configuration for the AI Customer Support Automation system.

Loads environment variables, validates application settings, and exposes
a cached Settings instance for use across the application.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------------------------------------------------------
# Project Paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent
ENV_FILE = PROJECT_ROOT / ".env"


# ---------------------------------------------------------
# Application Settings
# ---------------------------------------------------------

class Settings(BaseSettings):
    """Validated application configuration loaded from environment variables."""

    # Application
    APP_NAME: str = "AI Automation System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # API
    API_PREFIX: str = "/api"

    # AI / LLM
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    LLM_PROVIDER: str = "groq"
    LLM_MODEL: str = "llama-3.3-70b-versatile"

    TEMPERATURE: float = Field(default=0.2, ge=0.0, le=2.0)
    MAX_TOKENS: int = Field(default=1000, ge=1)

    # RAG
    EMBEDDING_MODEL: str = (
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    VECTOR_STORE_PATH: str = "data/vectorstore"
    DOCUMENTS_PATH: str = "data/documents"
    FAQ_PATH: str = "data/faq"

    TOP_K: int = Field(default=5, ge=1)
    SIMILARITY_THRESHOLD: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
    )

    # Database
    DATABASE_URL: str = "sqlite:///./data/automation.db"

    # Integrations
    ORDER_API_URL: str = ""

    EMAIL_HOST: str = ""
    EMAIL_PORT: int = Field(default=587, ge=1, le=65535)
    EMAIL_USERNAME: str = ""
    EMAIL_PASSWORD: str = ""

    # Webhooks
    WEBHOOK_SECRET: str = ""

    # Logging
    LOG_LEVEL: str = "INFO"

    # -----------------------------------------------------
    # Validation
    # -----------------------------------------------------

    @field_validator("ENVIRONMENT", "LLM_PROVIDER", mode="before")
    @classmethod
    def normalize_setting_names(cls, value: object) -> object:
        """Normalize environment and provider names."""
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def validate_log_level(cls, value: object) -> str:
        """Normalize and validate the logging level."""
        allowed_levels = {
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        }

        if not isinstance(value, str):
            raise ValueError("LOG_LEVEL must be a string.")

        normalized = value.strip().upper()

        if normalized not in allowed_levels:
            raise ValueError(
                f"Invalid LOG_LEVEL: {value!r}. "
                f"Choose one of: {', '.join(sorted(allowed_levels))}."
            )

        return normalized

    # -----------------------------------------------------
    # Pydantic Settings Configuration
    # -----------------------------------------------------

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
    )


# ---------------------------------------------------------
# Settings Factory
# ---------------------------------------------------------

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached application settings instance.

    Environment variables are read when the instance is first created.
    """
    return Settings()


# ---------------------------------------------------------
# Shared Settings Instance
# ---------------------------------------------------------

settings = get_settings()
