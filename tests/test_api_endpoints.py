"""
Integration tests for FastAPI endpoints.
"""

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_api_validate_bin_success():
    response = client.post("/api/v1/bin/validate", json={"bin": "081240012740"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert data["info"]["valid"] is True


def test_api_validate_bin_failure():
    response = client.post("/api/v1/bin/validate", json={"bin": "000000000000"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False


def test_api_create_contract_endpoint_success():
    payload = {
        "student_id": 42,
        "student_fullname": "Сәбитов Азамат",
        "company_name": "АО Казахтелеком",
        "company_bin": "941240000193",
        "mentor_fullname": "Смагулов Б. Е.",
        "academic_supervisor": "Самбетбаева М. А.",
        "start_date": "2026-06-01",
        "end_date": "2026-07-15",
    }
    response = client.post("/api/v1/contracts", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert "Д-2026-FIT" in data["contract_number"]


def test_api_create_contract_endpoint_invalid_bin():
    payload = {
        "student_id": 42,
        "student_fullname": "Сәбитов Азамат",
        "company_name": "Фейковая компания",
        "company_bin": "111111111111",
        "mentor_fullname": "Смагулов Б. Е.",
        "academic_supervisor": "Самбетбаева М. А.",
        "start_date": "2026-06-01",
        "end_date": "2026-07-15",
    }
    response = client.post("/api/v1/contracts", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "Ошибка валидации БИН" in data["detail"]


def test_api_check_transition():
    payload = {
        "current_status": "draft",
        "new_status": "under_review",
    }
    response = client.post("/api/v1/contracts/transition", json=payload)
    assert response.status_code == 200
    assert response.json()["allowed"] is True


def test_api_stats():
    response = client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["faculty"] == "FIT"
    assert data["target_students"] == 250
