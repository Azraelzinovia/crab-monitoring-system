"""
Core Configuration — Pydantic Settings
Loads all environment variables with type validation.
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "Crab Monitoring System"
    APP_VERSION: str = "1.0.0"
    API_DEBUG: bool = False
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_SECRET_KEY: str = "change-me-in-production"

    # ── Database ─────────────────────────────────────────────────
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "crab_monitoring"
    DB_USER: str = "crab_admin"
    DB_PASSWORD: str = "crab_secure_2024"
    DATABASE_URL: Optional[str] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def build_database_url(cls, v, info):
        if v:
            return v
        data = info.data
        return (
            f"postgresql+asyncpg://{data.get('DB_USER')}:"
            f"{data.get('DB_PASSWORD')}@{data.get('DB_HOST')}:"
            f"{data.get('DB_PORT')}/{data.get('DB_NAME')}"
        )

    # ── Camera ───────────────────────────────────────────────────
    CAMERA_1_INDEX: int = 0
    CAMERA_2_INDEX: int = 1
    CAMERA_1_WIDTH: int = 1280
    CAMERA_1_HEIGHT: int = 720
    CAMERA_2_WIDTH: int = 1280
    CAMERA_2_HEIGHT: int = 720
    CAMERA_FPS: int = 30

    # ── AI Models ────────────────────────────────────────────────
    YOLO_MODEL_PATH: str = "ai_models/weights/yolov8_crabs.pt"
    SPECIES_MODEL_PATH: str = "ai_models/weights/species_classifier.pt"
    GENDER_MODEL_PATH: str = "ai_models/weights/gender_classifier.pt"
    HEALTH_MODEL_PATH: str = "ai_models/weights/health_classifier.pt"
    YOLO_CONFIDENCE: float = 0.5
    YOLO_IOU: float = 0.45

    # ── Storage ──────────────────────────────────────────────────
    IMAGE_STORAGE_PATH: str = "storage/images"
    MODEL_STORAGE_PATH: str = "storage/models"

    # ── Streaming ────────────────────────────────────────────────
    STREAM_FPS: int = 15
    STREAM_QUALITY: int = 85

    # ── Scraping ─────────────────────────────────────────────────
    SCRAPING_INTERVAL_HOURS: int = 24
    KAGGLE_USERNAME: Optional[str] = None
    KAGGLE_KEY: Optional[str] = None

    # ── Redis ────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379"

    # ── Logging ──────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/crab_monitor.log"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


# Singleton settings instance
settings = Settings()
