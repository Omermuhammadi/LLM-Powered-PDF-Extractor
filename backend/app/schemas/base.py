"""
Base schema classes and validation utilities.

Provides common base classes, field confidence enums, and
validation utilities used across all document schemas.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FieldConfidence(str, Enum):
    """Confidence level for extracted field values."""

    HIGH = "high"  # >= 0.8 confidence
    MEDIUM = "medium"  # 0.5-0.8 confidence
    LOW = "low"  # < 0.5 confidence
    UNKNOWN = "unknown"  # Could not determine confidence

    @classmethod
    def from_score(cls, score: float) -> "FieldConfidence":
        """Convert numeric score to confidence level."""
        if score >= 0.8:
            return cls.HIGH
        elif score >= 0.5:
            return cls.MEDIUM
        else:
            return cls.LOW


class ValidationSeverity(str, Enum):
    """Severity level for validation issues."""

    CRITICAL = "critical"  # Must be fixed
    WARNING = "warning"  # Should be reviewed
    INFO = "info"  # Informational only


class BaseExtractedData(BaseModel):
    """
    Base class for all extracted data models.

    Provides common configuration and metadata fields.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="allow",  # Allow extra fields for flexibility
    )

    # Optional metadata fields
    extraction_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall extraction confidence score",
    )
    raw_text_snippet: Optional[str] = Field(
        default=None,
        description="Source text snippet for debugging",
    )

    def get_confidence_level(self) -> FieldConfidence:
        """Get confidence level enum from score."""
        return FieldConfidence.from_score(self.extraction_confidence)


class FieldScore(BaseModel):
    """Confidence score and metadata for a single extracted field."""

    field_name: str = Field(..., description="Name of the field")
    score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1)",
    )
    confidence: FieldConfidence = Field(
        default=FieldConfidence.UNKNOWN,
        description="Confidence level enum",
    )
    extracted_value: Optional[str] = Field(
        default=None,
        description="String representation of extracted value",
    )
    source: str = Field(
        default="extracted",
        description="Source of value: extracted, default, computed",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Any warnings about this field",
    )

    @field_validator("score", mode="after")
    @classmethod
    def update_confidence_from_score(cls, v: float, info) -> float:
        """Auto-update confidence level when score is set."""
        return v


class ValidationResult(BaseModel):
    """Result of validating a single field or constraint."""

    field_name: str = Field(..., description="Field being validated")
    is_valid: bool = Field(..., description="Whether validation passed")
    severity: ValidationSeverity = Field(
        default=ValidationSeverity.INFO,
        description="Severity if validation failed",
    )
    message: str = Field(
        default="",
        description="Validation message",
    )
    suggestion: Optional[str] = Field(
        default=None,
        description="Suggested fix or action",
    )


def parse_date(value: Any) -> Optional[date]:
    """
    Parse various date formats into a date object.

    Supports:
    - YYYY-MM-DD
    - MM/DD/YYYY
    - DD/MM/YYYY
    - Month DD, YYYY
    """
    if value is None:
        return None

    if isinstance(value, date):
        return value

    if isinstance(value, datetime):
        return value.date()

    if not isinstance(value, str):
        return None

    value = value.strip()
    if not value:
        return None

    # Common date formats to try
    formats = [
        "%Y-%m-%d",  # 2024-03-15
        "%m/%d/%Y",  # 03/15/2024
        "%d/%m/%Y",  # 15/03/2024
        "%B %d, %Y",  # March 15, 2024
        "%b %d, %Y",  # Mar 15, 2024
        "%d %B %Y",  # 15 March 2024
        "%d %b %Y",  # 15 Mar 2024
        "%Y/%m/%d",  # 2024/03/15
        "%d-%m-%Y",  # 15-03-2024
        "%m-%d-%Y",  # 03-15-2024
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    return None


def parse_amount(value: Any) -> Optional[float]:
    """
    Parse various amount formats into a float.

    Handles:
    - Plain numbers: 1500.00
    - With currency: $1,500.00, €1.500,00
    - With symbols: 1,500.00 USD
    """
    import re

    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if not isinstance(value, str):
        return None

    value = value.strip()
    if not value:
        return None

    # Remove currency symbols
    value = re.sub(r"[$€£¥₹]", "", value)
    # Remove currency codes
    value = re.sub(r"\b(USD|EUR|GBP|INR|JPY)\b", "", value, flags=re.IGNORECASE)
    value = value.strip()

    # Handle different decimal separators
    if "." in value and "," in value:
        if value.rfind(".") > value.rfind(","):
            value = value.replace(",", "")
        else:
            value = value.replace(".", "").replace(",", ".")
    elif "," in value:
        parts = value.split(",")
        if len(parts) == 2 and len(parts[1]) == 2:
            value = value.replace(",", ".")
        else:
            value = value.replace(",", "")

    try:
        return float(value)
    except ValueError:
        return None


def validate_extracted_data(
    data: BaseExtractedData,
    required_fields: Optional[list[str]] = None,
) -> list[ValidationResult]:
    """
    Validate extracted data against requirements.

    Args:
        data: The extracted data model to validate.
        required_fields: List of field names that must be present.

    Returns:
        List of validation results.
    """
    results: list[ValidationResult] = []

    if required_fields:
        for field_name in required_fields:
            value = getattr(data, field_name, None)
            if value is None:
                results.append(
                    ValidationResult(
                        field_name=field_name,
                        is_valid=False,
                        severity=ValidationSeverity.CRITICAL,
                        message=f"Required field '{field_name}' is missing",
                    )
                )
            elif isinstance(value, str) and not value.strip():
                results.append(
                    ValidationResult(
                        field_name=field_name,
                        is_valid=False,
                        severity=ValidationSeverity.CRITICAL,
                        message=f"Required field '{field_name}' is empty",
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        field_name=field_name,
                        is_valid=True,
                        message=f"Field '{field_name}' is present",
                    )
                )

    return results
