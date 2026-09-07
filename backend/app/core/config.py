import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

IS_VERCEL = bool(os.environ.get("VERCEL"))

class Settings(BaseSettings):
    # App
    APP_ENV: str = "production" if IS_VERCEL else "development"
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    DATABASE_URL: str = "sqlite:////tmp/recoverypilot.db" if IS_VERCEL else "sqlite:///./recoverypilot.db"
    FRONTEND_URL: str = "https://recovery-pilot-ai.vercel.app" if IS_VERCEL else "http://localhost:5173"
    LOG_LEVEL: str = "INFO"
    APP_VERSION: str = "1.0.0"

    # AI Provider
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    AI_MODEL: str = "llama-3.3-70b-versatile"
    AI_TIMEOUT_SECONDS: int = 8

    # Payment Providers
    RAZORPAY_API_KEY: Optional[str] = None
    RAZORPAY_API_SECRET: Optional[str] = None
    RAZORPAY_WEBHOOK_SECRET: str = "razorpay_webhook_secret_demo"

    # Policy Guardian defaults (can be overridden via env)
    MAX_PAYMENT_RETRIES: int = 2
    MAX_MESSAGES: int = 3
    MIN_HOURS_BETWEEN_CONTACTS: int = 24
    MAX_RECOVERY_DAYS: int = 30
    MAX_DISCOUNT_PERCENT: float = 10.0
    HIGH_VALUE_THRESHOLD_INR: float = 100000.0
    MIN_AI_CONFIDENCE: float = 0.60

    model_config = SettingsConfigDict(
        env_file=".env" if not IS_VERCEL else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
