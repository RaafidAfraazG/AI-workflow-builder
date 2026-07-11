# backend/app/core/config.py
from pydantic_settings import BaseSettings
from pydantic import model_validator
from typing import Optional, List
from pathlib import Path


class Settings(BaseSettings):
    # Database — PostgreSQL (local, native)
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/workflow_builder"

    # LLM Configuration
    LLM_PROVIDER: str = "mock"
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"

    # Search API Keys (optional)
    SERPAPI_KEY: Optional[str] = None
    BRAVE_API_KEY: Optional[str] = None

    # ChromaDB — embedded persistent mode (no server / no Docker needed)
    CHROMA_PERSIST_DIR: str = "./chroma_data"

    # Embedding Service — defaults to matching LLM_PROVIDER when not explicitly set
    EMBEDDING_PROVIDER: str = "mock"

    # Disable ChromaDB telemetry
    ANONYMIZED_TELEMETRY: bool = False

    # File Upload
    UPLOAD_DIR: str = "uploads"

    # API Configuration
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "AI Workflow Builder"

    # CORS Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    # Development
    DEBUG: bool = False

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
    }

    @model_validator(mode="after")
    def derive_embedding_provider(self) -> "Settings":
        """If EMBEDDING_PROVIDER was not explicitly set (still at default 'mock'),
        inherit the LLM_PROVIDER so Gemini LLM → Gemini embeddings automatically."""
        if self.EMBEDDING_PROVIDER == "mock" and self.LLM_PROVIDER != "mock":
            self.EMBEDDING_PROVIDER = self.LLM_PROVIDER
        return self

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create required directories if they don't exist
        Path(self.UPLOAD_DIR).mkdir(exist_ok=True)
        Path(self.CHROMA_PERSIST_DIR).mkdir(exist_ok=True)


settings = Settings()