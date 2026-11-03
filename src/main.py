"""
Main FastAPI application for Praktika-Tracker.
Author: Сәбитов Азамат (гр. АЖ-47)
"""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from src.core.config import settings
from src.services.bin_validator import parse_bin_info, validate_bin
from src.services.contract_service import (
    ContractRequest,
    ContractResponse,
    ContractStatus,
    process_new_contract,
    validate_contract_transition,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Система сквозного управления производственной практикой студентов ФИТ КазНУ имени аль-Фараби",
)


class BinValidationRequest(BaseModel):
    bin: str = Field(..., description="12-значный БИН организации")


class StatusTransitionRequest(BaseModel):
    current_status: ContractStatus
    new_status: ContractStatus


@app.get("/")
def read_root():
    """Root endpoint providing service metadata."""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "operational",
        "docs_url": "/docs",
    }


@app.get("/healthz", status_code=status.HTTP_200_OK)
def healthcheck():
    """Healthcheck endpoint for Docker container and orchestrator probes."""
    return {
        "status": "ok",
        "service": "praktika-tracker",
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION,
    }


@app.post("/api/v1/bin/validate")
def api_validate_bin(request: BinValidationRequest):
    """Endpoint for validating Kazakhstani organization BIN with official checksum rules."""
    is_valid, msg = validate_bin(request.bin)
    info = parse_bin_info(request.bin)
    return {
        "bin": request.bin,
        "is_valid": is_valid,
        "message": msg,
        "info": info,
    }


@app.post("/api/v1/contracts", response_model=ContractResponse)
def api_create_contract(payload: ContractRequest):
    """Submits a new contract draft and validates enterprise BIN."""
    response = process_new_contract(payload, sequence_id=101)
    if not response.is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=response.message,
        )
    return response


@app.post("/api/v1/contracts/transition")
def api_check_transition(payload: StatusTransitionRequest):
    """Validates contract status state machine transition."""
    is_allowed, msg = validate_contract_transition(payload.current_status, payload.new_status)
    return {
        "current_status": payload.current_status,
        "new_status": payload.new_status,
        "allowed": is_allowed,
        "message": msg,
    }


@app.get("/api/v1/stats")
def api_stats():
    """Returns general project telemetry for DORA & academic capacity monitoring."""
    return {
        "faculty": settings.FACULTY_CODE,
        "target_students": settings.TARGET_STUDENTS_COUNT,
        "system_status": "active",
        "modules": [
            "bin_validator",
            "contract_workflow",
            "dean_order_generator",
            "diary_evaluator",
        ],
    }
