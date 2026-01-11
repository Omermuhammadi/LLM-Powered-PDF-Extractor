"""
PDF text extraction service using pdfplumber.

Extracts text content from PDF files with metadata and
detection of scanned (image-based) documents.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pdfplumber

from app.core import EmptyPDFError, PDFExtractionError, ScannedPDFError, logger


@dataclass
class PDFExtractionResult:
    """Result of PDF text extraction."""

    text: str
    metadata: dict[str, Any]
    is_scanned: bool
    pages_processed: int
    char_count: int
    word_count: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "metadata": self.metadata,
            "is_scanned": self.is_scanned,
            "pages_processed": self.pages_processed,
            "char_count": self.char_count,
            "word_count": self.word_count,
        }


def extract_text_from_pdf(
    file_path: str | Path,
    max_pages: int | None = None,
    detect_scanned: bool = True,
) -> PDFExtractionResult:
    """
    Extract text content from a PDF file.

    Args:
        file_path: Path to the PDF file
        max_pages: Maximum number of pages to process (None for all)
        detect_scanned: Whether to detect and raise error for scanned PDFs

    Returns:
        PDFExtractionResult with extracted text and metadata

    Raises:
        PDFExtractionError: If extraction fails
        ScannedPDFError: If PDF appears to be scanned
        EmptyPDFError: If no text could be extracted
    """
    file_path = Path(file_path)
    filename = file_path.name

    logger.processing(filename)

    try:
        with pdfplumber.open(file_path) as pdf:
            # Extract metadata
            metadata = _extract_metadata(pdf, filename)

            # Determine pages to process
            total_pages = len(pdf.pages)
            pages_to_process = (
                total_pages if max_pages is None else min(max_pages, total_pages)
            )

            logger.step(1, 3, f"Extracting text from {pages_to_process} page(s)")

            # Extract text from each page
            page_texts: list[str] = []
            total_chars_in_pages = 0
            pages_with_text = 0

            for page in pdf.pages[:pages_to_process]:
                page_text = page.extract_text() or ""
                page_texts.append(page_text)

                char_count = len(page_text.strip())
                total_chars_in_pages += char_count

                if char_count > 0:
                    pages_with_text += 1

            # Combine text from all pages
            full_text = "\n\n".join(page_texts)

            # Detect if scanned
            logger.step(2, 3, "Analyzing document type")
            is_scanned = _detect_scanned_pdf(
                pdf,
                pages_to_process,
                total_chars_in_pages,
                pages_with_text,
            )

            if is_scanned and detect_scanned:
                raise ScannedPDFError(filename)

            # Validate extraction
            logger.step(3, 3, "Validating extraction")
            clean_text = full_text.strip()

            if not clean_text:
                raise EmptyPDFError(filename)

            # Calculate statistics
            char_count = len(clean_text)
            word_count = len(clean_text.split())

            logger.success(
                f"Extracted {word_count} words from {pages_to_process} page(s)"
            )

            return PDFExtractionResult(
                text=clean_text,
                metadata=metadata,
                is_scanned=is_scanned,
                pages_processed=pages_to_process,
                char_count=char_count,
                word_count=word_count,
            )

    except (ScannedPDFError, EmptyPDFError):
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        logger.error(f"PDF extraction failed: {str(e)}")
        raise PDFExtractionError(filename, str(e))


def _extract_metadata(pdf: pdfplumber.PDF, filename: str) -> dict[str, Any]:
    """Extract metadata from PDF."""
    pdf_metadata = pdf.metadata or {}

    return {
        "filename": filename,
        "total_pages": len(pdf.pages),
        "title": pdf_metadata.get("Title", ""),
        "author": pdf_metadata.get("Author", ""),
        "creator": pdf_metadata.get("Creator", ""),
        "producer": pdf_metadata.get("Producer", ""),
        "creation_date": pdf_metadata.get("CreationDate", ""),
        "modification_date": pdf_metadata.get("ModDate", ""),
    }


def _detect_scanned_pdf(
    pdf: pdfplumber.PDF,
    pages_processed: int,
    total_chars: int,
    pages_with_text: int,
) -> bool:
    """
    Detect if PDF is likely a scanned document.

    Uses multiple heuristics:
    1. Very low text-to-page ratio
    2. Presence of large images covering most of the page
    3. No selectable text on majority of pages
    """
    # Heuristic 1: Check text density
    # A typical text page has 2000-4000 characters
    # Scanned PDFs have very little or no extractable text
    avg_chars_per_page = total_chars / max(pages_processed, 1)
    MIN_CHARS_PER_PAGE = 50  # Threshold for considering a page "has text"

    if avg_chars_per_page < MIN_CHARS_PER_PAGE:
        # Very low text - likely scanned
        return True

    # Heuristic 2: Check if majority of pages have text
    text_coverage = pages_with_text / max(pages_processed, 1)
    if text_coverage < 0.3:  # Less than 30% of pages have text
        return True

    # Heuristic 3: Check for large images on first page
    try:
        first_page = pdf.pages[0]
        images = first_page.images or []

        if images:
            # Check if any image covers significant portion of page
            page_area = first_page.width * first_page.height

            for img in images:
                img_width = img.get("width", 0) or img.get("x1", 0) - img.get("x0", 0)
                img_height = img.get("height", 0) or img.get("y1", 0) - img.get("y0", 0)
                img_area = img_width * img_height

                # If image covers > 80% of page and low text, likely scanned
                if img_area > 0.8 * page_area and avg_chars_per_page < 200:
                    return True
    except Exception:  # nosec B110 - Intentional: fallback to text heuristics
        pass

    return False


def get_text_preview(text: str, max_length: int = 500) -> str:
    """
    Get a preview of the extracted text.

    Args:
        text: Full extracted text
        max_length: Maximum preview length

    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text

    return text[:max_length].rsplit(" ", 1)[0] + "..."
