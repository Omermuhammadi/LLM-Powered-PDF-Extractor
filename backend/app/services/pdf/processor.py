"""
Text processing service for PDF extraction.

Provides text cleaning and chunking utilities optimized for
LLM processing with token-aware text segmentation.
"""

import re
from dataclasses import dataclass, field
from typing import Any

from app.core import logger


@dataclass
class TextQualityMetrics:
    """Metrics for assessing text quality."""

    original_length: int
    cleaned_length: int
    reduction_ratio: float
    line_count: int
    avg_line_length: float
    has_structured_data: bool
    noise_ratio: float  # Ratio of removed characters

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "original_length": self.original_length,
            "cleaned_length": self.cleaned_length,
            "reduction_ratio": round(self.reduction_ratio, 3),
            "line_count": self.line_count,
            "avg_line_length": round(self.avg_line_length, 2),
            "has_structured_data": self.has_structured_data,
            "noise_ratio": round(self.noise_ratio, 3),
        }


@dataclass
class TextChunk:
    """A chunk of text with metadata."""

    content: str
    index: int
    start_char: int
    end_char: int
    estimated_tokens: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "index": self.index,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "estimated_tokens": self.estimated_tokens,
        }


@dataclass
class ProcessedText:
    """Result of text processing."""

    original_text: str
    cleaned_text: str
    chunks: list[TextChunk] = field(default_factory=list)
    quality_metrics: TextQualityMetrics | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "original_text": (
                self.original_text[:500] + "..."
                if len(self.original_text) > 500
                else self.original_text
            ),
            "cleaned_text": (
                self.cleaned_text[:500] + "..."
                if len(self.cleaned_text) > 500
                else self.cleaned_text
            ),
            "chunks": [c.to_dict() for c in self.chunks],
            "quality_metrics": (
                self.quality_metrics.to_dict() if self.quality_metrics else None
            ),
        }


# Token estimation: ~4 characters per token for English text
CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.

    Uses a simple heuristic of ~4 characters per token,
    which is a reasonable approximation for English text.

    Args:
        text: Input text

    Returns:
        Estimated token count
    """
    return max(1, len(text) // CHARS_PER_TOKEN)


def clean_text(
    text: str,
    normalize_whitespace: bool = True,
    remove_headers_footers: bool = True,
    fix_encoding: bool = True,
    remove_page_numbers: bool = True,
) -> tuple[str, TextQualityMetrics]:
    """
    Clean and normalize extracted PDF text.

    Performs multiple cleaning operations:
    - Normalizes whitespace and line breaks
    - Removes common PDF artifacts (headers, footers, page numbers)
    - Fixes encoding issues
    - Removes excessive blank lines

    Args:
        text: Raw extracted text
        normalize_whitespace: Normalize spaces and tabs
        remove_headers_footers: Remove repeated headers/footers
        fix_encoding: Fix common encoding issues
        remove_page_numbers: Remove standalone page numbers

    Returns:
        Tuple of (cleaned_text, quality_metrics)
    """
    original_length = len(text)
    cleaned = text

    logger.step(1, 4, "Normalizing whitespace")

    # Step 1: Fix encoding issues
    if fix_encoding:
        cleaned = _fix_encoding_issues(cleaned)

    # Step 2: Normalize whitespace
    if normalize_whitespace:
        # Replace tabs with spaces
        cleaned = cleaned.replace("\t", " ")
        # Normalize multiple spaces to single space (but preserve newlines)
        cleaned = re.sub(r"[^\S\n]+", " ", cleaned)
        # Normalize line endings
        cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

    logger.step(2, 4, "Removing PDF artifacts")

    # Step 3: Remove page numbers
    if remove_page_numbers:
        cleaned = _remove_page_numbers(cleaned)

    # Step 4: Remove headers/footers
    if remove_headers_footers:
        cleaned = _remove_repeated_patterns(cleaned)

    logger.step(3, 4, "Cleaning line structure")

    # Step 5: Clean up line breaks
    # Remove lines that are just whitespace
    lines = cleaned.split("\n")
    lines = [line.strip() for line in lines]

    # Remove excessive blank lines (more than 2 consecutive)
    cleaned_lines: list[str] = []
    blank_count = 0

    for line in lines:
        if not line:
            blank_count += 1
            if blank_count <= 2:
                cleaned_lines.append(line)
        else:
            blank_count = 0
            cleaned_lines.append(line)

    cleaned = "\n".join(cleaned_lines)

    # Final strip
    cleaned = cleaned.strip()

    logger.step(4, 4, "Calculating quality metrics")

    # Calculate quality metrics
    metrics = _calculate_quality_metrics(text, cleaned)

    logger.success(
        f"Text cleaned: {original_length} → {len(cleaned)} chars "
        f"({metrics.reduction_ratio:.1%} reduction)"
    )

    return cleaned, metrics


def _fix_encoding_issues(text: str) -> str:
    """Fix common PDF encoding issues."""
    # Common ligature replacements
    replacements = {
        "ﬁ": "fi",
        "ﬂ": "fl",
        "ﬀ": "ff",
        "ﬃ": "ffi",
        "ﬄ": "ffl",
        "\ufeff": "",  # BOM
        "\u00a0": " ",  # Non-breaking space
        "\u2018": "'",  # Left single quote
        "\u2019": "'",  # Right single quote
        "\u201c": '"',  # Left double quote
        "\u201d": '"',  # Right double quote
        "\u2013": "-",  # En dash
        "\u2014": "-",  # Em dash
        "\u2026": "...",  # Ellipsis
        "\u00ad": "",  # Soft hyphen
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def _remove_page_numbers(text: str) -> str:
    """Remove standalone page numbers from text."""
    lines = text.split("\n")
    cleaned_lines: list[str] = []

    for line in lines:
        stripped = line.strip()

        # Skip lines that are just page numbers
        # Patterns: "1", "Page 1", "- 1 -", "1 of 10", etc.
        if re.match(r"^(?:page\s*)?\d+(?:\s*(?:of|/)\s*\d+)?$", stripped, re.I):
            continue
        if re.match(r"^[-–—]\s*\d+\s*[-–—]$", stripped):
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def _remove_repeated_patterns(text: str) -> str:
    """
    Remove repeated headers/footers that appear on multiple pages.

    Detects patterns that repeat with similar content across page breaks.
    """
    lines = text.split("\n")

    if len(lines) < 10:
        return text

    # Find potential headers/footers by looking for short repeated lines
    line_counts: dict[str, int] = {}

    for line in lines:
        stripped = line.strip()
        # Only consider short lines as potential headers/footers
        if 3 <= len(stripped) <= 100:
            normalized = stripped.lower()
            line_counts[normalized] = line_counts.get(normalized, 0) + 1

    # Lines that appear 3+ times are likely headers/footers
    repeated_patterns = {
        pattern for pattern, count in line_counts.items() if count >= 3
    }

    if not repeated_patterns:
        return text

    # Remove repeated patterns
    cleaned_lines = [
        line for line in lines if line.strip().lower() not in repeated_patterns
    ]

    return "\n".join(cleaned_lines)


def _calculate_quality_metrics(original: str, cleaned: str) -> TextQualityMetrics:
    """Calculate quality metrics for cleaned text."""
    original_length = len(original)
    cleaned_length = len(cleaned)

    lines = [line for line in cleaned.split("\n") if line.strip()]
    line_count = len(lines)
    avg_line_length = sum(len(line) for line in lines) / max(line_count, 1)

    # Check for structured data indicators
    structured_indicators = [
        r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",  # Dates
        r"\$[\d,]+\.?\d*",  # Currency
        r"\b[A-Z]{2,}-?\d+\b",  # Invoice numbers
        r"total|subtotal|amount|qty|quantity",  # Keywords
    ]
    has_structured = any(
        re.search(pattern, cleaned, re.I) for pattern in structured_indicators
    )

    # Calculate noise ratio
    removed_chars = original_length - cleaned_length
    noise_ratio = removed_chars / max(original_length, 1)

    return TextQualityMetrics(
        original_length=original_length,
        cleaned_length=cleaned_length,
        reduction_ratio=1 - (cleaned_length / max(original_length, 1)),
        line_count=line_count,
        avg_line_length=avg_line_length,
        has_structured_data=has_structured,
        noise_ratio=noise_ratio,
    )


def chunk_text(
    text: str,
    max_tokens: int = 3000,
    overlap_tokens: int = 100,
    preserve_sentences: bool = True,
) -> list[TextChunk]:
    """
    Split text into chunks suitable for LLM processing.

    Creates overlapping chunks to maintain context across boundaries.
    Attempts to break at sentence boundaries when possible.

    Args:
        text: Text to chunk
        max_tokens: Maximum tokens per chunk (~4 chars/token)
        overlap_tokens: Token overlap between chunks
        preserve_sentences: Try to break at sentence boundaries

    Returns:
        List of TextChunk objects
    """
    if not text.strip():
        return []

    max_chars = max_tokens * CHARS_PER_TOKEN
    overlap_chars = overlap_tokens * CHARS_PER_TOKEN

    # If text fits in one chunk, return as-is
    if len(text) <= max_chars:
        return [
            TextChunk(
                content=text,
                index=0,
                start_char=0,
                end_char=len(text),
                estimated_tokens=estimate_tokens(text),
            )
        ]

    logger.step(1, 2, f"Splitting text into chunks (max {max_tokens} tokens each)")

    chunks: list[TextChunk] = []
    start = 0
    chunk_index = 0

    while start < len(text):
        # Calculate end position
        end = min(start + max_chars, len(text))

        # If not at the end, try to break at a sentence boundary
        if end < len(text) and preserve_sentences:
            # Look for sentence endings within the last 20% of the chunk
            search_start = start + int(max_chars * 0.8)
            search_region = text[search_start:end]

            # Find the last sentence boundary
            sentence_end = _find_sentence_boundary(search_region)

            if sentence_end > 0:
                end = search_start + sentence_end

        chunk_content = text[start:end].strip()

        if chunk_content:
            chunks.append(
                TextChunk(
                    content=chunk_content,
                    index=chunk_index,
                    start_char=start,
                    end_char=end,
                    estimated_tokens=estimate_tokens(chunk_content),
                )
            )
            chunk_index += 1

        # Move to next chunk with overlap
        start = end - overlap_chars

        # Ensure we make progress
        if start >= len(text) - overlap_chars:
            break

    logger.step(2, 2, f"Created {len(chunks)} chunk(s)")
    logger.success(f"Text chunked into {len(chunks)} segments")

    return chunks


def _find_sentence_boundary(text: str) -> int:
    """
    Find the best sentence boundary position in text.

    Returns the position after the last sentence-ending punctuation.
    """
    # Look for sentence endings: . ! ? followed by space or end
    matches = list(re.finditer(r"[.!?]+(?:\s|$)", text))

    if matches:
        # Return position after the last match
        return matches[-1].end()

    # Fallback: look for other break points
    # Try newline
    newline_pos = text.rfind("\n")
    if newline_pos > len(text) * 0.5:
        return newline_pos + 1

    # Try comma or semicolon
    for punct in [";", ","]:
        pos = text.rfind(punct)
        if pos > len(text) * 0.7:
            return pos + 1

    return 0


def process_text(
    text: str,
    max_tokens: int = 3000,
    overlap_tokens: int = 100,
) -> ProcessedText:
    """
    Full text processing pipeline: clean and chunk.

    Args:
        text: Raw extracted text
        max_tokens: Maximum tokens per chunk
        overlap_tokens: Overlap between chunks

    Returns:
        ProcessedText with cleaned text, chunks, and metrics
    """
    logger.processing("text processing pipeline")

    # Clean the text
    cleaned_text, quality_metrics = clean_text(text)

    # Chunk the text
    chunks = chunk_text(
        cleaned_text,
        max_tokens=max_tokens,
        overlap_tokens=overlap_tokens,
    )

    return ProcessedText(
        original_text=text,
        cleaned_text=cleaned_text,
        chunks=chunks,
        quality_metrics=quality_metrics,
    )


def assess_extraction_quality(metrics: TextQualityMetrics) -> dict[str, Any]:
    """
    Assess the quality of extracted text for LLM processing.

    Args:
        metrics: Quality metrics from cleaning

    Returns:
        Quality assessment with score and recommendations
    """
    issues: list[str] = []
    score = 100.0

    # Check text length
    if metrics.cleaned_length < 50:
        issues.append("Very short text - may lack sufficient information")
        score -= 30
    elif metrics.cleaned_length < 200:
        issues.append("Short text - extraction may be incomplete")
        score -= 15

    # Check noise ratio
    if metrics.noise_ratio > 0.5:
        issues.append("High noise ratio - possible extraction issues")
        score -= 20
    elif metrics.noise_ratio > 0.3:
        issues.append("Moderate noise ratio - some cleanup was needed")
        score -= 10

    # Check line structure
    if metrics.avg_line_length < 10:
        issues.append("Very short lines - possibly fragmented text")
        score -= 15

    # Bonus for structured data
    if metrics.has_structured_data:
        score = min(100, score + 10)

    return {
        "score": max(0, score),
        "quality": "good" if score >= 70 else "fair" if score >= 50 else "poor",
        "issues": issues,
        "recommendation": (
            "Ready for LLM processing"
            if score >= 70
            else "Review extraction quality before processing"
        ),
    }
