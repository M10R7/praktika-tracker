"""
API endpoints for Companies & Internship Bases (US-02, US-07).
Author: Сәбитов Азамат (гр. АЖ-47)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.database.models import Company
from src.database.session import get_db
from src.schemas.company import CompanyCreate, CompanyOut
from src.services.bin_validator import parse_bin_info, validate_bin

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.get("", response_model=list[CompanyOut])
def list_companies(
    partner_only: bool = Query(True, description="Показывать только проверенных партнеров"),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Returns list of partner companies for student application selection and directory."""
    q = db.query(Company)
    if partner_only:
        q = q.filter(Company.is_partner.is_(True))

    if search:
        term = f"%{search.strip()}%"
        q = q.filter((Company.name.ilike(term)) | (Company.bin.ilike(term)))

    return q.order_by(Company.name.asc()).all()


@router.post("", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
def add_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    """
    Adds a new verified company to the accredited internship catalog (US-07).
    Validates 12-digit BIN with KGD RK checksum algorithm.
    """
    bin_ok, bin_msg = validate_bin(payload.bin)
    if not bin_ok:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Ошибка валидации БИН предприятия: {bin_msg}",
        )

    existing = db.query(Company).filter(Company.bin == payload.bin.strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Организация с БИН {payload.bin} уже зарегистрирована в каталоге под наименованием '{existing.name}'",
        )

    company = Company(
        bin=payload.bin.strip(),
        name=payload.name.strip(),
        legal_form=payload.legal_form,
        address=payload.address,
        director_name=payload.director_name or "",
        contact_person=payload.contact_person or "",
        contact_phone=payload.contact_phone or "",
        contact_email=payload.contact_email or "",
        is_partner=payload.is_partner,
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("/{company_bin}/info")
def get_company_bin_info(company_bin: str):
    """Returns parsed metadata and verification status for a 12-digit BIN."""
    is_valid, msg = validate_bin(company_bin)
    info = parse_bin_info(company_bin)
    return {
        "bin": company_bin,
        "is_valid": is_valid,
        "message": msg,
        "details": info,
    }
