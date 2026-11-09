"""
Application configuration for Praktika-Tracker.
Author: Сәбитов Азамат (гр. АЖ-47)
"""

import os
from pathlib import Path

from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseModel):
    PROJECT_NAME: str = "«Практика-Трекер» ФИТ ЕНУ"
    VERSION: str = "1.0.0 (MVP)"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    HOST: str = Field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    PORT: int = Field(default_factory=lambda: int(os.getenv("PORT", "8000")))

    # Database: Default to local SQLite file for instant standalone execution,
    # or use PostgreSQL when DATABASE_URL is configured (e.g. in Docker)
    DATABASE_URL: str = Field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            f"sqlite:///{BASE_DIR / 'praktika.db'}",
        )
    )

    # University & Faculty Metadata (L.N. Gumilyov Eurasian National University, Astana)
    UNIVERSITY_NAME_RU: str = "Евразийский национальный университет имени Л.Н. Гумилева"
    UNIVERSITY_NAME_KZ: str = "Л.Н. Гумилев атындағы Еуразия ұлттық университеті"
    FACULTY_NAME_RU: str = "Факультет информационных технологий"
    FACULTY_NAME_KZ: str = "Ақпараттық технологиялар факультеті"
    FACULTY_CODE: str = "FIT"
    DEAN_NAME: str = "Шаяхметова А. К."
    TARGET_STUDENTS_COUNT: int = 250
    ACADEMIC_YEAR: str = "2026-2027"

    # Storage Paths
    STORAGE_DIR: Path = BASE_DIR / "storage"
    DOCUMENTS_DIR: Path = BASE_DIR / "storage" / "documents"
    UPLOADS_DIR: Path = BASE_DIR / "storage" / "uploads"

    # Rate limiting for public status tracker (SEC-01)
    RATE_LIMIT_TRACKER: str = "15/minute"


settings = Settings()

# Ensure storage directories exist
settings.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
