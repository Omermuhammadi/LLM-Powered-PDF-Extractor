"""
Extraction response schemas.

This module defines the API response schemas for extraction operations,
including extraction results, metadata, and validation summaries.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union

from pydantic import BaseModel, Field

from app.schemas.base import FieldScore, ValidationResult, ValidationSeverity
from app.schemas.invoice import InvoiceData


class DocumentType(str, Enum):
    """Supported document types for extraction."""

    INVOICE = "invoice"
    RESUME = "resume"
    CONTRACT = "contract"
    RECEIPT = "receipt"
    FORM = "form"
    GENERIC = "generic"
    UNKNOWN = "unknown"


class ExtractionStatus(str, Enum):
    """Status of extraction operation."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    PENDING = "pending"
    PROCESSING = "processing"


class ProcessingStage(str, Enum):
    """Stages in the extraction pipeline."""

    UPLOAD = "upload"
    PDF_EXTRACTION = "pdf_extraction"
    TEXT_PROCESSING = "text_processing"
    DOCUMENT_DETECTION = "document_detection"
    LLM_EXTRACTION = "llm_extraction"
    VALIDATION = "validation"
    COMPLETE = "complete"
    UNKNOWN = "unknown"


class ExtractionMetrics(BaseModel):
    """Metrics for extraction performance."""

    pdf_extraction_time: Optional[float] = Field(
        default=None,
        description="Time taken for PDF text extraction in seconds",
    )
    text_processing_time: Optional[float] = Field(
        default=None,
        description="Time taken for text processing in seconds",
    )
    document_detection_time: Optional[float] = Field(
        default=None,
        description="Time taken for document type detection in seconds",
    )
    llm_extraction_time: Optional[float] = Field(
        default=None,
        description="Time taken for LLM extraction in seconds",
    )
    validation_time: Optional[float] = Field(
        default=None,
        description="Time taken for validation in seconds",
    )
    total_time: Optional[float] = Field(
        default=None,
        description="Total extraction time in seconds",
    )
    tokens_used: Optional[int] = Field(
        default=None,
        description="Number of tokens used in LLM call",
    )
    tokens_per_second: Optional[float] = Field(
        default=None,
        description="LLM generation speed in tokens per second",
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "pdf_extraction_time": 0.5,
                "text_processing_time": 0.2,
                "document_detection_time": 0.1,
                "llm_extraction_time": 45.3,
                "validation_time": 0.05,
                "total_time": 46.15,
                "tokens_used": 512,
                "tokens_per_second": 11.3,
            }
        }


class PageInfo(BaseModel):
    """Information about a processed page."""

    page_number: int = Field(
        ...,
        ge=1,
        description="Page number (1-indexed)",
    )
    char_count: int = Field(
        default=0,
        ge=0,
        description="Number of characters extracted from page",
    )
    word_count: int = Field(
        default=0,
        ge=0,
        description="Number of words extracted from page",
    )
    has_tables: bool = Field(
        default=False,
        description="Whether page contains tables",
    )
    has_images: bool = Field(
        default=False,
        description="Whether page contains images",
    )


class DocumentMetadata(BaseModel):
    """Metadata about the processed document."""

    filename: str = Field(
        ...,
        description="Original filename",
    )
    file_size: Optional[int] = Field(
        default=None,
        ge=0,
        description="File size in bytes",
    )
    page_count: int = Field(
        default=1,
        ge=1,
        description="Number of pages in document",
    )
    detected_type: DocumentType = Field(
        default=DocumentType.UNKNOWN,
        description="Detected document type",
    )
    detection_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence of document type detection",
    )
    pages: list[PageInfo] = Field(
        default_factory=list,
        description="Information about each page",
    )
    total_chars: int = Field(
        default=0,
        ge=0,
        description="Total characters in document",
    )
    total_words: int = Field(
        default=0,
        ge=0,
        description="Total words in document",
    )
    language: Optional[str] = Field(
        default=None,
        description="Detected document language",
    )


class ValidationSummary(BaseModel):
    """Summary of validation results."""

    is_valid: bool = Field(
        ...,
        description="Whether the extraction passed validation",
    )
    overall_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall validation score (0-1)",
    )
    field_scores: list[FieldScore] = Field(
        default_factory=list,
        description="Individual field validation scores",
    )
    issues: list[ValidationResult] = Field(
        default_factory=list,
        description="Validation issues found",
    )
    critical_issues: int = Field(
        default=0,
        ge=0,
        description="Number of critical issues",
    )
    warning_issues: int = Field(
        default=0,
        ge=0,
        description="Number of warning issues",
    )
    fields_extracted: int = Field(
        default=0,
        ge=0,
        description="Number of fields successfully extracted",
    )
    fields_expected: int = Field(
        default=0,
        ge=0,
        description="Number of fields expected",
    )

    @property
    def extraction_coverage(self) -> float:
        """Calculate extraction coverage percentage."""
        if self.fields_expected == 0:
            return 0.0
        return self.fields_extracted / self.fields_expected

    def get_issues_by_severity(
        self, severity: ValidationSeverity
    ) -> list[ValidationResult]:
        """Get issues filtered by severity level."""
        return [issue for issue in self.issues if issue.severity == severity]


class ExtractionError(BaseModel):
    """Details about extraction error."""

    code: str = Field(
        ...,
        description="Error code",
    )
    message: str = Field(
        ...,
        description="Human-readable error message",
    )
    stage: ProcessingStage = Field(
        ...,
        description="Stage where error occurred",
    )
    details: Optional[dict[str, Any]] = Field(
        default=None,
        description="Additional error details",
    )
    recoverable: bool = Field(
        default=False,
        description="Whether the error is recoverable",
    )


class ExtractionResponse(BaseModel):
    """
    Complete extraction response schema.

    This is the main response model returned by extraction API endpoints.
    """

    # Request identification
    request_id: str = Field(
        ...,
        description="Unique request identifier",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of extraction",
    )

    # Status information
    status: ExtractionStatus = Field(
        default=ExtractionStatus.PENDING,
        description="Extraction status",
    )
    stage: ProcessingStage = Field(
        default=ProcessingStage.UPLOAD,
        description="Current processing stage",
    )

    # Document information
    document: Optional[DocumentMetadata] = Field(
        default=None,
        description="Document metadata",
    )

    # Extracted data (union of all document types)
    extracted_data: Optional[Union[InvoiceData, dict[str, Any]]] = Field(
        default=None,
        description="Extracted structured data",
    )

    # Raw extraction (before validation)
    raw_extraction: Optional[dict[str, Any]] = Field(
        default=None,
        description="Raw LLM extraction output before processing",
    )

    # Validation results
    validation: Optional[ValidationSummary] = Field(
        default=None,
        description="Validation summary",
    )

    # Performance metrics
    metrics: Optional[ExtractionMetrics] = Field(
        default=None,
        description="Extraction performance metrics",
    )

    # Error information
    error: Optional[ExtractionError] = Field(
        default=None,
        description="Error details if extraction failed",
    )

    # Warnings (non-fatal issues)
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal warnings during extraction",
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "request_id": "req_abc123",
                "timestamp": "2024-01-15T10:30:00Z",
                "status": "success",
                "stage": "complete",
                "document": {
                    "filename": "invoice.pdf",
                    "page_count": 2,
                    "detected_type": "invoice",
                    "detection_confidence": 0.95,
                },
                "extracted_data": {
                    "invoice_number": "INV-2024-001",
                    "total_amount": 1250.00,
                },
                "validation": {
                    "is_valid": True,
                    "overall_score": 0.92,
                    "fields_extracted": 8,
                    "fields_expected": 10,
                },
                "metrics": {
                    "total_time": 45.5,
                    "tokens_per_second": 11.3,
                },
            }
        }

    def is_successful(self) -> bool:
        """Check if extraction was successful."""
        return self.status in (ExtractionStatus.SUCCESS, ExtractionStatus.PARTIAL)

    def has_critical_issues(self) -> bool:
        """Check if there are critical validation issues."""
        return self.validation is not None and self.validation.critical_issues > 0


class BatchExtractionRequest(BaseModel):
    """Request schema for batch extraction."""

    file_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of file IDs to process",
    )
    options: Optional[dict[str, Any]] = Field(
        default=None,
        description="Extraction options",
    )
    priority: int = Field(
        default=0,
        ge=0,
        le=10,
        description="Processing priority (0=lowest, 10=highest)",
    )


class BatchExtractionResponse(BaseModel):
    """Response schema for batch extraction."""

    batch_id: str = Field(
        ...,
        description="Unique batch identifier",
    )
    total_files: int = Field(
        ...,
        ge=1,
        description="Total files in batch",
    )
    processed: int = Field(
        default=0,
        ge=0,
        description="Number of files processed",
    )
    successful: int = Field(
        default=0,
        ge=0,
        description="Number of successful extractions",
    )
    failed: int = Field(
        default=0,
        ge=0,
        description="Number of failed extractions",
    )
    results: list[ExtractionResponse] = Field(
        default_factory=list,
        description="Individual extraction results",
    )
    status: ExtractionStatus = Field(
        default=ExtractionStatus.PENDING,
        description="Overall batch status",
    )
    started_at: Optional[datetime] = Field(
        default=None,
        description="Batch start timestamp",
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Batch completion timestamp",
    )

    @property
    def progress_percentage(self) -> float:
        """Calculate batch processing progress."""
        if self.total_files == 0:
            return 0.0
        return (self.processed / self.total_files) * 100

    @property
    def success_rate(self) -> float:
        """Calculate success rate for completed extractions."""
        if self.processed == 0:
            return 0.0
        return self.successful / self.processed
