from pathlib import Path
from typing import List, Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application settings
    APP_NAME: str = "M-ARCH"
    APP_ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # AI Provider Modes
    AI_MODE: Literal["Auto", "Groq", "Ollama", "Hybrid"] = "Auto"
    AI_PRIMARY_PROVIDER: Literal["Groq", "Ollama"] = "Groq"
    AI_FALLBACK_PROVIDER: Literal["Groq", "Ollama"] = "Ollama"

    # Cloud Provider: Groq
    GROQ_API_KEY: Optional[str] = Field(default=None)
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    # Cloud Provider: Gemini (Free API Key - strictly for Code Review Agent)
    GEMINI_API_KEY: Optional[str] = Field(default=None)
    GEMINI_MODEL: str = "gemini-3.1-flash-lite"
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta"

    # Local Provider: Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5-coder:7b"

    # Hybrid Routing Policy (maps task role to provider)
    HYBRID_ORCHESTRATOR_PROVIDER: Literal["Groq", "Ollama"] = "Groq"
    HYBRID_CODE_PROVIDER: Literal["Groq", "Ollama"] = "Ollama"
    HYBRID_SECURITY_PROVIDER: Literal["Groq", "Ollama"] = "Groq"
    HYBRID_DOCS_PROVIDER: Literal["Groq", "Ollama"] = "Ollama"

    # Embeddings & Retrieval
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    RERANK_ENABLED: bool = True
    HYBRID_RETRIEVAL_DENSE_WEIGHT: float = 0.6
    HYBRID_RETRIEVAL_FTS_WEIGHT: float = 0.4

    # Storage Paths
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/m_arch.db"
    DATA_DIR: Path = BASE_DIR / "data"
    VECTOR_STORAGE_PATH: Path = BASE_DIR / "data" / "vectors"
    STORAGE_DIR: Path = BASE_DIR / "data" / "storage"
    UPLOAD_MAX_MB: int = 100

    # Agent Limits
    AGENT_TIMEOUT_SECONDS: int = 120
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_FACTOR: float = 1.5

    def is_groq_configured(self) -> bool:
        return bool(self.GROQ_API_KEY and len(self.GROQ_API_KEY.strip()) > 5)

    def is_gemini_configured(self) -> bool:
        return bool(self.GEMINI_API_KEY and len(self.GEMINI_API_KEY.strip()) > 5)

settings = Settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.VECTOR_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
