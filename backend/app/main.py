"""
FastAPI application entry point.

PDF Intelligence Extractor - A production-grade system for extracting
structured data from PDFs using local LLMs (Phi-3 Mini via Ollama).
"""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core import PDFExtractorError, console, log_startup_info, logger, settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Handles startup and shutdown events.
    """
    # Startup
    log_startup_info()
    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Application shutting down...")
    console.print("\n[warning]👋 Goodbye![/warning]\n")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description=(
        "LLM-Powered PDF Intelligence Extraction System. "
        "Extract structured data from invoices, resumes, and more."
    ),
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===========================================
# Exception Handlers
# ===========================================


@app.exception_handler(PDFExtractorError)
async def pdf_extractor_exception_handler(
    request: Request,
    exc: PDFExtractorError,
) -> JSONResponse:
    """Handle custom PDF Extractor exceptions."""
    logger.error(f"[{exc.code}] {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "error": exc.to_dict(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {"error": str(exc)} if settings.debug else {},
            },
        },
    )


# ===========================================
# Health Check Endpoints
# ===========================================


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """Root endpoint - API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs" if settings.debug else "disabled",
    }


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, Any]:
    """
    Health check endpoint.

    Returns system status and configuration info.
    """
    return {
        "status": "healthy",
        "version": settings.app_version,
        "llm": {
            "mode": settings.llm_mode,
            "model": (
                settings.ollama_model
                if settings.llm_mode == "local"
                else settings.groq_model
            ),
            "host": (
                settings.ollama_host if settings.llm_mode == "local" else "groq-api"
            ),
        },
        "config": {
            "max_upload_size_mb": settings.max_upload_size_mb,
            "supported_formats": settings.allowed_extensions_list,
        },
    }


@app.get(f"{settings.api_prefix}/health", tags=["Health"])
async def api_health_check() -> dict[str, str]:
    """API v1 health check endpoint."""
    return {
        "status": "healthy",
        "api_version": "v1",
    }


# ===========================================
# API Router Registration (Future Phases)
# ===========================================

# TODO: Phase 9 - Register API routers
# from app.api.v1.endpoints import extract, health
# app.include_router(extract.router, prefix=settings.api_prefix, tags=["Extraction"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
