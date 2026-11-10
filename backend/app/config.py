import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_BASE_DIR = DATA_DIR / "knowledge_base"
CHROMA_PERSIST_DIR = DATA_DIR / "chroma_db"
UPLOADS_DIR = BASE_DIR / "uploads"

# Ensure runtime directories exist
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    APP_NAME: str = "Screenly"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database
    DATABASE_URL: str = "sqlite:///./screenly.db"

    # LLM Settings
    # Modes: "mock" (offline fallback), "gemini", "openai"
    LLM_PROVIDER: str = "mock"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    LLM_MODEL_NAME: str = "gemini-1.5-flash"

    # RAG Settings
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 80
    TOP_K_RETRIEVAL: int = 3
    SIMILARITY_THRESHOLD: float = 0.25

    # Interview Orchestration
    QUESTIONS_PER_SESSION: int = 5
    ENABLE_ADAPTIVE_DIFFICULTY: bool = True
    ENABLE_FOLLOWUP_PROBES: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
