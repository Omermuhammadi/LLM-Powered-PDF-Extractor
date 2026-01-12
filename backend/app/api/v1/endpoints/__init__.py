"""API v1 endpoints."""

from app.api.v1.endpoints.batch import router as batch_router
from app.api.v1.endpoints.extract import router as extract_router
from app.api.v1.endpoints.health import router as health_router

__all__ = ["extract_router", "health_router", "batch_router"]
