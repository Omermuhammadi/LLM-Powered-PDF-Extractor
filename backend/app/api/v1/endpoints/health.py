"""
Health check API endpoints.

This module provides health check endpoints for monitoring
the application status, LLM connectivity, and system resources.
"""

import platform
import time
from datetime import datetime
from typing import Any, Optional

import httpx
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from app.core import settings

router = APIRouter()


class ComponentStatus(BaseModel):
    """Status of a system component."""

    name: str
    status: str  # healthy, degraded, unhealthy
    latency_ms: Optional[float] = None
    message: Optional[str] = None
    details: Optional[dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(description="Overall system status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(description="Application version")
    uptime_seconds: Optional[float] = None
    components: list[ComponentStatus] = Field(default_factory=list)
    system: Optional[dict[str, Any]] = None


class ReadinessResponse(BaseModel):
    """Readiness check response model."""

    ready: bool
    checks: dict[str, bool]
    message: Optional[str] = None


# Track startup time
_startup_time: Optional[float] = None


def get_startup_time() -> float:
    """Get or initialize startup time."""
    global _startup_time
    if _startup_time is None:
        _startup_time = time.time()
    return _startup_time


async def check_ollama_health() -> ComponentStatus:
    """Check Ollama service health."""
    start = time.time()

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.ollama_host}/api/tags")
            latency = (time.time() - start) * 1000

            if response.status_code == 200:
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                has_target_model = any(settings.ollama_model in m for m in models)

                return ComponentStatus(
                    name="ollama",
                    status="healthy" if has_target_model else "degraded",
                    latency_ms=round(latency, 2),
                    message=(
                        f"Model {settings.ollama_model} available"
                        if has_target_model
                        else f"Model {settings.ollama_model} not found"
                    ),
                    details={"available_models": models[:5]},
                )
            else:
                return ComponentStatus(
                    name="ollama",
                    status="unhealthy",
                    latency_ms=round(latency, 2),
                    message=f"Ollama returned status {response.status_code}",
                )

    except httpx.TimeoutException:
        return ComponentStatus(
            name="ollama",
            status="unhealthy",
            message="Ollama connection timeout",
        )
    except httpx.ConnectError:
        return ComponentStatus(
            name="ollama",
            status="unhealthy",
            message=f"Cannot connect to Ollama at {settings.ollama_host}",
        )
    except Exception as e:
        return ComponentStatus(
            name="ollama",
            status="unhealthy",
            message=str(e),
        )


def get_system_info() -> dict[str, Any]:
    """Get system information."""
    import os

    return {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "python_version": platform.python_version(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
    }


@router.get(
    "/",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health status of the API and its dependencies.",
)
async def health_check(
    include_details: bool = False,
) -> HealthResponse:
    """
    Comprehensive health check endpoint.

    Args:
        include_details: Include detailed component status

    Returns:
        HealthResponse with system and component status
    """
    startup_time = get_startup_time()
    uptime = time.time() - startup_time

    components: list[ComponentStatus] = []
    overall_status = "healthy"

    if include_details or settings.debug:
        # Check Ollama if using local LLM
        if settings.llm_mode == "local":
            ollama_status = await check_ollama_health()
            components.append(ollama_status)

            if ollama_status.status == "unhealthy":
                overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        uptime_seconds=round(uptime, 2),
        components=components,
        system=get_system_info() if include_details else None,
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness check",
    description="Check if the service is ready to accept requests.",
)
async def readiness_check() -> ReadinessResponse:
    """
    Readiness probe for container orchestration.

    Checks if all required services are available.
    """
    checks = {
        "api": True,
    }

    # Check LLM availability
    if settings.llm_mode == "local":
        ollama_status = await check_ollama_health()
        checks["llm"] = ollama_status.status in ("healthy", "degraded")
    else:
        checks["llm"] = True  # Cloud LLM assumed available

    all_ready = all(checks.values())

    return ReadinessResponse(
        ready=all_ready,
        checks=checks,
        message="Service ready" if all_ready else "Some components not ready",
    )


@router.get(
    "/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness check",
    description="Simple liveness probe.",
)
async def liveness_check() -> dict[str, str]:
    """
    Liveness probe for container orchestration.

    Simple check that the service is running.
    """
    return {"status": "alive"}


@router.get(
    "/llm",
    response_model=ComponentStatus,
    summary="LLM health check",
    description="Check LLM service status and connectivity.",
)
async def llm_health_check() -> ComponentStatus:
    """
    Detailed LLM health check.

    Returns:
        ComponentStatus with LLM service details
    """
    if settings.llm_mode == "local":
        return await check_ollama_health()
    else:
        # For cloud LLM (Groq), just return configured status
        return ComponentStatus(
            name="llm",
            status="healthy",
            message=f"Cloud LLM configured: {settings.groq_model}",
            details={"mode": "cloud", "provider": "groq"},
        )


@router.get(
    "/info",
    summary="API information",
    description="Get API configuration and capabilities.",
)
async def api_info() -> dict[str, Any]:
    """
    Get API information and capabilities.

    Returns:
        Dictionary with API configuration details
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "api_version": "v1",
        "llm": {
            "mode": settings.llm_mode,
            "model": (
                settings.ollama_model
                if settings.llm_mode == "local"
                else settings.groq_model
            ),
        },
        "limits": {
            "max_upload_size_mb": settings.max_upload_size_mb,
            "supported_formats": settings.allowed_extensions_list,
            "timeout_seconds": settings.llm_timeout,
        },
        "features": {
            "document_types": ["invoice", "resume", "generic"],
            "validation": True,
            "batch_processing": False,  # Future feature
        },
    }
