"""
Document type detection service.

Detects document types (Invoice, Resume, etc.) from extracted text
using keyword matching and pattern recognition with confidence scoring.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.core import logger


class DocumentType(str, Enum):
    """Supported document types."""

    INVOICE = "invoice"
    RESUME = "resume"
    UNKNOWN = "unknown"


@dataclass
class DetectionResult:
    """Result of document type detection."""

    document_type: DocumentType
    confidence: float
    matched_keywords: list[str]
    matched_patterns: list[str]
    scores: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "document_type": self.document_type.value,
            "confidence": round(self.confidence, 3),
            "matched_keywords": self.matched_keywords,
            "matched_patterns": self.matched_patterns,
            "scores": {k: round(v, 3) for k, v in self.scores.items()},
        }


# =============================================================================
# Detection Configuration
# =============================================================================

# Keywords with weights for each document type
INVOICE_KEYWORDS: dict[str, float] = {
    # High-weight keywords (very specific to invoices)
    "invoice": 3.0,
    "invoice number": 3.0,
    "invoice #": 3.0,
    "inv-": 2.5,
    "invoice date": 2.5,
    "due date": 2.0,
    "payment terms": 2.0,
    "bill to": 2.5,
    "ship to": 1.5,
    "purchase order": 2.0,
    "po number": 2.0,
    "po #": 2.0,
    # Medium-weight keywords
    "subtotal": 2.0,
    "total amount": 2.0,
    "grand total": 2.0,
    "balance due": 2.5,
    "amount due": 2.5,
    "tax": 1.5,
    "vat": 1.5,
    "gst": 1.5,
    "discount": 1.0,
    "shipping": 1.0,
    # Lower-weight keywords (common but not exclusive)
    "quantity": 1.0,
    "qty": 1.0,
    "unit price": 1.5,
    "rate": 0.8,
    "description": 0.5,
    "item": 0.5,
    "payment": 1.0,
    "remit": 1.5,
    "vendor": 1.5,
    "supplier": 1.5,
}

RESUME_KEYWORDS: dict[str, float] = {
    # High-weight keywords (very specific to resumes)
    "resume": 3.5,
    "curriculum vitae": 3.5,
    "cv": 2.5,
    "career objective": 3.0,
    "professional summary": 3.0,
    "work experience": 3.5,
    "professional experience": 3.5,
    "employment history": 3.0,
    "work history": 3.0,
    # Medium-weight keywords
    "education": 2.5,
    "skills": 2.5,
    "technical skills": 3.0,
    "core competencies": 2.5,
    "key skills": 2.5,
    "certifications": 2.5,
    "certificates": 2.0,
    "qualifications": 2.0,
    "references": 2.0,
    "references available": 2.5,
    "achievements": 2.0,
    "accomplishments": 2.0,
    "projects": 2.0,
    "personal projects": 2.5,
    # Education-specific
    "bachelor": 2.0,
    "master": 2.0,
    "degree": 2.0,
    "university": 1.5,
    "college": 1.5,
    "gpa": 2.0,
    "cgpa": 2.0,
    "graduated": 1.5,
    "graduation": 1.5,
    # Experience-specific
    "proficient": 1.5,
    "experienced in": 2.0,
    "responsible for": 1.5,
    "years of experience": 2.5,
    "yrs experience": 2.5,
    # Contact patterns (common in resumes)
    "linkedin": 2.5,
    "github": 2.0,
    "portfolio": 2.0,
    # Language skills
    "languages": 1.5,
    "fluent": 1.5,
    "native speaker": 2.0,
    # Job-hunting phrases
    "seeking position": 2.5,
    "looking for opportunities": 2.5,
    "career goals": 2.0,
}

# Regex patterns for each document type
INVOICE_PATTERNS: list[tuple[str, float]] = [
    # Invoice number patterns
    (r"inv(?:oice)?[\s\-#:]*(?:no\.?|number)?[\s\-#:]*[A-Z0-9\-]+", 2.5),
    (r"#\s*\d{4,}", 1.0),
    # Date patterns with invoice context
    (r"(?:invoice|due|payment)\s*date\s*[:\-]?\s*\d", 2.0),
    # Currency amounts
    (r"\$[\d,]+\.?\d*", 1.5),
    (r"(?:USD|EUR|GBP|CAD)\s*[\d,]+\.?\d*", 1.5),
    # Line items (qty x price pattern)
    (r"\d+\s*(?:x|@)\s*\$?[\d,]+\.?\d*", 1.5),
    # Total patterns
    (r"(?:sub)?total\s*[:\-]?\s*\$?[\d,]+\.?\d*", 2.0),
    # Tax patterns
    (r"tax\s*\(?[\d.]+%?\)?", 1.5),
]

RESUME_PATTERNS: list[tuple[str, float]] = [
    # Email pattern (common in resumes)
    (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", 1.5),
    # Phone patterns
    (r"(?:\+\d{1,3}[\s\-]?)?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}", 1.0),
    # LinkedIn URL
    (r"linkedin\.com/in/[\w\-]+", 2.0),
    # GitHub URL
    (r"github\.com/[\w\-]+", 1.5),
    # Year ranges (employment/education periods)
    (r"(?:19|20)\d{2}\s*[-–]\s*(?:(?:19|20)\d{2}|present|current)", 2.0),
    # Degree patterns
    (r"(?:B\.?S\.?|B\.?A\.?|M\.?S\.?|M\.?A\.?|Ph\.?D\.?|MBA)", 2.0),
    # GPA pattern
    (r"GPA\s*[:\-]?\s*[0-4]\.\d+", 2.0),
]


def detect_document_type(
    text: str,
    min_confidence: float = 0.3,
) -> DetectionResult:
    """
    Detect the type of document from extracted text.

    Uses keyword matching and pattern recognition to classify
    documents with confidence scoring.

    Args:
        text: Extracted text from PDF
        min_confidence: Minimum confidence to return a type (default 0.3)

    Returns:
        DetectionResult with document type, confidence, and details
    """
    logger.processing("document type detection")

    text_lower = text.lower()

    # Calculate scores for each document type
    logger.step(1, 3, "Analyzing keywords")
    invoice_score, invoice_keywords = _calculate_keyword_score(
        text_lower, INVOICE_KEYWORDS
    )
    resume_score, resume_keywords = _calculate_keyword_score(
        text_lower, RESUME_KEYWORDS
    )

    logger.step(2, 3, "Matching patterns")
    invoice_pattern_score, invoice_patterns = _calculate_pattern_score(
        text, INVOICE_PATTERNS
    )
    resume_pattern_score, resume_patterns = _calculate_pattern_score(
        text, RESUME_PATTERNS
    )

    # Combine scores (keywords weighted 60%, patterns 40%)
    invoice_total = (invoice_score * 0.6) + (invoice_pattern_score * 0.4)
    resume_total = (resume_score * 0.6) + (resume_pattern_score * 0.4)

    logger.step(3, 3, "Determining document type")

    # Normalize to confidence (0-1 scale)
    max_possible = 15.0  # Approximate max weighted score
    invoice_confidence = min(1.0, invoice_total / max_possible)
    resume_confidence = min(1.0, resume_total / max_possible)

    scores = {
        "invoice": invoice_confidence,
        "resume": resume_confidence,
    }

    # Determine winner
    if invoice_confidence >= resume_confidence and invoice_confidence >= min_confidence:
        doc_type = DocumentType.INVOICE
        confidence = invoice_confidence
        matched_keywords = invoice_keywords
        matched_patterns = invoice_patterns
    elif resume_confidence > invoice_confidence and resume_confidence >= min_confidence:
        doc_type = DocumentType.RESUME
        confidence = resume_confidence
        matched_keywords = resume_keywords
        matched_patterns = resume_patterns
    else:
        doc_type = DocumentType.UNKNOWN
        confidence = max(invoice_confidence, resume_confidence)
        matched_keywords = []
        matched_patterns = []

    result = DetectionResult(
        document_type=doc_type,
        confidence=confidence,
        matched_keywords=matched_keywords[:10],  # Limit to top 10
        matched_patterns=matched_patterns[:5],  # Limit to top 5
        scores=scores,
    )

    logger.success(f"Detected: {doc_type.value.upper()} (confidence: {confidence:.1%})")

    return result


def _calculate_keyword_score(
    text: str,
    keywords: dict[str, float],
) -> tuple[float, list[str]]:
    """
    Calculate weighted keyword score for text.

    Args:
        text: Lowercase text to analyze
        keywords: Dict of keyword -> weight

    Returns:
        Tuple of (total_score, matched_keywords)
    """
    total_score = 0.0
    matched: list[str] = []

    for keyword, weight in keywords.items():
        # Count occurrences (with diminishing returns)
        count = text.count(keyword.lower())
        if count > 0:
            # First occurrence gets full weight, subsequent get 50%
            score = weight + (weight * 0.5 * min(count - 1, 3))
            total_score += score
            matched.append(keyword)

    return total_score, matched


def _calculate_pattern_score(
    text: str,
    patterns: list[tuple[str, float]],
) -> tuple[float, list[str]]:
    """
    Calculate weighted pattern score for text.

    Args:
        text: Text to analyze (original case)
        patterns: List of (regex_pattern, weight) tuples

    Returns:
        Tuple of (total_score, matched_pattern_descriptions)
    """
    total_score = 0.0
    matched: list[str] = []

    for pattern, weight in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            # Score based on number of matches (with cap)
            count = min(len(matches), 5)
            score = weight * (1 + (count - 1) * 0.3)
            total_score += score
            # Add first match as example
            matched.append(matches[0][:50])

    return total_score, matched


def is_invoice(text: str, min_confidence: float = 0.5) -> bool:
    """Quick check if text is likely an invoice."""
    result = detect_document_type(text, min_confidence=0.0)
    return (
        result.document_type == DocumentType.INVOICE
        and result.confidence >= min_confidence
    )


def is_resume(text: str, min_confidence: float = 0.5) -> bool:
    """Quick check if text is likely a resume."""
    result = detect_document_type(text, min_confidence=0.0)
    return (
        result.document_type == DocumentType.RESUME
        and result.confidence >= min_confidence
    )
