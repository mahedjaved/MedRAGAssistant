"""Pydantic Settings for MedRAGAssistant — all env vars validated at startup."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Required API keys ──────────────────────────────────────────
    pinecone_api_key: str
    groq_api_key: str

    # ── Legacy fallback (for backward compat with existing .env files) ──
    grok_api_key: str = ""

    # ── Optional API keys (reserved for future phases) ─────────────
    google_api_key: str | None = None
    langchain_api_key: Optional[str] = None
    langsmith_api_key: str | None = None
    langsmith_tracing: bool = Field(default=True, description="Enable LangSmith tracing (default: True)")
    langsmith_project: str | None = Field(default="medrag-assistant", description="LangSmith project name (default: medrag-assistant)")

    # ── Pinecone ───────────────────────────────────────────────────
    pinecone_env: str = "us-east-1"
    pinecone_index_name: str = "medical-index"
    relaxation_time: int = 1  # seconds for readiness polls

    # ── Service URLs (Docker defaults; override for local dev) ─────
    qdrant_url: str = "http://qdrant:6333"
    database_url: str = "postgresql://postgres:postgres@postgres:5432/medrag"

    # ── Server ─────────────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    uploaded_docs_dir: str = "./uploaded_docs"

    # ── GROQ_API_KEY fallback ──────────────────────────────────────
    @property
    def groq_api_key_resolved(self) -> str:
        """Return GROQ_API_KEY, falling back to the legacy GROK_API_KEY env var."""
        return self.groq_api_key or self.grok_api_key

    class Config:
        env_file = ".env"
        extra = "ignore"

# Module-level singleton — instantiated once on import.
# Imports:  from config import settings
settings = Settings()