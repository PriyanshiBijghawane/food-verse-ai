import os
from typing import List

class Settings:
    APP_NAME: str = "Food Verse AI"
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "t")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./foodverse.db")

    # Uploads
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads"))
    MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "25"))
    MAX_VIDEO_DURATION_SEC: int = int(os.getenv("MAX_VIDEO_DURATION_SEC", "60"))
    MAX_VIDEO_FRAMES: int = int(os.getenv("MAX_VIDEO_FRAMES", "12"))

    # AI Provider Configuration
    AI_MODE: str = os.getenv("AI_MODE", "demo").lower()  # "demo" | "real"
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "gemini").lower()  # "gemini" | "groq" | "openai" | "local"
    AI_API_KEY: str = os.getenv("AI_API_KEY", os.getenv("GEMINI_API_KEY", os.getenv("GROQ_API_KEY", "")))
    AI_MODEL: str = os.getenv("AI_MODEL", "gemini-1.5-flash")

    # Nutrition Service
    NUTRITION_PROVIDER: str = os.getenv("NUTRITION_PROVIDER", "local")
    NUTRITION_API_KEY: str = os.getenv("NUTRITION_API_KEY", "")

    # Security & Auth
    SECRET_KEY: str = os.getenv("SESSION_SECRET", os.getenv("SECRET_KEY", "foodverse-super-secret-key-change-in-production-2026"))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # CORS
    @property
    def CORS_ORIGINS(self) -> List[str]:
        raw = os.getenv("CORS_ORIGINS", "")
        if raw:
            return [origin.strip() for origin in raw.split(",") if origin.strip()]
        return [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]

settings = Settings()
