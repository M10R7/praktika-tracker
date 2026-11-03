"""
Application configuration using Pydantic.
Author: Сәбитов Азамат (гр. АЖ-47)
"""

import os

from pydantic import BaseModel, Field


class Settings(BaseModel):
    PROJECT_NAME: str = "Praktika-Tracker API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    HOST: str = Field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    PORT: int = Field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    DATABASE_URL: str = Field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql://praktika_user:praktika_secret_2026@localhost:5432/praktika_db",
        )
    )
    FACULTY_CODE: str = "FIT"
    TARGET_STUDENTS_COUNT: int = 250


settings = Settings()
