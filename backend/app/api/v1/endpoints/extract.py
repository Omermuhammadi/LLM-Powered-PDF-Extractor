"""
PDF Extraction API endpoint.

This module provides the main extraction endpoint for processing PDFs
and extracting structured data using the LLM-powered extraction pipeline.
"""

import asyncio
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.core import logger, settings
from app.core.exceptions import PDFExtractorError
from app.schemas.extraction import (
    DocumentMetadata,
    DocumentType,
    ExtractionMetrics,
    ExtractionResponse,
    ExtractionStatus,
    ProcessingStage,
    ValidationSummary,
)
from app.schemas.invoice import InvoiceData
from app.services.extraction import ExtractionOrchestrator, validate_extraction

router = APIRouter()

# Allowed file extensions
ALLOWED_EXTENSIONS = {".pdf"}

# Maximum file size in bytes (from settings)
MAX_FILE_SIZE = settings.max_upload_size_mb * 1024 * 1024


def validate_file(file: UploadFile) -> None:
    """
    Validate uploaded file.

    Args:
        file: The uploaded file to validate.

    Raises:
        HTTPException: If file is invalid.
    """
    # Check filename
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    # Check extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        allowed_str = ", ".join(ALLOWED_EXTENSIONS)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{ext}'. Allowed types: {allowed_str}",
        )

    # Check content type
    if file.content_type not in ["application/pdf", "application/octet-stream"]:
        logger.warning(f"Unexpected content type: {file.content_type}")


async def save_temp_file(file: UploadFile) -> Path:
    """
    Save uploaded file to temporary location.

    Args:
        file: The uploaded file.

    Returns:
        Path to the saved temporary file.
    """
    # Create temp directory if it doesn't exist
    temp_dir = Path(settings.temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    unique_id = uuid.uuid4().hex[:8]
    safe_filename = f"{unique_id}_{Path(file.filename or 'upload').stem}.pdf"
    temp_path = temp_dir / safe_filename

    # Read file content
    content = await file.read()

    # Check file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.max_upload_size_mb}MB",
        )

    # Write to temp file
    temp_path.write_bytes(content)

    return temp_path


def cleanup_temp_file(path: Path) -> None:
    """
    Remove temporary file.

    Args:
        path: Path to the temporary file.
    """
    try:
        if path.exists():
            path.unlink()
    except Exception as e:
        logger.warning(f"Failed to cleanup temp file {path}: {e}")


@router.post(
    "/",
    response_model=ExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract data from PDF",
    description=(
        "Upload a PDF file and extract structured data using LLM-powered extraction. "
        "Supports invoices and other document types."
    ),
    responses={
        200: {
            "description": "Extraction successful",
            "content": {
                "application/json": {
                    "example": {
                        "request_id": "req_abc123",
                        "status": "success",
                        "document": {
                            "filename": "invoice.pdf",
                            "detected_type": "invoice",
                        },
                        "extracted_data": {"invoice_number": "INV-001"},
                    }
                }
            },
        },
        400: {"description": "Invalid file or request"},
        413: {"description": "File too large"},
        422: {"description": "Extraction failed"},
        500: {"description": "Server error"},
    },
)
async def extract_from_pdf(
    file: UploadFile = File(
        ...,
        description="PDF file to process",
    ),
    document_type: Optional[str] = Form(
        default=None,
        description="Document type hint (invoice, resume, etc.)",
    ),
    validate_output: bool = Form(
        default=True,
        description="Whether to validate extracted data",
    ),
    include_raw_text: bool = Form(
        default=False,
        description="Include raw text preview in response",
    ),
) -> ExtractionResponse:
    """
    Extract structured data from an uploaded PDF file.

    This endpoint:
    1. Validates and saves the uploaded PDF
    2. Extracts text from the PDF
    3. Detects document type (if not specified)
    4. Uses LLM to extract structured fields
    5. Validates the extracted data
    6. Returns structured JSON response

    Args:
        file: The PDF file to process
        document_type: Optional hint for document type
        validate_output: Whether to run validation on extracted data
        include_raw_text: Whether to include raw text preview

    Returns:
        ExtractionResponse with extracted data and metadata
    """
    request_id = f"req_{uuid.uuid4().hex[:12]}"
    start_time = time.time()
    temp_path: Optional[Path] = None

    logger.info(f"[{request_id}] Starting extraction for: {file.filename}")

    try:
        # Validate file
        validate_file(file)

        # Save to temp location
        temp_path = await save_temp_file(file)
        logger.debug(f"[{request_id}] Saved temp file: {temp_path}")

        # Initialize orchestrator
        orchestrator = ExtractionOrchestrator(settings)

        # Run extraction
        result = await orchestrator.extract_from_pdf(
            pdf_path=temp_path,
            document_type_hint=document_type,
        )

        # Calculate metrics
        total_time = time.time() - start_time

        # Build response
        if result.success:
            # Create document metadata
            doc_metadata = DocumentMetadata(
                filename=file.filename or "unknown.pdf",
                file_size=temp_path.stat().st_size if temp_path else None,
                page_count=result.metadata.page_count if result.metadata else 1,
                detected_type=DocumentType(result.document_type or "unknown"),
                detection_confidence=(
                    result.metadata.detection_confidence if result.metadata else 0.0
                ),
                total_chars=result.metadata.total_chars if result.metadata else 0,
                total_words=result.metadata.total_words if result.metadata else 0,
            )

            # Create metrics
            metrics = ExtractionMetrics(
                pdf_extraction_time=(
                    result.metadata.pdf_extraction_time if result.metadata else None
                ),
                text_processing_time=(
                    result.metadata.text_processing_time if result.metadata else None
                ),
                document_detection_time=(
                    result.metadata.detection_time if result.metadata else None
                ),
                llm_extraction_time=(
                    result.metadata.llm_extraction_time if result.metadata else None
                ),
                total_time=total_time,
                tokens_used=(
                    result.metadata.tokens_generated if result.metadata else None
                ),
                tokens_per_second=(
                    result.metadata.tokens_per_second if result.metadata else None
                ),
            )

            # Validate extracted data if requested
            validation: Optional[ValidationSummary] = None
            if validate_output and result.extracted_data:
                try:
                    # Convert to InvoiceData if it's an invoice
                    if result.document_type == "invoice" and isinstance(
                        result.extracted_data, dict
                    ):
                        invoice_data = InvoiceData(**result.extracted_data)
                        validation_result = validate_extraction(invoice_data)
                        validation = ValidationSummary(
                            is_valid=validation_result.is_valid,
                            overall_score=validation_result.overall_score,
                            field_scores=validation_result.field_scores,
                            issues=validation_result.issues,
                            critical_issues=validation_result.critical_issues,
                            warning_issues=validation_result.warning_issues,
                            fields_extracted=validation_result.fields_extracted,
                            fields_expected=validation_result.fields_expected,
                        )
                except Exception as e:
                    logger.warning(f"[{request_id}] Validation failed: {e}")
                    validation = ValidationSummary(
                        is_valid=False,
                        overall_score=0.0,
                        critical_issues=1,
                    )

            response = ExtractionResponse(
                request_id=request_id,
                timestamp=datetime.utcnow(),
                status=ExtractionStatus.SUCCESS,
                stage=ProcessingStage.COMPLETE,
                document=doc_metadata,
                extracted_data=result.extracted_data,
                raw_extraction=result.extracted_data if include_raw_text else None,
                validation=validation,
                metrics=metrics,
                warnings=result.warnings if hasattr(result, "warnings") else [],
            )

            field_count = len(result.extracted_data) if result.extracted_data else 0
            logger.info(
                f"[{request_id}] Extraction complete in {total_time:.2f}s - "
                f"Type: {result.document_type}, Fields: {field_count}"
            )

            return response

        else:
            # Extraction failed
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "request_id": request_id,
                    "error": result.error or "Extraction failed",
                    "stage": "extraction",
                },
            )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except PDFExtractorError as e:
        logger.error(f"[{request_id}] PDF extraction error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "request_id": request_id,
                "error": e.message,
                "code": e.code,
            },
        )

    except asyncio.TimeoutError:
        logger.error(f"[{request_id}] Extraction timed out")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={
                "request_id": request_id,
                "error": "Extraction timed out",
                "code": "TIMEOUT",
            },
        )

    except Exception as e:
        logger.exception(f"[{request_id}] Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "request_id": request_id,
                "error": str(e) if settings.debug else "Internal server error",
            },
        )

    finally:
        # Cleanup temp file
        if temp_path:
            cleanup_temp_file(temp_path)


@router.post(
    "/text",
    response_model=dict,
    summary="Extract text only from PDF",
    description="Extract raw text from a PDF without LLM processing.",
)
async def extract_text_only(
    file: UploadFile = File(..., description="PDF file to process"),
    max_pages: int = Form(default=10, ge=1, le=100, description="Max pages to process"),
) -> dict[str, Any]:
    """
    Extract raw text from PDF without LLM processing.

    Useful for debugging or previewing PDF content.
    """
    request_id = f"req_{uuid.uuid4().hex[:12]}"
    temp_path: Optional[Path] = None

    try:
        validate_file(file)
        temp_path = await save_temp_file(file)

        # Import PDF extractor
        from app.services.pdf import PDFExtractor

        extractor = PDFExtractor()
        result = extractor.extract(temp_path)

        return {
            "request_id": request_id,
            "filename": file.filename,
            "success": result.success,
            "page_count": result.page_count,
            "total_chars": len(result.text) if result.text else 0,
            "text_preview": result.text[:2000] if result.text else None,
            "is_scanned": result.is_scanned,
            "metadata": result.metadata,
        }

    except Exception as e:
        logger.error(f"[{request_id}] Text extraction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    finally:
        if temp_path:
            cleanup_temp_file(temp_path)


# ===========================================
# Helper Functions for Building Responses
# ===========================================


def build_error_response(
    request_id: str,
    error_message: str,
    stage: str = "unknown",
    code: str = "EXTRACTION_ERROR",
) -> ExtractionResponse:
    """
    Build a standardized error response.

    Args:
        request_id: Unique request identifier
        error_message: Human-readable error message
        stage: Processing stage where error occurred
        code: Error code for programmatic handling

    Returns:
        ExtractionResponse with error status
    """
    from datetime import datetime

    # Map stage string to enum value
    stage_map = {s.value: s for s in ProcessingStage}
    processing_stage = stage_map.get(stage, ProcessingStage.UNKNOWN)

    return ExtractionResponse(
        request_id=request_id,
        timestamp=datetime.utcnow(),
        status=ExtractionStatus.FAILED,
        stage=processing_stage,
        error={
            "code": code,
            "message": error_message,
            "stage": stage,
        },
    )


def build_success_response(
    request_id: str,
    document_type: str,
    extracted_data: dict,
    processing_time: float,
    file_path: Optional[Path] = None,
    original_filename: str = "unknown.pdf",
    validation: Optional[ValidationSummary] = None,
) -> ExtractionResponse:
    """
    Build a standardized success response.

    Args:
        request_id: Unique request identifier
        document_type: Detected document type
        extracted_data: Dictionary of extracted fields
        processing_time: Total processing time in seconds
        file_path: Path to the processed file
        original_filename: Original filename
        validation: Optional validation summary

    Returns:
        ExtractionResponse with success status
    """
    from datetime import datetime

    # Build document metadata
    doc_type_map = {d.value: d for d in DocumentType}
    detected_type = doc_type_map.get(document_type, DocumentType.UNKNOWN)

    doc_metadata = DocumentMetadata(
        filename=original_filename,
        file_size=(
            file_path.stat().st_size if file_path and file_path.exists() else None
        ),
        page_count=1,
        detected_type=detected_type,
        detection_confidence=0.9,
    )

    # Build metrics
    metrics = ExtractionMetrics(
        total_time=processing_time,
    )

    return ExtractionResponse(
        request_id=request_id,
        timestamp=datetime.utcnow(),
        status=ExtractionStatus.SUCCESS,
        stage=ProcessingStage.COMPLETE,
        document=doc_metadata,
        extracted_data=extracted_data,
        validation=validation,
        metrics=metrics,
    )
