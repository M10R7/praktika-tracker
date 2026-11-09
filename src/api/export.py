"""
API endpoints for Registry Exports (US-10).
Author: Сәбитов Азамат (гр. АЖ-47)
"""

from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload

from src.database.models import InternshipApplication
from src.database.session import get_db
from src.services.export_service import export_applications_to_csv

router = APIRouter(prefix="/export", tags=["Exports"])


@router.get("/csv")
def export_registry_csv(db: Session = Depends(get_db)):
    """Exports full internship applications registry to CSV (US-10) with UTF-8 BOM."""
    applications = (
        db.query(InternshipApplication)
        .options(
            joinedload(InternshipApplication.student),
            joinedload(InternshipApplication.company),
        )
        .order_by(InternshipApplication.id.asc())
        .all()
    )

    csv_data = export_applications_to_csv(applications)
    filename = f"praktika_registry_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

    return Response(
        content=csv_data.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
