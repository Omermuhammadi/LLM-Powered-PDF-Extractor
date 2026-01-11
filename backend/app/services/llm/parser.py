"""
LLM response parser for extraction results.

Parses JSON responses from LLM, handles malformed output,
and provides validation and cleaning utilities.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any

from app.core import ExtractionParseError, logger


@dataclass
class ParseResult:
    """Result of parsing LLM response."""

    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    raw_response: str = ""
    error: str | None = None
    was_repaired: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "was_repaired": self.was_repaired,
        }


def parse_llm_response(
    response: str,
    expected_fields: list[str] | None = None,
    strict: bool = False,
) -> ParseResult:
    """
    Parse LLM response as JSON.

    Attempts multiple strategies to extract valid JSON:
    1. Direct JSON parse
    2. Extract JSON from markdown code blocks
    3. Find JSON object in text
    4. Repair common JSON errors

    Args:
        response: Raw LLM response text
        expected_fields: Optional list of fields to validate
        strict: If True, raise exception on parse failure

    Returns:
        ParseResult with parsed data or error

    Raises:
        ExtractionParseError: If strict=True and parsing fails
    """
    if not response or not response.strip():
        error = "Empty response from LLM"
        if strict:
            raise ExtractionParseError(error)
        return ParseResult(success=False, raw_response=response, error=error)

    raw = response.strip()
    was_repaired = False

    # Strategy 1: Direct JSON parse
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            logger.debug("Parsed response directly as JSON")
            return ParseResult(
                success=True,
                data=data,
                raw_response=raw,
            )
    except json.JSONDecodeError:
        pass

    # Strategy 2: Extract from markdown code block
    json_str = _extract_from_code_block(raw)
    if json_str:
        try:
            data = json.loads(json_str)
            if isinstance(data, dict):
                logger.debug("Extracted JSON from code block")
                return ParseResult(
                    success=True,
                    data=data,
                    raw_response=raw,
                )
        except json.JSONDecodeError:
            pass

    # Strategy 3: Find JSON object in text
    json_str = _find_json_object(raw)
    if json_str:
        try:
            data = json.loads(json_str)
            if isinstance(data, dict):
                logger.debug("Found JSON object in text")
                return ParseResult(
                    success=True,
                    data=data,
                    raw_response=raw,
                )
        except json.JSONDecodeError:
            # Try to repair
            repaired = _repair_json(json_str)
            if repaired:
                try:
                    data = json.loads(repaired)
                    if isinstance(data, dict):
                        logger.debug("Repaired and parsed JSON")
                        was_repaired = True
                        return ParseResult(
                            success=True,
                            data=data,
                            raw_response=raw,
                            was_repaired=True,
                        )
                except json.JSONDecodeError:
                    pass

    # Strategy 4: Try to repair the entire response
    repaired = _repair_json(raw)
    if repaired:
        try:
            data = json.loads(repaired)
            if isinstance(data, dict):
                logger.debug("Repaired entire response as JSON")
                return ParseResult(
                    success=True,
                    data=data,
                    raw_response=raw,
                    was_repaired=True,
                )
        except json.JSONDecodeError:
            pass

    # All strategies failed
    error = "Failed to parse JSON from LLM response"
    logger.warning(f"{error}: {raw[:200]}...")

    if strict:
        raise ExtractionParseError(error, raw[:500])

    return ParseResult(
        success=False,
        raw_response=raw,
        error=error,
        was_repaired=was_repaired,
    )


def _extract_from_code_block(text: str) -> str | None:
    """Extract JSON from markdown code blocks."""
    # Match ```json ... ``` or ``` ... ```
    patterns = [
        r"```json\s*([\s\S]*?)\s*```",
        r"```\s*([\s\S]*?)\s*```",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return None


def _find_json_object(text: str) -> str | None:
    """Find a JSON object in text by matching braces."""
    # Find first { and last }
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]

    return None


def _repair_json(json_str: str) -> str | None:
    """
    Attempt to repair common JSON errors.

    Handles:
    - Trailing commas
    - Single quotes instead of double quotes
    - Unquoted keys
    - Missing closing braces
    """
    if not json_str:
        return None

    repaired = json_str

    # Remove trailing commas before } or ]
    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)

    # Replace single quotes with double quotes (careful with apostrophes)
    # Only replace if it looks like a JSON string delimiter
    repaired = re.sub(r"'(\w+)':", r'"\1":', repaired)
    repaired = re.sub(r":\s*'([^']*)'", r': "\1"', repaired)

    # Fix unquoted keys
    repaired = re.sub(r"(\{|\,)\s*(\w+)\s*:", r'\1"\2":', repaired)

    # Balance braces
    open_braces = repaired.count("{")
    close_braces = repaired.count("}")
    if open_braces > close_braces:
        repaired += "}" * (open_braces - close_braces)

    open_brackets = repaired.count("[")
    close_brackets = repaired.count("]")
    if open_brackets > close_brackets:
        repaired += "]" * (open_brackets - close_brackets)

    return repaired


def validate_extracted_fields(
    data: dict[str, Any],
    required_fields: list[str],
    document_type: str = "document",
) -> tuple[bool, list[str], list[str]]:
    """
    Validate that required fields are present and not null.

    Args:
        data: Extracted data dictionary
        required_fields: List of required field names
        document_type: Document type for error messages

    Returns:
        Tuple of (is_valid, missing_fields, warnings)
    """
    missing: list[str] = []
    warnings: list[str] = []

    for field_name in required_fields:
        if field_name not in data:
            missing.append(field_name)
        elif data[field_name] is None:
            missing.append(field_name)
            warnings.append(f"Field '{field_name}' is null")
        elif isinstance(data[field_name], str) and not data[field_name].strip():
            warnings.append(f"Field '{field_name}' is empty")

    is_valid = len(missing) == 0

    return is_valid, missing, warnings


def clean_extracted_data(
    data: dict[str, Any],
    document_type: str = "invoice",
) -> dict[str, Any]:
    """
    Clean and normalize extracted data.

    Performs:
    - String trimming
    - Null value standardization
    - Type coercion for known fields

    Args:
        data: Raw extracted data
        document_type: Type of document for field-specific cleaning

    Returns:
        Cleaned data dictionary
    """
    cleaned: dict[str, Any] = {}

    for key, value in data.items():
        # Skip None values
        if value is None:
            cleaned[key] = None
            continue

        # Clean strings
        if isinstance(value, str):
            value = value.strip()
            if not value:
                cleaned[key] = None
                continue
            cleaned[key] = value

        # Clean numbers
        elif isinstance(value, (int, float)):
            cleaned[key] = value

        # Clean lists
        elif isinstance(value, list):
            cleaned[key] = [item for item in value if item is not None and item != ""]

        # Clean nested dicts
        elif isinstance(value, dict):
            cleaned[key] = clean_extracted_data(value, document_type)

        else:
            cleaned[key] = value

    # Type coercion for invoice fields
    if document_type == "invoice":
        for amount_field in ["total_amount", "tax_amount", "subtotal"]:
            if amount_field in cleaned and cleaned[amount_field] is not None:
                try:
                    val = cleaned[amount_field]
                    if isinstance(val, str):
                        # Remove currency symbols and commas
                        val = re.sub(r"[,$€£]", "", val)
                        cleaned[amount_field] = float(val)
                except (ValueError, TypeError):
                    pass

    return cleaned
