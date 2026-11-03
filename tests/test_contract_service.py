"""
Unit tests for internship contract service and state machine.
"""

from src.services.contract_service import (
    ContractRequest,
    ContractStatus,
    generate_contract_number,
    process_new_contract,
    validate_contract_transition,
)


def test_generate_contract_number():
    assert generate_contract_number(1) == "Д-2026-FIT-0001"
    assert generate_contract_number(42, faculty_code="FIT", year=2026) == "Д-2026-FIT-0042"


def test_valid_transitions():
    allowed_pairs = [
        (ContractStatus.DRAFT, ContractStatus.UNDER_REVIEW),
        (ContractStatus.UNDER_REVIEW, ContractStatus.APPROVED_BY_DEAN),
        (ContractStatus.APPROVED_BY_DEAN, ContractStatus.SIGNED_BY_COMPANY),
        (ContractStatus.SIGNED_BY_COMPANY, ContractStatus.ACTIVE),
        (ContractStatus.ACTIVE, ContractStatus.COMPLETED),
    ]
    for curr, nxt in allowed_pairs:
        ok, msg = validate_contract_transition(curr, nxt)
        assert ok is True
        assert "разрешен" in msg


def test_invalid_transitions():
    forbidden_pairs = [
        (ContractStatus.DRAFT, ContractStatus.ACTIVE),
        (ContractStatus.COMPLETED, ContractStatus.DRAFT),
        (ContractStatus.TERMINATED, ContractStatus.ACTIVE),
    ]
    for curr, nxt in forbidden_pairs:
        ok, msg = validate_contract_transition(curr, nxt)
        assert ok is False
        assert "Запрещенный" in msg


def test_process_new_contract_success():
    req = ContractRequest(
        student_id=1,
        student_fullname="Сәбитов Азамат",
        company_name="АО Kaspi Bank",
        company_bin="081240012740",
        mentor_fullname="Иванов И. И.",
        academic_supervisor="Самбетбаева М. А.",
        start_date="2026-06-01",
        end_date="2026-07-15",
    )
    res = process_new_contract(req, sequence_id=101)
    assert res.is_valid is True
    assert res.contract_number == "Д-2026-FIT-0101"
    assert res.status == ContractStatus.DRAFT


def test_process_new_contract_invalid_bin():
    req = ContractRequest(
        student_id=1,
        student_fullname="Сәбитов Азамат",
        company_name="Несуществующая организация",
        company_bin="123456789012",
        mentor_fullname="Иванов И. И.",
        academic_supervisor="Самбетбаева М. А.",
        start_date="2026-06-01",
        end_date="2026-07-15",
    )
    res = process_new_contract(req, sequence_id=101)
    assert res.is_valid is False
    assert res.status == ContractStatus.REJECTED
    assert "Ошибка валидации БИН" in res.message
