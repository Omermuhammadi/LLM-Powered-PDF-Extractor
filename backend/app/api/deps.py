"""
FastAPI dependency injection utilities.

Provides reusable dependencies for API endpoints including:
- Service instances (orchestrator, validator)
- Rate limiting
- Common query parameters
- Authentication (future)
"""

import asyncio
from functools import lru_cache
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Query, status

from app.core import logger, settings
from app.services.extraction import ExtractionOrchestrator
from app.services.extraction.validator import ExtractionValidator, ValidationConfig

# ===========================================
# Service Singletons
# ===========================================


@lru_cache
def get_validator_config() -> ValidationConfig:
    """
    Get validation configuration singleton.

    Returns:
        ValidationConfig with default settings
    """
    return ValidationConfig(
        min_confidence_threshold=0.5,
        fail_on_critical=True,
        required_invoice_fields=["invoice_number", "total_amount"],
    )


@lru_cache
def get_validator(
    config: ValidationConfig = Depends(get_validator_config),
) -> ExtractionValidator:
    """
    Get extraction validator singleton.

    Returns:
        ExtractionValidator instance
    """
    return ExtractionValidator(config=config)


# Store orchestrator instance at module level
_orchestrator_instance: Optional[ExtractionOrchestrator] = None
_orchestrator_lock = asyncio.Lock()


async def get_orchestrator() -> ExtractionOrchestrator:
    """
    Get extraction orchestrator singleton (async).

    Creates orchestrator on first call and reuses it.
    This ensures we don't create multiple LLM connections.

    Returns:
        ExtractionOrchestrator instance
    """
    global _orchestrator_instance

    if _orchestrator_instance is None:
        async with _orchestrator_lock:
            # Double-check after acquiring lock
            if _orchestrator_instance is None:
                logger.info("Creating ExtractionOrchestrator singleton")
                _orchestrator_instance = ExtractionOrchestrator()
                # Initialize the orchestrator
                await _orchestrator_instance.initialize()

    return _orchestrator_instance


# ===========================================
# Common Query Parameters
# ===========================================


async def common_extraction_params(
    include_raw_text: bool = Query(
        default=False,
        description="Include raw extracted text in response",
    ),
    include_metadata: bool = Query(
        default=True,
        description="Include document metadata in response",
    ),
    validate_output: bool = Query(
        default=True,
        description="Run validation on extracted data",
    ),
    min_confidence: float = Query(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for extraction",
    ),
) -> dict:
    """
    Common query parameters for extraction endpoints.

    Returns:
        Dict with extraction options
    """
    return {
        "include_raw_text": include_raw_text,
        "include_metadata": include_metadata,
        "validate_output": validate_output,
        "min_confidence": min_confidence,
    }


# Type aliases for dependency injection
ExtractionParams = Annotated[dict, Depends(common_extraction_params)]
Orchestrator = Annotated[ExtractionOrchestrator, Depends(get_orchestrator)]
Validator = Annotated[ExtractionValidator, Depends(get_validator)]


# ===========================================
# Rate Limiting
# ===========================================


class RateLimiter:
    """
    Simple in-memory rate limiter.

    Uses sliding window algorithm for rate limiting.
    For production, consider using Redis-based solution.
    """

    def __init__(self, requests_per_minute: int = 10):
        """Initialize rate limiter."""
        self.requests_per_minute = requests_per_minute
        self.requests: dict[str, list[float]] = {}
        self._lock = asyncio.Lock()

    async def check_rate_limit(self, client_id: str) -> bool:
        """
        Check if client is within rate limit.

        Args:
            client_id: Unique client identifier (IP or API key)

        Returns:
            True if within limit, False if exceeded
        """
        import time

        current_time = time.time()
        window_start = current_time - 60  # 1 minute window

        async with self._lock:
            if client_id not in self.requests:
                self.requests[client_id] = []

            # Remove old requests outside window
            self.requests[client_id] = [
                req_time
                for req_time in self.requests[client_id]
                if req_time > window_start
            ]

            # Check if within limit
            if len(self.requests[client_id]) >= self.requests_per_minute:
                return False

            # Add current request
            self.requests[client_id].append(current_time)
            return True


# Global rate limiter instance
_rate_limiter = RateLimiter(requests_per_minute=settings.api_rate_limit)


async def check_rate_limit(
    client_ip: str = "default",
) -> None:
    """
    Rate limiting dependency.

    Raises HTTPException if rate limit exceeded.
    """
    if not await _rate_limiter.check_rate_limit(client_ip):
        logger.warning(f"Rate limit exceeded for client: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "message": f"Maximum {settings.api_rate_limit} requests per minute",
                "retry_after": 60,
            },
        )


# ===========================================
# File Validation
# ===========================================


def validate_file_extension(filename: str) -> str:
    """
    Validate file has allowed extension.

    Args:
        filename: Original filename

    Returns:
        Lowercase file extension

    Raises:
        HTTPException if extension not allowed
    """
    import os

    ext = os.path.splitext(filename)[1].lower()
    allowed = settings.allowed_extensions_list

    if ext not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid file type",
                "message": f"File type '{ext}' not supported",
                "allowed_types": allowed,
            },
        )

    return ext


def validate_file_size(size: int) -> None:
    """
    Validate file size is within limits.

    Args:
        size: File size in bytes

    Raises:
        HTTPException if file too large
    """
    max_size = settings.max_upload_size_mb * 1024 * 1024

    if size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error": "File too large",
                "message": f"File size exceeds {settings.max_upload_size_mb}MB limit",
                "max_size_bytes": max_size,
                "actual_size_bytes": size,
            },
        )


# ===========================================
# Cleanup
# ===========================================


async def cleanup_orchestrator() -> None:
    """
    Cleanup orchestrator resources.

    Should be called on application shutdown.
    """
    global _orchestrator_instance

    if _orchestrator_instance is not None:
        logger.info("Cleaning up ExtractionOrchestrator")
        # Add any cleanup logic here
        _orchestrator_instance = None
