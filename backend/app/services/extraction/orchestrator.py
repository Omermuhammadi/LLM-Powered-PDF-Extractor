"""
Extraction orchestrator - Full PDF extraction pipeline.

Coordinates PDF extraction, text processing, document detection,
LLM extraction, and validation into a unified pipeline.
"""

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.core import ExtractionError, logger
from app.core.config import get_settings
from app.services.extraction.post_processor import post_process_invoice
from app.services.llm import LLMClient, get_llm_client
from app.services.llm.parser import (
    clean_extracted_data,
    parse_llm_response,
    validate_extracted_fields,
)
from app.services.llm.prompts import format_extraction_prompt
from app.services.pdf import (
    DetectionResult,
    DocumentType,
    detect_document_type,
    extract_text_from_pdf,
    get_text_preview,
    process_text,
)


@dataclass
class ExtractionMetadata:
    """Metadata about the extraction process."""

    file_name: str
    file_path: str
    pages_processed: int
    is_scanned: bool
    processing_time_ms: float
    model_used: str
    document_type: str
    detection_confidence: float
    llm_duration_ms: float
    was_json_repaired: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "file_name": self.file_name,
            "pages_processed": self.pages_processed,
            "is_scanned": self.is_scanned,
            "processing_time_ms": round(self.processing_time_ms, 2),
            "model_used": self.model_used,
            "document_type": self.document_type,
            "detection_confidence": round(self.detection_confidence, 3),
            "llm_duration_ms": round(self.llm_duration_ms, 2),
            "was_json_repaired": self.was_json_repaired,
        }


@dataclass
class ExtractionResult:
    """Complete result of document extraction."""

    success: bool
    document_type: str
    extracted_fields: dict[str, Any] = field(default_factory=dict)
    missing_fields: list[str] = field(default_factory=list)
    confidence_scores: dict[str, float] = field(default_factory=dict)
    processing_metadata: ExtractionMetadata | None = None
    raw_text_preview: str = ""
    warnings: list[str] = field(default_factory=list)
    error: dict[str, str] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to API response format."""
        result: dict[str, Any] = {
            "success": self.success,
            "document_type": self.document_type,
        }

        if self.success:
            result.update(
                {
                    "processing_metadata": (
                        self.processing_metadata.to_dict()
                        if self.processing_metadata
                        else None
                    ),
                    "extracted_fields": self.extracted_fields,
                    "missing_fields": self.missing_fields,
                    "confidence_scores": self.confidence_scores,
                    "raw_text_preview": self.raw_text_preview,
                    "warnings": self.warnings,
                }
            )
        else:
            result["error"] = self.error

        return result


# Required fields for each document type
REQUIRED_FIELDS: dict[str, list[str]] = {
    "invoice": ["vendor_name", "invoice_number", "invoice_date", "total_amount"],
    "resume": ["candidate_name", "email", "phone"],
    "unknown": [],
}


class ExtractionOrchestrator:
    """
    Orchestrates the full PDF extraction pipeline.

    Pipeline stages:
    1. PDF text extraction
    2. Text cleaning and processing
    3. Document type detection
    4. LLM-based field extraction
    5. Response parsing and validation
    6. Confidence scoring
    """

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        max_retries: int | None = None,
    ):
        """
        Initialize the orchestrator.

        Args:
            llm_client: Optional LLM client (uses singleton if not provided)
            max_retries: Maximum LLM extraction retries
        """
        self._settings = get_settings()
        self._llm = llm_client or get_llm_client()
        # Use configured retries unless explicitly overridden
        self._max_retries = (
            max_retries if max_retries is not None else self._settings.llm_max_retries
        )

    def extract_from_pdf(
        self,
        file_path: str | Path,
        force_type: DocumentType | None = None,
    ) -> ExtractionResult:
        """
        Extract structured data from a PDF file.

        Args:
            file_path: Path to PDF file
            force_type: Optional document type to force (skip detection)

        Returns:
            ExtractionResult with extracted data or error
        """
        start_time = time.time()
        file_path = Path(file_path)
        file_name = file_path.name

        logger.processing(f"extraction pipeline: {file_name}")

        try:
            # Stage 1: Extract text from PDF
            logger.step(1, 5, "Extracting text from PDF")
            pdf_result = extract_text_from_pdf(
                file_path,
                detect_scanned=False,  # Don't raise on scanned
            )

            # Stage 2: Process text
            logger.step(2, 5, "Processing extracted text")
            processed = process_text(
                pdf_result.text,
                max_tokens=self._settings.chunk_size,
            )

            # Stage 3: Detect document type
            logger.step(3, 5, "Detecting document type")
            if force_type:
                detection = DetectionResult(
                    document_type=force_type,
                    confidence=1.0,
                    matched_keywords=[],
                    matched_patterns=[],
                    scores={force_type.value: 1.0},
                )
            else:
                detection = detect_document_type(processed.cleaned_text)

            # Stage 4: LLM extraction
            logger.step(4, 5, "Extracting fields with LLM")
            llm_result, llm_duration = self._extract_with_llm(
                processed.cleaned_text,
                detection.document_type,
            )

            # Stage 5: Validate and score
            logger.step(5, 5, "Validating extraction")
            doc_type_str = detection.document_type.value
            required = REQUIRED_FIELDS.get(doc_type_str, [])

            # Parse response
            parse_result = parse_llm_response(llm_result)

            if not parse_result.success:
                raise ExtractionError(
                    file_name,
                    f"LLM response parsing failed: {parse_result.error}",
                )

            # Clean data
            cleaned_data = clean_extracted_data(parse_result.data, doc_type_str)

            # Post-process for invoices
            if doc_type_str == "invoice":
                post_result = post_process_invoice(cleaned_data)
                cleaned_data = post_result.data
                # Add any post-processing warnings
                if post_result.warnings:
                    logger.warning(f"Post-processing warnings: {post_result.warnings}")

            # Validate
            is_valid, missing, warnings = validate_extracted_fields(
                cleaned_data, required, doc_type_str
            )

            # Calculate confidence scores
            confidence_scores = self._calculate_confidence(
                cleaned_data, required, detection.confidence
            )

            # Build metadata
            elapsed_ms = (time.time() - start_time) * 1000

            metadata = ExtractionMetadata(
                file_name=file_name,
                file_path=str(file_path),
                pages_processed=pdf_result.pages_processed,
                is_scanned=pdf_result.is_scanned,
                processing_time_ms=elapsed_ms,
                model_used=self._llm.provider,
                document_type=doc_type_str,
                detection_confidence=detection.confidence,
                llm_duration_ms=llm_duration,
                was_json_repaired=parse_result.was_repaired,
            )

            logger.success(
                f"Extraction complete: {doc_type_str} "
                f"({len(cleaned_data)} fields, {elapsed_ms:.0f}ms)"
            )

            return ExtractionResult(
                success=True,
                document_type=doc_type_str,
                extracted_fields=cleaned_data,
                missing_fields=missing,
                confidence_scores=confidence_scores,
                processing_metadata=metadata,
                raw_text_preview=get_text_preview(pdf_result.text, 500),
                warnings=warnings,
            )

        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"Extraction failed: {e}")

            return ExtractionResult(
                success=False,
                document_type="unknown",
                error={
                    "code": type(e).__name__,
                    "message": str(e),
                },
            )

    def extract_from_text(
        self,
        text: str,
        file_name: str = "text_input",
        force_type: DocumentType | None = None,
    ) -> ExtractionResult:
        """
        Extract structured data from text directly.

        Args:
            text: Document text
            file_name: Optional name for the text source
            force_type: Optional document type to force

        Returns:
            ExtractionResult with extracted data
        """
        start_time = time.time()

        logger.processing(f"text extraction: {file_name}")

        try:
            # Process text
            processed = process_text(text, max_tokens=self._settings.chunk_size)

            # Detect type
            if force_type:
                detection = DetectionResult(
                    document_type=force_type,
                    confidence=1.0,
                    matched_keywords=[],
                    matched_patterns=[],
                    scores={force_type.value: 1.0},
                )
            else:
                detection = detect_document_type(processed.cleaned_text)

            # Extract with LLM
            llm_result, llm_duration = self._extract_with_llm(
                processed.cleaned_text,
                detection.document_type,
            )

            # Parse and validate
            doc_type_str = detection.document_type.value
            required = REQUIRED_FIELDS.get(doc_type_str, [])

            parse_result = parse_llm_response(llm_result)

            if not parse_result.success:
                raise ExtractionError(
                    file_name,
                    f"LLM parsing failed: {parse_result.error}",
                )

            cleaned_data = clean_extracted_data(parse_result.data, doc_type_str)

            # Post-process for invoices
            if doc_type_str == "invoice":
                post_result = post_process_invoice(cleaned_data)
                cleaned_data = post_result.data

            is_valid, missing, warnings = validate_extracted_fields(
                cleaned_data, required, doc_type_str
            )

            confidence_scores = self._calculate_confidence(
                cleaned_data, required, detection.confidence
            )

            elapsed_ms = (time.time() - start_time) * 1000

            metadata = ExtractionMetadata(
                file_name=file_name,
                file_path="",
                pages_processed=1,
                is_scanned=False,
                processing_time_ms=elapsed_ms,
                model_used=self._llm.provider,
                document_type=doc_type_str,
                detection_confidence=detection.confidence,
                llm_duration_ms=llm_duration,
                was_json_repaired=parse_result.was_repaired,
            )

            logger.success(f"Text extraction complete ({elapsed_ms:.0f}ms)")

            return ExtractionResult(
                success=True,
                document_type=doc_type_str,
                extracted_fields=cleaned_data,
                missing_fields=missing,
                confidence_scores=confidence_scores,
                processing_metadata=metadata,
                raw_text_preview=text[:500] + "..." if len(text) > 500 else text,
                warnings=warnings,
            )

        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return ExtractionResult(
                success=False,
                document_type="unknown",
                error={"code": type(e).__name__, "message": str(e)},
            )

    def _extract_with_llm(
        self,
        text: str,
        doc_type: DocumentType,
    ) -> tuple[str, float]:
        """
        Extract fields using LLM with retry logic.

        Returns:
            Tuple of (llm_response_content, duration_ms)
        """
        system_prompt, user_prompt = format_extraction_prompt(doc_type, text)

        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                response = self._llm.generate_sync(
                    prompt=user_prompt,
                    system=system_prompt,
                    temperature=0.1,
                    max_tokens=self._settings.llm_max_tokens,
                    json_mode=True,
                )

                return response.content, response.duration_ms

            except Exception as e:
                last_error = e
                if attempt < self._max_retries:
                    logger.warning(f"LLM attempt {attempt + 1} failed: {e}")
                    continue

        raise last_error or ExtractionError("unknown", "LLM extraction failed")

    def _calculate_confidence(
        self,
        data: dict[str, Any],
        required_fields: list[str],
        detection_confidence: float,
    ) -> dict[str, float]:
        """
        Calculate confidence scores for extracted fields.

        Scoring factors:
        - Field presence: 1.0 if present and non-null
        - Detection confidence: Affects overall score
        - Data quality: Based on value characteristics
        """
        scores: dict[str, float] = {}

        # Score individual fields
        for field_name in required_fields:
            if field_name in data and data[field_name] is not None:
                value = data[field_name]
                base_score = 0.9

                # Boost for non-empty strings
                if isinstance(value, str) and len(value) > 2:
                    base_score = 0.95

                # Boost for reasonable numbers
                if isinstance(value, (int, float)) and value > 0:
                    base_score = 0.95

                scores[field_name] = base_score
            else:
                scores[field_name] = 0.0

        # Calculate overall confidence
        if scores:
            field_avg = sum(scores.values()) / len(scores)
            # Weight: 70% field extraction, 30% type detection
            overall = (field_avg * 0.7) + (detection_confidence * 0.3)
        else:
            overall = detection_confidence * 0.5

        scores["overall"] = min(1.0, overall)

        return scores


# Convenience function
def extract_document(
    file_path: str | Path,
    force_type: DocumentType | None = None,
) -> ExtractionResult:
    """
    Extract structured data from a PDF document.

    Convenience function that creates an orchestrator and extracts.

    Args:
        file_path: Path to PDF file
        force_type: Optional document type to force

    Returns:
        ExtractionResult with extracted data
    """
    orchestrator = ExtractionOrchestrator()
    return orchestrator.extract_from_pdf(file_path, force_type)
