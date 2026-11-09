"""
Public Status Tracker API (US-14, SEC-01).
Implements Rate Limiting (15 req/min) and PII masking.
Author: Сәбитов Азамат (гр. АЖ-47)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session, joinedload

from src.core.rate_limiter import limiter
from src.database.models import InternshipApplication, Student
from src.database.session import get_db
from src.schemas.application import PublicTrackerOut
from src.services.contract_service import (
    STATUS_LABELS_KZ,
    STATUS_LABELS_RU,
    STATUS_STEPS,
    mask_iin,
    mask_student_name,
)

router = APIRouter(prefix="/tracker", tags=["Public Tracker"])


@router.get("", response_model=PublicTrackerOut)
@limiter.limit("15/minute")
def track_application_by_iin(
    request: Request,
    iin: str = Query(..., min_length=12, max_length=12, description="12-значный ИИН студента"),
    db: Session = Depends(get_db),
):
    """
    Public endpoint for tracking internship status.
    Protected by Rate Limiter (SEC-01).
    PII (full name, phone, email) is masked for confidentiality.
    """
    clean_iin = iin.strip()

    student = db.query(Student).filter(Student.iin == clean_iin).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заявка с указанным ИИН не найдена в реестре практики.",
        )

    application = (
        db.query(InternshipApplication)
        .options(joinedload(InternshipApplication.company))
        .filter(InternshipApplication.student_id == student.id)
        .order_by(InternshipApplication.id.desc())
        .first()
    )

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="По указанному ИИН отсутствуют активные заявления на производственную практику.",
        )

    st_code = application.status
    return PublicTrackerOut(
        application_number=application.application_number,
        masked_student_name=mask_student_name(student.full_name),
        masked_iin=mask_iin(student.iin),
        company_name=application.company.name,
        practice_type=application.practice_type,
        status=st_code,
        status_label_ru=STATUS_LABELS_RU.get(st_code, st_code),
        status_label_kz=STATUS_LABELS_KZ.get(st_code, st_code),
        status_step=STATUS_STEPS.get(st_code, 2),
        rejection_reason=application.rejection_reason if st_code == "rejected" else None,
        has_contract_doc=bool(application.contract_file_path),
        has_signed_scan=bool(application.signed_scan_path),
        updated_at=application.updated_at.strftime("%d.%m.%Y %H:%M")
        if application.updated_at
        else "",
    )
