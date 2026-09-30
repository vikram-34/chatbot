"""
Central configuration for the chatbot.
Loads everything from environment variables (.env file supported via python-dotenv).
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # LLM Provider Abstraction Layer -> Gemini only for this build
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    # Auth / JWT Service
    JWT_SECRET: str = os.getenv("JWT_SECRET", "insecure-dev-secret-change-me")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

    # Rate Limiter & Guardrails
    RATE_LIMIT_MAX_REQUESTS: int = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "20"))
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

    # Storage Layer (SQLite standing in for Postgres/Redis/Chroma in this lightweight build)
    DB_PATH: str = os.getenv("DB_PATH", "./data/chatbot.db")


settings = Settings()
