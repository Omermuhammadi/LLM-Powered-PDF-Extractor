"""API v1 module - Main router configuration."""

from fastapi import APIRouter

from app.api.v1.endpoints import extract_router, health_router

# Create main v1 router
api_router = APIRouter()

# Include sub-routers with prefixes
api_router.include_router(
    health_router,
    prefix="/health",
    tags=["health"],
)

api_router.include_router(
    extract_router,
    prefix="/extract",
    tags=["extraction"],
)

__all__ = ["api_router"]
