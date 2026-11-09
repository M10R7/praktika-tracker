"""
API package initialization.
"""

from fastapi import APIRouter

from src.api.applications import router as applications_router
from src.api.companies import router as companies_router
from src.api.export import router as export_router
from src.api.orders import router as orders_router
from src.api.stats import router as stats_router
from src.api.tracker import router as tracker_router

api_router = APIRouter()
api_router.include_router(applications_router)
api_router.include_router(companies_router)
api_router.include_router(tracker_router)
api_router.include_router(orders_router)
api_router.include_router(export_router)
api_router.include_router(stats_router)

__all__ = ["api_router"]
