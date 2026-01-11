"""
PDF processing services.

Provides functionality for:
- Text extraction from PDFs
- Document type detection
- Text cleaning and processing
"""

from app.services.pdf.extractor import (
    PDFExtractionResult,
    extract_text_from_pdf,
    get_text_preview,
)
from app.services.pdf.processor import (
    ProcessedText,
    TextChunk,
    TextQualityMetrics,
    assess_extraction_quality,
    chunk_text,
    clean_text,
    estimate_tokens,
    process_text,
)

__all__ = [
    # Extraction
    "PDFExtractionResult",
    "extract_text_from_pdf",
    "get_text_preview",
    # Processing
    "ProcessedText",
    "TextChunk",
    "TextQualityMetrics",
    "clean_text",
    "chunk_text",
    "process_text",
    "estimate_tokens",
    "assess_extraction_quality",
]
