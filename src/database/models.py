"""
SQLAlchemy ORM models for Praktika-Tracker.
Author: Сәбитов Азамат (гр. АЖ-47)
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from src.database.session import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    bin = Column(String(12), unique=True, index=True, nullable=False)
    name = Column(String(255), index=True, nullable=False)
    legal_form = Column(String(100), default="ТОО")
    address = Column(String(255), default="г. Алматы")
    director_name = Column(String(255), default="")
    contact_person = Column(String(255), default="")
    contact_phone = Column(String(50), default="")
    contact_email = Column(String(100), default="")
    is_partner = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    applications = relationship("InternshipApplication", back_populates="company")


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    iin = Column(String(12), unique=True, index=True, nullable=False)
    full_name = Column(String(255), index=True, nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=False)
    faculty = Column(String(100), default="Факультет информационных технологий")
    specialty_code = Column(String(100), default="6B06101 - Информационные системы")
    group_code = Column(String(50), default="АЖ-47", index=True)
    course = Column(Integer, default=4)
    created_at = Column(DateTime, default=datetime.utcnow)

    applications = relationship("InternshipApplication", back_populates="student")


class InternshipApplication(Base):
    __tablename__ = "internship_applications"

    id = Column(Integer, primary_key=True, index=True)
    application_number = Column(String(50), unique=True, index=True, nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    practice_type = Column(String(100), default="Өндірістік практика / Производственная практика")
    start_date = Column(String(20), default="2026-06-01")
    end_date = Column(String(20), default="2026-07-15")
    company_mentor_name = Column(String(255), nullable=False)
    academic_supervisor_name = Column(String(255), default="Самбетбаева Мадина Аралбаевна")
    status = Column(String(50), default="under_review", index=True)
    rejection_reason = Column(Text, nullable=True)
    contract_file_path = Column(String(255), nullable=True)
    signed_scan_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("Student", back_populates="applications")
    company = relationship("Company", back_populates="applications")
    audit_logs = relationship(
        "StatusAuditLog", back_populates="application", cascade="all, delete-orphan"
    )


class StatusAuditLog(Base):
    """Immutable audit trail for status transitions (SEC-02, НФТ-07)."""

    __tablename__ = "status_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("internship_applications.id"), nullable=False)
    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    changed_by = Column(String(100), default="Координатор практики ФИТ")
    comment = Column(Text, nullable=True)
    ip_address = Column(String(50), default="127.0.0.1")
    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("InternshipApplication", back_populates="audit_logs")


class DeanOrder(Base):
    __tablename__ = "dean_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, index=True, nullable=False)
    order_date = Column(String(20), nullable=False)
    academic_year = Column(String(50), default="2026-2027")
    faculty = Column(String(150), default="Факультет информационных технологий")
    specialty = Column(String(150), default="6B061 - Информационно-коммуникационные технологии")
    total_students = Column(Integer, default=0)
    file_path = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
