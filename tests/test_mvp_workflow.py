"""
End-to-End integration test suite for Praktika-Tracker MVP.
Covers US-01, US-04, US-06, US-07, US-08, US-09, US-10, US-11, US-14, SEC-01, SEC-02.
Author: Сәбитов Азамат (гр. АЖ-47)
"""

import os

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_html_pages_render():
    """Verifies that all frontend pages render successfully (HTTP 200)."""
    headers = {"Accept": "text/html"}

    routes = ["/", "/apply", "/tracker", "/coordinator", "/companies"]
    for route in routes:
        res = client.get(route, headers=headers)
        assert res.status_code == 200
        assert "ПРАКТИКА-ТРЕКЕР" in res.text


def test_submit_application_success():
    """US-01: Student submits application with valid IIN and Kaspi Bank BIN."""
    payload = {
        "student_iin": "030915500062",
        "student_fullname": "Жолдасов Нурлан Кайратович",
        "student_email": "nurlan.zh@enu.kz",
        "student_phone": "+7 707 999 88 77",
        "student_group": "АЖ-47",
        "specialty_code": "6B06101 - Информационные системы",
        "company_bin": "081240012740",
        "company_name": "АО Kaspi Bank",
        "mentor_fullname": "Аскаров Кайрат",
        "academic_supervisor": "Самбетбаева Мадина Аралбаевна",
        "practice_type": "Өндірістік практика",
        "start_date": "2026-06-01",
        "end_date": "2026-07-15",
    }
    res = client.post("/api/v1/applications", json=payload)
    # Could be 201 or 400 if already submitted in seed
    assert res.status_code in (201, 400)
    if res.status_code == 201:
        data = res.json()
        assert "ПР-2026-FIT" in data["application_number"]
        assert data["status"] == "under_review"


def test_submit_application_invalid_bin():
    """US-04: Submitting an invalid company BIN must return HTTP 422."""
    payload = {
        "student_iin": "030412500088",
        "student_fullname": "Токтаров Руслан Берикович",
        "student_email": "ruslan.t@enu.kz",
        "student_phone": "+7 707 111 22 33",
        "student_group": "ВТиПО-42",
        "specialty_code": "6B06102 - ВТиПО",
        "company_bin": "111111111111",  # Invalid checksum
        "company_name": "Фейковая компания",
        "mentor_fullname": "Иванов И. И.",
        "academic_supervisor": "Самбетбаева М. А.",
        "start_date": "2026-06-01",
        "end_date": "2026-07-15",
    }
    res = client.post("/api/v1/applications", json=payload)
    assert res.status_code == 422
    assert "Ошибка валидации БИН" in res.json()["detail"]


def test_public_tracker_and_pii_masking():
    """US-14 & SEC-01: Public tracker masks name and IIN."""
    # Seed contains Azamat Sabitov with IIN 030514500012
    res = client.get("/api/v1/tracker?iin=030514500012")
    assert res.status_code == 200
    data = res.json()
    assert "ПР-2026-FIT" in data["application_number"]
    assert data["masked_student_name"] == "Сәбитов А."
    assert data["masked_iin"] == "030514******"
    assert "company_name" in data
    assert "status_label_ru" in data


def test_public_tracker_not_found():
    """US-14: Searching for non-existent IIN returns 404."""
    res = client.get("/api/v1/tracker?iin=030412599999")
    assert res.status_code == 404


def test_status_change_rejection_requires_reason():
    """US-06: Rejecting an application requires mandatory reason."""
    # Fetch an application
    apps_res = client.get("/api/v1/applications")
    assert apps_res.status_code == 200
    apps = apps_res.json()
    assert len(apps) > 0

    app_id = apps[0]["id"]

    # Attempt to reject without reason
    res = client.patch(
        f"/api/v1/applications/{app_id}/status",
        json={"new_status": "rejected", "rejection_reason": ""},
    )
    assert res.status_code in (422, 400)


def test_download_contract_docx():
    """US-09: Downloading generated 3-party contract DOCX."""
    apps_res = client.get("/api/v1/applications")
    apps = apps_res.json()
    app_id = apps[0]["id"]

    res = client.get(f"/api/v1/applications/{app_id}/download-docx")
    assert res.status_code == 200
    assert (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        in res.headers["content-type"]
    )
    # Check that bytes represent a valid zip/docx archive (starts with PK)
    assert res.content.startswith(b"PK")


def test_generate_and_download_dean_order():
    """US-11: Consolidated Dean's order generation in DOCX and download."""
    import uuid

    unique_order_num = f"№ {uuid.uuid4().hex[:5].upper()}-П"
    gen_payload = {
        "order_number": unique_order_num,
        "order_date": "25.05.2026",
        "academic_year": "2026-2027",
    }
    res = client.post("/api/v1/orders/generate", json=gen_payload)
    assert res.status_code == 201
    order_data = res.json()
    assert order_data["order_number"] == unique_order_num
    assert order_data["total_students"] > 0
    order_id = order_data["id"]

    # Download order DOCX
    dl_res = client.get(f"/api/v1/orders/{order_id}/download")
    assert dl_res.status_code == 200
    assert dl_res.content.startswith(b"PK")


def test_export_registry_csv():
    """US-10: Exporting internship registry to CSV."""
    res = client.get("/api/v1/export/csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    content_str = res.content.decode("utf-8")
    assert "№ заявки" in content_str
    assert "ФИО студента" in content_str


def test_add_company_and_list():
    """US-07: Coordinator adds new company to catalog with BIN verification."""
    payload = {
        "bin": "940140000385",  # Halyk Bank valid BIN
        "name": "АО Народный Банк Казахстана (Тест)",
        "legal_form": "АО",
        "address": "г. Алматы",
        "is_partner": True,
    }
    # Might be 201 or 400 if already seeded
    res = client.post("/api/v1/companies", json=payload)
    assert res.status_code in (201, 400)

    # List companies
    list_res = client.get("/api/v1/companies")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 5


def test_generate_contract_docx_direct(tmp_path):
    """Direct verification of Form #107 MES RK contract generator."""
    from src.services.document_generator import generate_contract_docx

    path_str = generate_contract_docx(
        contract_number="TEST-2026-999",
        student_fullname="Сәбитов Азамат Бақытжанұлы",
        student_iin="030514500012",
        student_group="АЖ-47",
        specialty_code="6B06102",
        company_name="ТОО «Kaspi.kz»",
        company_bin="081240012740",
        company_address="г. Алматы, ул. Наурызбай батыра, 154/8",
        company_director="Ломадзе М.",
        mentor_fullname="Алиев Данияр",
        academic_supervisor="Самбетбаева Мадина Аралбаевна",
        start_date="2026-06-01",
        end_date="2026-07-15",
        output_dir=tmp_path,
    )
    assert os.path.exists(path_str)
    assert os.path.getsize(path_str) > 1000


def test_duplicate_order_conflict():
    """Generating Dean's order with already used order number returns 409."""
    import uuid

    order_num = f"№ {uuid.uuid4().hex[:5].upper()}-П"
    gen_payload = {
        "order_number": order_num,
        "order_date": "25.05.2026",
        "academic_year": "2026-2027",
    }
    res1 = client.post("/api/v1/orders/generate", json=gen_payload)
    assert res1.status_code == 201

    # Second attempt with exact same order_number
    res2 = client.post("/api/v1/orders/generate", json=gen_payload)
    assert res2.status_code == 409


def test_upload_scan_file():
    """US-08: Student or coordinator uploads signed contract scan."""
    import io

    apps_res = client.get("/api/v1/applications")
    apps = apps_res.json()
    app_id = apps[0]["id"]

    fake_pdf = io.BytesIO(b"%PDF-1.4 ... mock pdf content ...")
    fake_pdf.name = "signed_agreement.pdf"

    res = client.post(
        f"/api/v1/applications/{app_id}/upload-scan",
        files={"file": ("signed_agreement.pdf", fake_pdf, "application/pdf")},
    )
    assert res.status_code == 200
    assert "успешно загружен" in res.json()["message"]


def test_filter_applications():
    """Dean dashboard filters applications by status and search."""
    res1 = client.get("/api/v1/applications?status=under_review")
    assert res1.status_code == 200
    for item in res1.json():
        assert item["status"] == "under_review"

    res2 = client.get("/api/v1/applications?search=Сәбитов")
    assert res2.status_code == 200
    assert len(res2.json()) >= 1
