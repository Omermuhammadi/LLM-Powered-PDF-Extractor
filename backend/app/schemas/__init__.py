"""
Pydantic schemas module.

This module exports all schema classes for use throughout the application.
"""

from app.schemas.base import (
    BaseExtractedData,
    FieldConfidence,
    FieldScore,
    ValidationResult,
    ValidationSeverity,
    validate_extracted_data,
)
from app.schemas.extraction import (
    BatchExtractionRequest,
    BatchExtractionResponse,
    DocumentMetadata,
    DocumentType,
    ExtractionError,
    ExtractionMetrics,
    ExtractionResponse,
    ExtractionStatus,
    PageInfo,
    ProcessingStage,
    ValidationSummary,
)
from app.schemas.invoice import (
    CustomerInfo,
    Invoice,
    InvoiceData,
    LineItem,
    PaymentInfo,
    VendorInfo,
)

__all__ = [
    # Base schemas
    "BaseExtractedData",
    "FieldConfidence",
    "FieldScore",
    "ValidationResult",
    "ValidationSeverity",
    "validate_extracted_data",
    # Extraction schemas
    "BatchExtractionRequest",
    "BatchExtractionResponse",
    "DocumentMetadata",
    "DocumentType",
    "ExtractionError",
    "ExtractionMetrics",
    "ExtractionResponse",
    "ExtractionStatus",
    "PageInfo",
    "ProcessingStage",
    "ValidationSummary",
    # Invoice schemas
    "CustomerInfo",
    "Invoice",
    "InvoiceData",
    "LineItem",
    "PaymentInfo",
    "VendorInfo",
]
