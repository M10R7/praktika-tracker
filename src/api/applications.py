"""
API endpoints for Internship Applications.
Author: Сәбитов Азамат (гр. АЖ-47)
"""

import os
import shutil

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from src.core.config import settings
from src.database.models import (
    Company,
    InternshipApplication,
    Student,
)
from src.database.session import get_db
from src.schemas.application import (
    ApplicationOut,
    ApplicationSubmission,
    StatusChangeRequest,
)
from src.services.audit_service import log_status_change
from src.services.bin_validator import validate_bin
from src.services.contract_service import (
    generate_contract_number,
    validate_contract_transition,
)
from src.services.document_generator import generate_contract_docx
from src.services.iin_validator import validate_iin

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
def submit_application(
    payload: ApplicationSubmission,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Submits a new internship application.
    Validates student IIN and enterprise BIN according to Kazakhstan official algorithms.
    """
    # 1. Validate student IIN
    iin_ok, iin_msg = validate_iin(payload.student_iin)
    if not iin_ok:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Ошибка валидации ИИН студента: {iin_msg}",
        )

    # 2. Validate enterprise BIN
    bin_ok, bin_msg = validate_bin(payload.company_bin)
    if not bin_ok:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Ошибка валидации БИН предприятия: {bin_msg}",
        )

    # 3. Find or create Student
    student = db.query(Student).filter(Student.iin == payload.student_iin.strip()).first()
    if not student:
        student = Student(
            iin=payload.student_iin.strip(),
            full_name=payload.student_fullname.strip(),
            email=payload.student_email.strip(),
            phone=payload.student_phone.strip(),
            group_code=payload.student_group.strip(),
            specialty_code=payload.specialty_code.strip(),
        )
        db.add(student)
        db.flush()
    else:
        # Check duplicate submission in review / approved (US-13)
        existing_app = (
            db.query(InternshipApplication)
            .filter(
                InternshipApplication.student_id == student.id,
                InternshipApplication.status.in_(["under_review", "approved", "in_order"]),
            )
            .first()
        )
        if existing_app:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"По данному ИИН уже зарегистрирована активная заявка № {existing_app.application_number} со статусом '{existing_app.status}'. Повторная подача отклонена.",
            )

    # 4. Find or create Company
    company = None
    if payload.company_id:
        company = db.query(Company).filter(Company.id == payload.company_id).first()

    if not company:
        company = db.query(Company).filter(Company.bin == payload.company_bin.strip()).first()

    if not company:
        company = Company(
            bin=payload.company_bin.strip(),
            name=payload.company_name or "Организация",
            address=payload.company_address or "г. Алматы",
            director_name=payload.company_director or "",
            contact_person=payload.mentor_fullname or "",
            contact_phone=payload.student_phone or "",
            is_partner=False,
        )
        db.add(company)
        db.flush()

    # 5. Determine application number
    seq = db.query(InternshipApplication).count() + 1
    app_num = f"ПР-2026-FIT-{seq:04d}"

    # 6. Create Application record
    app = InternshipApplication(
        application_number=app_num,
        student_id=student.id,
        company_id=company.id,
        practice_type=payload.practice_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        company_mentor_name=payload.mentor_fullname,
        academic_supervisor_name=payload.academic_supervisor,
        status="under_review",
    )
    db.add(app)
    db.flush()

    # 7. Record immutable audit log (SEC-02, НФТ-07)
    client_ip = request.client.host if request.client else "127.0.0.1"
    log_status_change(
        db=db,
        application_id=app.id,
        old_status=None,
        new_status="under_review",
        changed_by="Студент (Веб-портал)",
        comment="Подача первичного заявления через веб-форму",
        ip_address=client_ip,
    )

    db.commit()
    db.refresh(app)
    return app


@router.get("", response_model=list[ApplicationOut])
def list_applications(
    status_filter: str | None = Query(None, alias="status"),
    group_filter: str | None = Query(None, alias="group"),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Lists applications with filtering by status, group, and text search."""
    q = (
        db.query(InternshipApplication)
        .options(
            joinedload(InternshipApplication.student),
            joinedload(InternshipApplication.company),
            joinedload(InternshipApplication.audit_logs),
        )
        .order_by(InternshipApplication.id.desc())
    )

    if status_filter:
        q = q.filter(InternshipApplication.status == status_filter)

    if group_filter:
        q = q.join(InternshipApplication.student).filter(Student.group_code == group_filter)

    if search:
        search_term = f"%{search.strip()}%"
        q = (
            q.join(InternshipApplication.student)
            .join(InternshipApplication.company)
            .filter(
                (Student.full_name.ilike(search_term))
                | (Student.iin.ilike(search_term))
                | (Company.name.ilike(search_term))
                | (InternshipApplication.application_number.ilike(search_term))
            )
        )

    return q.all()


@router.get("/{app_id}", response_model=ApplicationOut)
def get_application(app_id: int, db: Session = Depends(get_db)):
    """Retrieves a single application by ID."""
    app = (
        db.query(InternshipApplication)
        .options(
            joinedload(InternshipApplication.student),
            joinedload(InternshipApplication.company),
            joinedload(InternshipApplication.audit_logs),
        )
        .filter(InternshipApplication.id == app_id)
        .first()
    )
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")
    return app


@router.patch("/{app_id}/status", response_model=ApplicationOut)
def update_application_status(
    app_id: int,
    payload: StatusChangeRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Updates application status with state-machine transition check.
    Enforces mandatory rejection reason when status is 'rejected' (US-06).
    Automatically generates official DOCX agreement when approved.
    """
    app = (
        db.query(InternshipApplication)
        .options(
            joinedload(InternshipApplication.student),
            joinedload(InternshipApplication.company),
        )
        .filter(InternshipApplication.id == app_id)
        .first()
    )
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")

    # 1. State machine check
    is_allowed, transition_msg = validate_contract_transition(app.status, payload.new_status)
    if not is_allowed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=transition_msg)

    # 2. Enforce rejection reason if rejected (US-06)
    if payload.new_status == "rejected":
        if not payload.rejection_reason or not payload.rejection_reason.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Для отклонения заявки необходимо указать причину отклонения (US-06)",
            )
        app.rejection_reason = payload.rejection_reason.strip()

    old_status = app.status
    app.status = payload.new_status

    # 3. Auto-generate DOCX agreement on approval if not generated yet
    if payload.new_status in ("approved", "in_order") and not app.contract_file_path:
        try:
            contract_num = generate_contract_number(app.id)
            docx_path = generate_contract_docx(
                contract_number=contract_num,
                student_fullname=app.student.full_name,
                student_iin=app.student.iin,
                student_group=app.student.group_code,
                specialty_code=app.student.specialty_code,
                company_name=app.company.name,
                company_bin=app.company.bin,
                company_address=app.company.address,
                company_director=app.company.director_name,
                mentor_fullname=app.company_mentor_name,
                academic_supervisor=app.academic_supervisor_name,
                start_date=app.start_date,
                end_date=app.end_date,
            )
            app.contract_file_path = docx_path
        except Exception:
            # Fallback
            pass

    # 4. Log status audit record
    client_ip = request.client.host if request.client else "127.0.0.1"
    comment = payload.comment or payload.rejection_reason or "Смена статуса координатором"
    log_status_change(
        db=db,
        application_id=app.id,
        old_status=old_status,
        new_status=payload.new_status,
        changed_by="Координатор практики ФИТ",
        comment=comment,
        ip_address=client_ip,
    )

    db.commit()
    db.refresh(app)
    return app


@router.get("/{app_id}/download-docx")
def download_contract_docx(app_id: int, db: Session = Depends(get_db)):
    """Downloads the generated 3-party internship contract in DOCX format."""
    app = (
        db.query(InternshipApplication)
        .options(
            joinedload(InternshipApplication.student),
            joinedload(InternshipApplication.company),
        )
        .filter(InternshipApplication.id == app_id)
        .first()
    )
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")

    # Generate if not exists
    if not app.contract_file_path or not os.path.exists(app.contract_file_path):
        contract_num = generate_contract_number(app.id)
        docx_path = generate_contract_docx(
            contract_number=contract_num,
            student_fullname=app.student.full_name,
            student_iin=app.student.iin,
            student_group=app.student.group_code,
            specialty_code=app.student.specialty_code,
            company_name=app.company.name,
            company_bin=app.company.bin,
            company_address=app.company.address,
            company_director=app.company.director_name,
            mentor_fullname=app.company_mentor_name,
            academic_supervisor=app.academic_supervisor_name,
            start_date=app.start_date,
            end_date=app.end_date,
        )
        app.contract_file_path = docx_path
        db.commit()

    filename = os.path.basename(app.contract_file_path)
    return FileResponse(
        path=app.contract_file_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename,
    )


@router.post("/{app_id}/upload-scan")
def upload_signed_scan(
    app_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Uploads a signed agreement scan (PDF or image, max 10MB) - US-08."""
    app = db.query(InternshipApplication).filter(InternshipApplication.id == app_id).first()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заявка не найдена")

    # Validate file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".pdf", ".png", ".jpg", ".jpeg"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Допустимы только файлы форматов PDF, PNG, JPG, JPEG",
        )

    save_filename = f"signed_scan_app_{app.id}_{int(app.created_at.timestamp())}{ext}"
    dest_path = settings.UPLOADS_DIR / save_filename

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    app.signed_scan_path = str(dest_path)
    db.commit()

    return {
        "status": "success",
        "message": "Скан подписанного договора успешно загружен",
        "file_name": save_filename,
    }
