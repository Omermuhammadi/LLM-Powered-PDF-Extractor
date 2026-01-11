"""
Custom exceptions for the PDF Intelligence Extractor.

Provides structured error handling with error codes and
detailed messages for different failure scenarios.
"""

from typing import Any


class PDFExtractorError(Exception):
    """Base exception for all PDF Extractor errors."""

    def __init__(
        self,
        message: str,
        code: str = "UNKNOWN_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize the exception.

        Args:
            message: Human-readable error message
            code: Error code for programmatic handling
            details: Additional error details
        """
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


# ===========================================
# File Related Exceptions
# ===========================================


class FileError(PDFExtractorError):
    """Base exception for file-related errors."""

    pass


class FileNotFoundError(FileError):
    """Raised when a file cannot be found."""

    def __init__(self, filename: str) -> None:
        super().__init__(
            message=f"File not found: {filename}",
            code="FILE_NOT_FOUND",
            details={"filename": filename},
        )


class InvalidFileTypeError(FileError):
    """Raised when file type is not supported."""

    def __init__(self, filename: str, allowed_types: list[str]) -> None:
        super().__init__(
            message=f"Invalid file type. Allowed: {', '.join(allowed_types)}",
            code="INVALID_FILE_TYPE",
            details={"filename": filename, "allowed_types": allowed_types},
        )


class FileTooLargeError(FileError):
    """Raised when file exceeds size limit."""

    def __init__(self, filename: str, size_mb: float, max_size_mb: int) -> None:
        super().__init__(
            message=f"File too large ({size_mb:.1f}MB). Max: {max_size_mb}MB",
            code="FILE_TOO_LARGE",
            details={
                "filename": filename,
                "size_mb": size_mb,
                "max_size_mb": max_size_mb,
            },
        )


# ===========================================
# PDF Processing Exceptions
# ===========================================


class PDFProcessingError(PDFExtractorError):
    """Base exception for PDF processing errors."""

    pass


class PDFExtractionError(PDFProcessingError):
    """Raised when text extraction from PDF fails."""

    def __init__(self, filename: str, reason: str) -> None:
        super().__init__(
            message=f"Failed to extract text from PDF: {reason}",
            code="PDF_EXTRACTION_FAILED",
            details={"filename": filename, "reason": reason},
        )


class ScannedPDFError(PDFProcessingError):
    """Raised when PDF appears to be scanned (image-based)."""

    def __init__(self, filename: str) -> None:
        super().__init__(
            message="PDF appears to be scanned/image-based. OCR not yet supported",
            code="SCANNED_PDF_NOT_SUPPORTED",
            details={"filename": filename},
        )


class EmptyPDFError(PDFProcessingError):
    """Raised when PDF contains no extractable text."""

    def __init__(self, filename: str) -> None:
        super().__init__(
            message="PDF contains no extractable text",
            code="EMPTY_PDF",
            details={"filename": filename},
        )


# ===========================================
# LLM Related Exceptions
# ===========================================


class LLMError(PDFExtractorError):
    """Base exception for LLM-related errors."""

    pass


class LLMConnectionError(LLMError):
    """Raised when cannot connect to LLM service."""

    def __init__(self, host: str, reason: str) -> None:
        super().__init__(
            message=f"Cannot connect to LLM service at {host}: {reason}",
            code="LLM_CONNECTION_FAILED",
            details={"host": host, "reason": reason},
        )


class LLMTimeoutError(LLMError):
    """Raised when LLM request times out."""

    def __init__(
        self,
        provider: str = "llm",
        timeout_seconds: int = 60,
        elapsed_seconds: float | None = None,
    ) -> None:
        elapsed_info = ""
        if elapsed_seconds is not None:
            elapsed_info = f" (elapsed: {elapsed_seconds:.1f}s)"
        msg = f"LLM request to {provider} timed out after {timeout_seconds}s"
        msg += elapsed_info
        super().__init__(
            message=msg,
            code="LLM_TIMEOUT",
            details={
                "provider": provider,
                "timeout_seconds": timeout_seconds,
                "elapsed_seconds": elapsed_seconds,
            },
        )


class LLMResponseError(LLMError):
    """Raised when LLM returns an invalid response."""

    def __init__(self, reason: str, raw_response: str | None = None) -> None:
        super().__init__(
            message=f"Invalid LLM response: {reason}",
            code="LLM_INVALID_RESPONSE",
            details={"reason": reason, "raw_response": raw_response},
        )


class ModelNotFoundError(LLMError):
    """Raised when specified model is not available."""

    def __init__(self, model_name: str) -> None:
        super().__init__(
            message=f"Model '{model_name}' not found. Run: ollama pull {model_name}",
            code="MODEL_NOT_FOUND",
            details={"model_name": model_name},
        )


# ===========================================
# Extraction & Validation Exceptions
# ===========================================


class ExtractionError(PDFExtractorError):
    """Base exception for extraction errors."""

    pass


class DocumentTypeDetectionError(ExtractionError):
    """Raised when document type cannot be determined."""

    def __init__(self) -> None:
        super().__init__(
            message="Could not determine document type. Supported: invoice, resume",
            code="UNKNOWN_DOCUMENT_TYPE",
        )


class UnsupportedDocumentTypeError(ExtractionError):
    """Raised when document type is not supported."""

    def __init__(self, detected_type: str, supported_types: list[str]) -> None:
        super().__init__(
            message=f"Document type '{detected_type}' is not supported",
            code="UNSUPPORTED_DOCUMENT_TYPE",
            details={
                "detected_type": detected_type,
                "supported_types": supported_types,
            },
        )


class ValidationError(ExtractionError):
    """Raised when extracted data fails validation."""

    def __init__(self, errors: list[dict[str, Any]]) -> None:
        super().__init__(
            message="Extracted data failed validation",
            code="VALIDATION_FAILED",
            details={"errors": errors},
        )


class LowConfidenceError(ExtractionError):
    """Raised when extraction confidence is below threshold."""

    def __init__(self, confidence: float, threshold: float) -> None:
        super().__init__(
            message=f"Confidence ({confidence:.2%}) below threshold ({threshold:.2%})",
            code="LOW_CONFIDENCE",
            details={"confidence": confidence, "threshold": threshold},
        )


class ExtractionParseError(ExtractionError):
    """Raised when parsing LLM extraction response fails."""

    def __init__(self, reason: str, raw_response: str | None = None) -> None:
        super().__init__(
            message=f"Failed to parse extraction response: {reason}",
            code="EXTRACTION_PARSE_ERROR",
            details={
                "reason": reason,
                "raw_response": raw_response[:500] if raw_response else None,
            },
        )
