"""
Core module - Configuration, logging, and exception handling.

This module provides the foundational components for the PDF Intelligence Extractor:
- Settings management via Pydantic
- Rich-based logging
- Custom exception hierarchy
"""

from app.core.config import Settings, get_settings, settings
from app.core.exceptions import (
    DocumentTypeDetectionError,
    EmptyPDFError,
    ExtractionError,
    FileError,
    FileTooLargeError,
    InvalidFileTypeError,
    LLMConnectionError,
    LLMError,
    LLMResponseError,
    LLMTimeoutError,
    LowConfidenceError,
    ModelNotFoundError,
    PDFExtractionError,
    PDFExtractorError,
    PDFProcessingError,
    ScannedPDFError,
    UnsupportedDocumentTypeError,
    ValidationError,
)
from app.core.logger import console, get_logger, log_startup_info, logger

__all__ = [
    # Config
    "Settings",
    "settings",
    "get_settings",
    # Logger
    "logger",
    "get_logger",
    "console",
    "log_startup_info",
    # Exceptions
    "PDFExtractorError",
    "FileError",
    "InvalidFileTypeError",
    "FileTooLargeError",
    "PDFProcessingError",
    "PDFExtractionError",
    "ScannedPDFError",
    "EmptyPDFError",
    "LLMError",
    "LLMConnectionError",
    "LLMTimeoutError",
    "LLMResponseError",
    "ModelNotFoundError",
    "ExtractionError",
    "DocumentTypeDetectionError",
    "UnsupportedDocumentTypeError",
    "ValidationError",
    "LowConfidenceError",
]
