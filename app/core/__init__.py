"""
Core module - configuration and utilities.
"""
import os
import logging
from dataclasses import dataclass
from typing import Optional


# =============================================================================
# Logging Setup
# =============================================================================

def setup_logging(level: int = logging.INFO):
    """Configure application logging."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class Settings:
    """Application settings loaded from environment."""

    # LLM Configuration
    llm_provider: str = "ollama"
    llm_model: str = "llama3.2"
    llm_temperature: float = 0.2

    # OpenAI
    openai_api_key: Optional[str] = None

    # Ollama
    ollama_base_url: str = "http://localhost:11434"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_name: str = "gym_exercises"

    # Database
    database_url: str = "postgresql://trainer:trainer123@localhost:5432/trenerai"

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables."""
        return cls(
            llm_provider=os.getenv("LLM_PROVIDER", "ollama").lower(),
            llm_model=os.getenv("LLM_MODEL", "llama3.2"),
            llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            qdrant_collection_name=os.getenv("QDRANT_COLLECTION_NAME", "gym_exercises"),
            database_url=os.getenv("DATABASE_URL", "postgresql://trainer:trainer123@localhost:5432/trenerai"),
        )


# Singleton settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings (singleton)."""
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings
