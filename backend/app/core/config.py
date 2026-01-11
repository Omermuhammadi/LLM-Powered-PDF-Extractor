"""
Application configuration using Pydantic Settings.

Loads configuration from environment variables with sensible defaults
optimized for CPU-only environments running Phi-3 Mini via Ollama.
"""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ===========================================
    # Application Settings
    # ===========================================
    app_name: str = Field(default="PDF Intelligence Extractor")
    app_version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # ===========================================
    # API Settings
    # ===========================================
    api_host: str = Field(default="0.0.0.0")  # nosec B104 - Intentional for Docker
    api_port: int = Field(default=8000)
    api_prefix: str = Field(default="/api/v1")
    api_rate_limit: int = Field(default=60)  # Requests per minute

    # ===========================================
    # CORS Settings
    # ===========================================
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:5173")

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # ===========================================
    # File Upload Settings
    # ===========================================
    max_upload_size_mb: int = Field(default=10)
    allowed_extensions: str = Field(default=".pdf")
    temp_dir: str = Field(default="./temp")

    @property
    def max_upload_size_bytes(self) -> int:
        """Convert MB to bytes."""
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def allowed_extensions_list(self) -> List[str]:
        """Parse allowed extensions string into a list."""
        return [ext.strip().lower() for ext in self.allowed_extensions.split(",")]

    # ===========================================
    # LLM Settings (Ollama)
    # ===========================================
    llm_mode: str = Field(default="local")  # "local" or "cloud"
    ollama_host: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="phi3:mini")
    llm_timeout: int = Field(default=60)
    llm_max_retries: int = Field(default=3)

    # ===========================================
    # Cloud LLM (Optional - Groq API)
    # ===========================================
    groq_api_key: str | None = Field(default=None)
    groq_model: str = Field(default="llama-3.1-70b-versatile")

    # ===========================================
    # Processing Settings
    # ===========================================
    max_text_length: int = Field(default=10000)
    chunk_size: int = Field(default=3000)
    min_confidence_threshold: float = Field(default=0.5)

    # ===========================================
    # Validators
    # ===========================================
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is a valid Python logging level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()

    @field_validator("llm_mode")
    @classmethod
    def validate_llm_mode(cls, v: str) -> str:
        """Validate LLM mode is either local or cloud."""
        if v.lower() not in ["local", "cloud"]:
            raise ValueError("llm_mode must be 'local' or 'cloud'")
        return v.lower()

    @field_validator("min_confidence_threshold")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Validate confidence threshold is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("min_confidence_threshold must be between 0 and 1")
        return v


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()


# Convenience instance for direct imports
settings = get_settings()
