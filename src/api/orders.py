"""
API endpoints for Dean's Orders (US-11, WBS 1.3.4).
Author: Сәбитов Азамат (гр. АЖ-47)
"""

import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from src.core.config import settings
from src.database.models import (
    DeanOrder,
    InternshipApplication,
    Student,
)
from src.database.session import get_db
from src.schemas.order import OrderGenerateRequest, OrderOut
from src.services.audit_service import log_status_change
from src.services.order_generator import generate_dean_order_docx

router = APIRouter(prefix="/orders", tags=["Dean Orders"])


@router.post("/generate", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_dean_order(
    payload: OrderGenerateRequest,
    db: Session = Depends(get_db),
):
    """
    Generates a consolidated Faculty Dean's Order in DOCX format (US-11).
    Aggregates all approved students by enterprise in alphabetical order.
    Identifies unassigned students and reports them to coordinator.
    """
    # 1. Fetch approved / in-order applications
    apps = (
        db.query(InternshipApplication)
        .options(
            joinedload(InternshipApplication.student),
            joinedload(InternshipApplication.company),
        )
        .filter(InternshipApplication.status.in_(["approved", "in_order"]))
        .all()
    )

    if not apps:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="В системе нет согласованных заявок для формирования приказа. Сначала согласуйте заявки студентов.",
        )

    # 2. Fetch all students in current cohort
    all_students = db.query(Student).all()
    students_data = [
        {"iin": s.iin, "full_name": s.full_name, "group_code": s.group_code} for s in all_students
    ]

    # 3. Prepare payload for generator
    approved_payload = []
    for a in apps:
        approved_payload.append(
            {
                "student_fullname": a.student.full_name,
                "student_iin": a.student.iin,
                "student_group": a.student.group_code,
                "company_name": a.company.name,
                "company_bin": a.company.bin,
                "start_date": a.start_date,
                "end_date": a.end_date,
                "mentor_fullname": a.company_mentor_name,
                "academic_supervisor": a.academic_supervisor_name,
            }
        )

    order_num = payload.order_number or f"№ {db.query(DeanOrder).count() + 142}-П"
    order_date = payload.order_date or datetime.now().strftime("%d.%m.%Y")

    # Check for existing order number to prevent IntegrityError
    existing_order = db.query(DeanOrder).filter(DeanOrder.order_number == order_num).first()
    if existing_order:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Приказ с номером '{order_num}' уже зарегистрирован в системе.",
        )

    # 4. Generate DOCX file
    docx_path, unassigned_list = generate_dean_order_docx(
        order_number=order_num,
        order_date=order_date,
        academic_year=payload.academic_year or settings.ACADEMIC_YEAR,
        faculty_name=payload.faculty or settings.FACULTY_NAME_RU,
        specialty_name=payload.specialty or "6B061 - Информационно-коммуникационные технологии",
        approved_applications=approved_payload,
        all_students_in_cohort=students_data,
    )

    # 5. Save order in database
    dean_order = DeanOrder(
        order_number=order_num,
        order_date=order_date,
        academic_year=payload.academic_year or settings.ACADEMIC_YEAR,
        faculty=payload.faculty or settings.FACULTY_NAME_RU,
        specialty=payload.specialty or "6B061 - Информационно-коммуникационные технологии",
        total_students=len(approved_payload),
        file_path=docx_path,
    )
    db.add(dean_order)

    # 6. Mark applications as in_order
    for a in apps:
        if a.status != "in_order":
            a.status = "in_order"
            log_status_change(
                db=db,
                application_id=a.id,
                old_status="approved",
                new_status="in_order",
                changed_by="Координатор практики ФИТ",
                comment=f"Включение студента в сводный приказ {order_num}",
            )

    db.commit()
    db.refresh(dean_order)

    return OrderOut(
        id=dean_order.id,
        order_number=dean_order.order_number,
        order_date=dean_order.order_date,
        academic_year=dean_order.academic_year,
        faculty=dean_order.faculty,
        specialty=dean_order.specialty,
        total_students=dean_order.total_students,
        file_path=dean_order.file_path,
        created_at=dean_order.created_at,
        unassigned_students_count=len(unassigned_list),
        unassigned_students=unassigned_list,
    )


@router.get("", response_model=list[OrderOut])
def list_dean_orders(db: Session = Depends(get_db)):
    """Lists past generated Dean's orders."""
    orders = db.query(DeanOrder).order_by(DeanOrder.id.desc()).all()
    res = []
    for o in orders:
        res.append(
            OrderOut(
                id=o.id,
                order_number=o.order_number,
                order_date=o.order_date,
                academic_year=o.academic_year,
                faculty=o.faculty,
                specialty=o.specialty,
                total_students=o.total_students,
                file_path=o.file_path,
                created_at=o.created_at,
                unassigned_students_count=0,
                unassigned_students=[],
            )
        )
    return res


@router.get("/{order_id}/download")
def download_order_docx(order_id: int, db: Session = Depends(get_db)):
    """Downloads the generated Dean's order DOCX document."""
    order = db.query(DeanOrder).filter(DeanOrder.id == order_id).first()
    if not order or not os.path.exists(order.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Файл приказа не найден")

    filename = os.path.basename(order.file_path)
    return FileResponse(
        path=order.file_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename,
    )
