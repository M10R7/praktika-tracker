"""
Internship Contract lifecycle and validation service.
Author: Сәбитов Азамат (гр. АЖ-47)
"""

from enum import Enum

from pydantic import BaseModel, Field

from .bin_validator import validate_bin


class ContractStatus(str, Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED_BY_DEAN = "approved_by_dean"
    SIGNED_BY_COMPANY = "signed_by_company"
    ACTIVE = "active"
    COMPLETED = "completed"
    REJECTED = "rejected"
    TERMINATED = "terminated"


# Allowed state machine transitions for solo PM workflow
ALLOWED_TRANSITIONS: dict[ContractStatus, set[ContractStatus]] = {
    ContractStatus.DRAFT: {ContractStatus.UNDER_REVIEW, ContractStatus.REJECTED},
    ContractStatus.UNDER_REVIEW: {ContractStatus.APPROVED_BY_DEAN, ContractStatus.REJECTED},
    ContractStatus.APPROVED_BY_DEAN: {ContractStatus.SIGNED_BY_COMPANY, ContractStatus.REJECTED},
    ContractStatus.SIGNED_BY_COMPANY: {ContractStatus.ACTIVE, ContractStatus.REJECTED},
    ContractStatus.ACTIVE: {ContractStatus.COMPLETED, ContractStatus.TERMINATED},
    ContractStatus.COMPLETED: set(),
    ContractStatus.REJECTED: {ContractStatus.DRAFT},
    ContractStatus.TERMINATED: set(),
}


class ContractRequest(BaseModel):
    student_id: int = Field(..., gt=0, description="Уникальный ID студента")
    student_fullname: str = Field(..., min_length=3, description="ФИО студента")
    company_name: str = Field(..., min_length=2, description="Наименование предприятия")
    company_bin: str = Field(..., min_length=12, max_length=12, description="БИН организации (12 цифр)")
    mentor_fullname: str = Field(..., min_length=3, description="ФИО руководителя от базы практики")
    academic_supervisor: str = Field(..., min_length=3, description="ФИО руководителя от кафедры")
    start_date: str = Field(..., description="Дата начала практики (ГГГГ-ММ-ДД)")
    end_date: str = Field(..., description="Дата окончания практики (ГГГГ-ММ-ДД)")


class ContractResponse(BaseModel):
    contract_number: str
    status: ContractStatus
    is_valid: bool
    message: str


def generate_contract_number(sequence_id: int, faculty_code: str = "FIT", year: int = 2026) -> str:
    """Generates standardized official contract number, e.g. Д-2026-FIT-0042."""
    return f"Д-{year}-{faculty_code}-{sequence_id:04d}"


def validate_contract_transition(
    current_status: ContractStatus,
    new_status: ContractStatus,
) -> tuple[bool, str]:
    """Validates if status transition is allowed by business process."""
    allowed = ALLOWED_TRANSITIONS.get(current_status, set())
    if new_status in allowed:
        return True, f"Переход из '{current_status.value}' в '{new_status.value}' разрешен"
    return False, f"Запрещенный переход статуса: '{current_status.value}' -> '{new_status.value}'"


def process_new_contract(payload: ContractRequest, sequence_id: int = 1) -> ContractResponse:
    """Validates contract payload including company BIN checksum."""
    bin_valid, bin_msg = validate_bin(payload.company_bin)
    if not bin_valid:
        return ContractResponse(
            contract_number="",
            status=ContractStatus.REJECTED,
            is_valid=False,
            message=f"Ошибка валидации БИН предприятия: {bin_msg}",
        )

    contract_num = generate_contract_number(sequence_id)
    return ContractResponse(
        contract_number=contract_num,
        status=ContractStatus.DRAFT,
        is_valid=True,
        message=f"Договор успешно сформирован под номером {contract_num}",
    )
