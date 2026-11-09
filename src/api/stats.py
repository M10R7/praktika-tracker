"""
API endpoints for Academic & System Telemetry.
Author: Сәбитов Азамат (гр. АЖ-47)
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.core.config import settings
from src.database.models import (
    Company,
    DeanOrder,
    InternshipApplication,
    Student,
)
from src.database.session import get_db

router = APIRouter(prefix="/stats", tags=["Statistics"])


@router.get("")
def get_system_stats(db: Session = Depends(get_db)):
    """Returns aggregated academic capacity and distribution telemetry."""
    total_students = db.query(Student).count()
    total_companies = db.query(Company).count()
    partner_companies = db.query(Company).filter(Company.is_partner.is_(True)).count()

    total_applications = db.query(InternshipApplication).count()
    under_review = (
        db.query(InternshipApplication)
        .filter(InternshipApplication.status == "under_review")
        .count()
    )
    approved = (
        db.query(InternshipApplication).filter(InternshipApplication.status == "approved").count()
    )
    in_order = (
        db.query(InternshipApplication).filter(InternshipApplication.status == "in_order").count()
    )
    rejected = (
        db.query(InternshipApplication).filter(InternshipApplication.status == "rejected").count()
    )

    distributed_count = approved + in_order
    quota = settings.TARGET_STUDENTS_COUNT
    coverage_pct = round((distributed_count / max(quota, 1)) * 100, 1)

    # Top companies by student count
    top_companies_query = (
        db.query(Company.name, func.count(InternshipApplication.id).label("students_count"))
        .join(InternshipApplication, Company.id == InternshipApplication.company_id)
        .filter(InternshipApplication.status.in_(["approved", "in_order", "under_review"]))
        .group_by(Company.name)
        .order_by(func.count(InternshipApplication.id).desc())
        .limit(5)
        .all()
    )
    top_companies = [{"name": row[0], "count": row[1]} for row in top_companies_query]

    # Academic groups breakdown
    groups_query = (
        db.query(Student.group_code, func.count(Student.id).label("total"))
        .group_by(Student.group_code)
        .all()
    )
    groups = [{"group": row[0], "count": row[1]} for row in groups_query]

    orders_count = db.query(DeanOrder).count()

    return {
        "faculty": settings.FACULTY_CODE,
        "faculty_name": settings.FACULTY_NAME_RU,
        "academic_year": settings.ACADEMIC_YEAR,
        "target_students": quota,
        "target_quota": quota,
        "total_students": total_students,
        "total_companies": total_companies,
        "partner_companies": partner_companies,
        "total_applications": total_applications,
        "under_review_count": under_review,
        "approved_count": approved,
        "in_order_count": in_order,
        "rejected_count": rejected,
        "distributed_count": distributed_count,
        "coverage_percentage": coverage_pct,
        "dean_orders_count": orders_count,
        "top_companies": top_companies,
        "groups": groups,
    }
