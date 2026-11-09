"""
Audit Trail service (SEC-02, НФТ-07).
Records immutable history of all application status changes.
Author: Сәбитов Азамат (гр. АЖ-47)
"""

from sqlalchemy.orm import Session

from src.database.models import StatusAuditLog


def log_status_change(
    db: Session,
    application_id: int,
    old_status: str | None,
    new_status: str,
    changed_by: str = "Координатор практики ФИТ",
    comment: str | None = "",
    ip_address: str | None = "127.0.0.1",
) -> StatusAuditLog:
    """Inserts an immutable audit record for an application state transition."""
    audit_entry = StatusAuditLog(
        application_id=application_id,
        old_status=old_status,
        new_status=new_status,
        changed_by=changed_by,
        comment=comment or "",
        ip_address=ip_address or "127.0.0.1",
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)
    return audit_entry
