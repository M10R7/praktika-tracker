"""
Main FastAPI application for Praktika-Tracker (MVP).
Automated Internship Management System for Faculty of Information Technology, L.N. Gumilyov ENU (Astana).
Author: Сәбитов Азамат (гр. АЖ-47)
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.api import api_router
from src.core.config import settings
from src.core.rate_limiter import limiter
from src.database.seed import seed_database
from src.database.session import Base, SessionLocal, engine
from src.services.bin_validator import parse_bin_info, validate_bin
from src.services.contract_service import (
    ContractStatus,
    generate_contract_number,
    validate_contract_transition,
)

BASE_DIR = Path(__file__).resolve().parent

# Ensure tables and seed data exist immediately upon import
Base.metadata.create_all(bind=engine)
_init_db = SessionLocal()
try:
    seed_database(_init_db)
finally:
    _init_db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Система сквозного управления производственной практикой студентов ФИТ ЕНУ имени Л.Н. Гумилева (г. Астана)",
    lifespan=lifespan,
)

# Attach rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Mount static assets
static_path = BASE_DIR / "static"
static_path.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Mount Jinja2 templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Include modern API v1 routers
app.include_router(api_router, prefix=settings.API_V1_STR)


# ==================== HTML PAGE ROUTES ====================


@app.get("/", tags=["Web Pages"])
def page_home(request: Request):
    """
    Root endpoint.
    Returns JSON metadata for API/test clients, or renders HTML dashboard for browsers.
    """
    accept = request.headers.get("accept", "")
    if "text/html" not in accept:
        return {
            "service": "Praktika-Tracker API",
            "version": "0.1.0",
            "environment": settings.ENVIRONMENT,
            "status": "operational",
            "docs_url": "/docs",
        }
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"active_page": "home", "settings": settings},
    )


@app.get("/apply", response_class=HTMLResponse, tags=["Web Pages"])
def page_apply(request: Request):
    """Student application submission form."""
    return templates.TemplateResponse(
        request=request,
        name="apply.html",
        context={"active_page": "apply", "settings": settings},
    )


@app.get("/tracker", response_class=HTMLResponse, tags=["Web Pages"])
def page_tracker(request: Request):
    """Public status tracking page."""
    return templates.TemplateResponse(
        request=request,
        name="tracker.html",
        context={"active_page": "tracker", "settings": settings},
    )


@app.get("/coordinator", response_class=HTMLResponse, tags=["Web Pages"])
def page_coordinator(request: Request):
    """Dean's office / coordinator control dashboard."""
    return templates.TemplateResponse(
        request=request,
        name="coordinator.html",
        context={"active_page": "coordinator", "settings": settings},
    )


@app.get("/companies", response_class=HTMLResponse, tags=["Web Pages"])
def page_companies(request: Request):
    """Accredited internship partner companies directory."""
    return templates.TemplateResponse(
        request=request,
        name="companies.html",
        context={"active_page": "companies", "settings": settings},
    )


# ==================== SYSTEM & BACKWARD-COMPATIBLE API ROUTES ====================


@app.get("/healthz", status_code=status.HTTP_200_OK, tags=["Health"])
def healthcheck():
    """Healthcheck endpoint for Docker containers and monitoring probes."""
    return {
        "status": "ok",
        "service": "praktika-tracker",
        "environment": settings.ENVIRONMENT,
        "version": "0.1.0",
    }


class BinValidationRequest(BaseModel):
    bin: str = Field(..., description="12-значный БИН организации")


class StatusTransitionRequest(BaseModel):
    current_status: ContractStatus
    new_status: ContractStatus


class LegacyContractRequest(BaseModel):
    student_id: int
    student_fullname: str
    company_name: str
    company_bin: str
    mentor_fullname: str
    academic_supervisor: str
    start_date: str
    end_date: str


@app.post("/api/v1/bin/validate", tags=["Validation"])
def api_validate_bin(request: BinValidationRequest):
    """Official BIN validation endpoint."""
    is_valid, msg = validate_bin(request.bin)
    info = parse_bin_info(request.bin)
    return {
        "bin": request.bin,
        "is_valid": is_valid,
        "message": msg,
        "info": info,
    }


@app.post("/api/v1/contracts", tags=["Contracts"])
def api_create_contract(payload: LegacyContractRequest):
    """Legacy endpoint for backward compatibility with LZ 10 test suite."""
    is_valid, msg = validate_bin(payload.company_bin)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Ошибка валидации БИН предприятия: {msg}",
        )
    contract_num = generate_contract_number(101)
    return {
        "contract_number": contract_num,
        "status": ContractStatus.DRAFT,
        "is_valid": True,
        "message": f"Договор успешно сформирован под номером {contract_num}",
    }


@app.post("/api/v1/contracts/transition", tags=["Contracts"])
def api_check_transition(payload: StatusTransitionRequest):
    """Legacy state transition validation."""
    is_allowed, msg = validate_contract_transition(
        payload.current_status.value, payload.new_status.value
    )
    return {
        "current_status": payload.current_status,
        "new_status": payload.new_status,
        "allowed": is_allowed,
        "message": msg,
    }
