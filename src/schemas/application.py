"""
Pydantic schemas for InternshipApplication.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.company import CompanyOut
from src.schemas.student import StudentOut


class ApplicationSubmission(BaseModel):
    # Student information
    student_iin: str = Field(..., min_length=12, max_length=12, description="12-значный ИИН")
    student_fullname: str = Field(..., min_length=3, description="ФИО студента")
    student_email: str = Field(..., description="Email студента")
    student_phone: str = Field(..., description="Телефон студента")
    student_group: str = Field("АЖ-47", description="Академическая группа")
    specialty_code: str = Field(
        "6B06101 - Информационные системы", description="Шифр и название специальности"
    )

    # Company information
    company_id: int | None = Field(None, description="ID из справочника баз")
    company_name: str | None = Field(None, description="Наименование организации")
    company_bin: str = Field(..., min_length=12, max_length=12, description="12-значный БИН")
    company_address: str | None = Field("г. Алматы", description="Юридический адрес")
    company_director: str | None = Field("", description="ФИО первого руководителя")
    mentor_fullname: str = Field(..., min_length=3, description="ФИО руководителя от базы практики")

    # Practice details
    practice_type: str = Field(
        "Өндірістік практика / Производственная практика", description="Вид практики"
    )
    academic_supervisor: str = Field(
        "Самбетбаева Мадина Аралбаевна", description="ФИО руководителя от кафедры"
    )
    start_date: str = Field("2026-06-01", description="Дата начала (ГГГГ-ММ-ДД)")
    end_date: str = Field("2026-07-15", description="Дата окончания (ГГГГ-ММ-ДД)")


class StatusChangeRequest(BaseModel):
    new_status: str = Field(..., description="Новый статус заявки")
    comment: str | None = Field("", description="Комментарий к изменению статуса")
    rejection_reason: str | None = Field(
        None, description="Обязательная причина отклонения при статусе rejected (US-06)"
    )


class AuditLogOut(BaseModel):
    id: int
    old_status: str | None
    new_status: str
    changed_by: str
    comment: str | None
    ip_address: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ApplicationOut(BaseModel):
    id: int
    application_number: str
    student: StudentOut
    company: CompanyOut
    practice_type: str
    start_date: str
    end_date: str
    company_mentor_name: str
    academic_supervisor_name: str
    status: str
    rejection_reason: str | None
    contract_file_path: str | None
    signed_scan_path: str | None
    created_at: datetime
    updated_at: datetime
    audit_logs: list[AuditLogOut] | None = []
    model_config = ConfigDict(from_attributes=True)


class PublicTrackerOut(BaseModel):
    """Masked public view according to SEC-01 & US-14."""

    application_number: str
    masked_student_name: str
    masked_iin: str
    company_name: str
    practice_type: str
    status: str
    status_label_ru: str
    status_label_kz: str
    status_step: int
    rejection_reason: str | None = None
    has_contract_doc: bool
    has_signed_scan: bool
    updated_at: str
