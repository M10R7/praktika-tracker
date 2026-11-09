"""
Internship contract lifecycle and validation service.
Author: Сәбитов Азамат (гр. АЖ-47)
"""

from enum import Enum

from pydantic import BaseModel, Field

from src.services.bin_validator import validate_bin


class ContractStatus(str, Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    APPROVED_BY_DEAN = "approved_by_dean"
    SIGNED_BY_COMPANY = "signed_by_company"
    ACTIVE = "active"
    IN_ORDER = "in_order"
    COMPLETED = "completed"
    REJECTED = "rejected"
    TERMINATED = "terminated"


ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    ContractStatus.DRAFT.value: {
        ContractStatus.UNDER_REVIEW.value,
        ContractStatus.REJECTED.value,
    },
    ContractStatus.UNDER_REVIEW.value: {
        ContractStatus.APPROVED.value,
        ContractStatus.APPROVED_BY_DEAN.value,
        ContractStatus.REJECTED.value,
    },
    ContractStatus.APPROVED_BY_DEAN.value: {
        ContractStatus.SIGNED_BY_COMPANY.value,
        ContractStatus.REJECTED.value,
    },
    ContractStatus.SIGNED_BY_COMPANY.value: {
        ContractStatus.ACTIVE.value,
        ContractStatus.REJECTED.value,
    },
    ContractStatus.ACTIVE.value: {
        ContractStatus.COMPLETED.value,
        ContractStatus.TERMINATED.value,
    },
    ContractStatus.APPROVED.value: {
        ContractStatus.IN_ORDER.value,
        ContractStatus.REJECTED.value,
    },
    ContractStatus.IN_ORDER.value: {
        ContractStatus.COMPLETED.value,
        ContractStatus.REJECTED.value,
    },
    ContractStatus.REJECTED.value: {
        ContractStatus.DRAFT.value,
        ContractStatus.UNDER_REVIEW.value,
    },
    ContractStatus.COMPLETED.value: set(),
    ContractStatus.TERMINATED.value: set(),
}

STATUS_LABELS_RU = {
    ContractStatus.DRAFT.value: "Черновик",
    ContractStatus.UNDER_REVIEW.value: "На проверке",
    ContractStatus.APPROVED.value: "Согласовано",
    ContractStatus.APPROVED_BY_DEAN.value: "Утвержден деканатом",
    ContractStatus.SIGNED_BY_COMPANY.value: "Подписан организацией",
    ContractStatus.ACTIVE.value: "Действует",
    ContractStatus.REJECTED.value: "Отклонено",
    ContractStatus.IN_ORDER.value: "В приказе",
    ContractStatus.COMPLETED.value: "Завершено",
    ContractStatus.TERMINATED.value: "Расторгнут",
}

STATUS_LABELS_KZ = {
    ContractStatus.DRAFT.value: "Жоба",
    ContractStatus.UNDER_REVIEW.value: "Тексеруде",
    ContractStatus.APPROVED.value: "Келісілді",
    ContractStatus.APPROVED_BY_DEAN.value: "Деканатпен бекітілді",
    ContractStatus.SIGNED_BY_COMPANY.value: "Кәсіпорынмен қол қойылды",
    ContractStatus.ACTIVE.value: "Белсенді",
    ContractStatus.REJECTED.value: "Қабылданбады",
    ContractStatus.IN_ORDER.value: "Бұйрықта",
    ContractStatus.COMPLETED.value: "Аяқталды",
    ContractStatus.TERMINATED.value: "Тоқтатылды",
}

STATUS_STEPS = {
    ContractStatus.DRAFT.value: 1,
    ContractStatus.UNDER_REVIEW.value: 2,
    ContractStatus.APPROVED.value: 4,
    ContractStatus.APPROVED_BY_DEAN.value: 3,
    ContractStatus.SIGNED_BY_COMPANY.value: 4,
    ContractStatus.ACTIVE.value: 5,
    ContractStatus.IN_ORDER.value: 5,
    ContractStatus.REJECTED.value: 0,
    ContractStatus.COMPLETED.value: 5,
}


def validate_contract_transition(current_status: str, new_status: str) -> tuple[bool, str]:
    """Validates if status transition is allowed by business process."""
    if hasattr(current_status, "value"):
        current_status = current_status.value
    if hasattr(new_status, "value"):
        new_status = new_status.value

    if current_status == new_status:
        return True, "Статус не изменился"

    allowed = ALLOWED_TRANSITIONS.get(current_status, set())
    if new_status in allowed:
        return True, f"Переход из '{current_status}' в '{new_status}' разрешен"
    return False, f"Запрещенный переход статуса: '{current_status}' -> '{new_status}'"


def generate_contract_number(sequence_id: int, faculty_code: str = "FIT", year: int = 2026) -> str:
    """Generates standardized official contract number, e.g. Д-2026-FIT-0042."""
    return f"Д-{year}-{faculty_code}-{sequence_id:04d}"


def mask_student_name(full_name: str) -> str:
    """Masks student name for public tracker privacy (SEC-01). E.g. 'Сәбитов А.'"""
    if not full_name:
        return ""
    parts = full_name.strip().split()
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1][0]}."
    return full_name


def mask_iin(iin: str) -> str:
    """Masks IIN showing only birth date prefix (SEC-01). E.g. '020514******'"""
    if not iin or len(iin) < 6:
        return "******"
    return iin[:6] + "******"


# Legacy support models for LZ 10 test suite
class ContractRequest(BaseModel):
    student_id: int = Field(..., gt=0)
    student_fullname: str = Field(..., min_length=3)
    company_name: str = Field(..., min_length=2)
    company_bin: str = Field(..., min_length=12, max_length=12)
    mentor_fullname: str = Field(..., min_length=3)
    academic_supervisor: str = Field(..., min_length=3)
    start_date: str
    end_date: str


class ContractResponse(BaseModel):
    contract_number: str
    status: ContractStatus
    is_valid: bool
    message: str


def process_new_contract(payload: ContractRequest, sequence_id: int = 1) -> ContractResponse:
    """Legacy validation function for backward compatibility."""
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
