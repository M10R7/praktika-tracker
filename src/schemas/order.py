"""
Pydantic schemas for DeanOrder.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OrderGenerateRequest(BaseModel):
    order_number: str | None = Field("№ 142-П", description="Номер приказа")
    order_date: str | None = Field("2026-05-25", description="Дата приказа")
    academic_year: str | None = Field("2026-2027", description="Учебный год")
    faculty: str | None = Field("Факультет информационных технологий", description="Факультет")
    specialty: str | None = Field(
        "6B061 - Информационно-коммуникационные технологии", description="Направление/специальность"
    )


class OrderOut(BaseModel):
    id: int
    order_number: str
    order_date: str
    academic_year: str
    faculty: str
    specialty: str
    total_students: int
    file_path: str
    created_at: datetime
    unassigned_students_count: int
    unassigned_students: list[str] = []
    model_config = ConfigDict(from_attributes=True)
