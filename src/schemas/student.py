"""
Pydantic schemas for Student.
"""

from pydantic import BaseModel, ConfigDict, Field


class StudentBase(BaseModel):
    iin: str = Field(..., min_length=12, max_length=12, description="12-значный ИИН студента")
    full_name: str = Field(..., min_length=3, max_length=255)
    email: str = Field(..., max_length=100)
    phone: str = Field(..., max_length=50)
    faculty: str = Field("Факультет информационных технологий", max_length=100)
    specialty_code: str = Field("6B06101 - Информационные системы", max_length=100)
    group_code: str = Field("АЖ-47", max_length=50)
    course: int = Field(4, ge=1, le=5)


class StudentCreate(StudentBase):
    pass


class StudentOut(StudentBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
