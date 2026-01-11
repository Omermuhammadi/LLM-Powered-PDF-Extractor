"""
Extraction validation service.

This module provides validation logic for extracted data,
including field-level scoring, consistency checks, and
overall quality assessment.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, Optional

from app.schemas.base import (
    FieldConfidence,
    FieldScore,
    ValidationResult,
    ValidationSeverity,
)
from app.schemas.extraction import ValidationSummary
from app.schemas.invoice import InvoiceData, LineItem

logger = logging.getLogger(__name__)


@dataclass
class ValidationConfig:
    """Configuration for validation behavior."""

    # Minimum confidence threshold for valid extraction
    min_confidence_threshold: float = 0.5

    # Whether to fail on critical issues
    fail_on_critical: bool = True

    # Required fields for different document types
    required_invoice_fields: list[str] = field(default_factory=list)

    # Patterns for field validation
    invoice_number_pattern: str = r"^[A-Za-z0-9\-_/]+$"
    currency_codes: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize default values."""
        if not self.required_invoice_fields:
            self.required_invoice_fields = [
                "invoice_number",
                "total_amount",
            ]
        if not self.currency_codes:
            self.currency_codes = ["USD", "EUR", "GBP", "CAD", "AUD", "INR"]


class ExtractionValidator:
    """
    Validates extracted data for quality and consistency.

    This class provides comprehensive validation including:
    - Field presence checks
    - Format validation
    - Consistency validation (e.g., totals match)
    - Confidence scoring
    """

    def __init__(self, config: Optional[ValidationConfig] = None):
        """
        Initialize the validator.

        Args:
            config: Validation configuration. Uses defaults if not provided.
        """
        self.config = config or ValidationConfig()
        self._field_weights = self._get_default_field_weights()

    def _get_default_field_weights(self) -> dict[str, float]:
        """Get default weights for field importance in scoring."""
        return {
            # Critical fields
            "invoice_number": 1.0,
            "total_amount": 1.0,
            # Important fields
            "invoice_date": 0.8,
            "vendor_name": 0.8,
            "subtotal": 0.7,
            "tax_amount": 0.6,
            # Moderate importance
            "customer_name": 0.5,
            "line_items": 0.5,
            "payment_terms": 0.4,
            # Lower importance
            "notes": 0.2,
            "reference_number": 0.2,
        }

    def validate_invoice(
        self,
        invoice: InvoiceData,
        raw_data: Optional[dict[str, Any]] = None,
    ) -> ValidationSummary:
        """
        Validate an extracted invoice.

        Args:
            invoice: The extracted invoice data.
            raw_data: Optional raw extraction data for comparison.

        Returns:
            ValidationSummary with results.
        """
        issues: list[ValidationResult] = []
        field_scores: list[FieldScore] = []

        # Track fields
        fields_expected = len(self.config.required_invoice_fields) + 5
        fields_extracted = 0

        # Validate required fields
        for field_name in self.config.required_invoice_fields:
            result = self._validate_required_field(invoice, field_name)
            if result:
                issues.append(result)
            else:
                fields_extracted += 1

        # Validate invoice number format
        if invoice.invoice_number:
            fields_extracted += 1
            score, issue = self._validate_invoice_number(invoice.invoice_number)
            field_scores.append(score)
            if issue:
                issues.append(issue)

        # Validate dates
        if invoice.invoice_date:
            fields_extracted += 1
            score, issue = self._validate_date_field(
                "invoice_date", invoice.invoice_date
            )
            field_scores.append(score)
            if issue:
                issues.append(issue)

        # Validate monetary amounts
        if invoice.total_amount is not None:
            fields_extracted += 1
            score, issue = self._validate_monetary_amount(
                "total_amount", invoice.total_amount
            )
            field_scores.append(score)
            if issue:
                issues.append(issue)

        if invoice.subtotal is not None:
            fields_extracted += 1
            score, issue = self._validate_monetary_amount("subtotal", invoice.subtotal)
            field_scores.append(score)
            if issue:
                issues.append(issue)

        if invoice.tax_amount is not None:
            fields_extracted += 1
            score, issue = self._validate_monetary_amount(
                "tax_amount", invoice.tax_amount
            )
            field_scores.append(score)
            if issue:
                issues.append(issue)

        # Validate line items
        if invoice.line_items:
            fields_extracted += 1
            li_scores, li_issues = self._validate_line_items(invoice.line_items)
            field_scores.extend(li_scores)
            issues.extend(li_issues)

        # Validate totals consistency
        consistency_issues = self._validate_totals_consistency(invoice)
        issues.extend(consistency_issues)

        # Validate vendor info
        if invoice.vendor and invoice.vendor.name:
            fields_extracted += 1
            score = FieldScore(
                field_name="vendor_name",
                score=0.8,
                confidence=FieldConfidence.HIGH,
                extracted_value=invoice.vendor.name,
            )
            field_scores.append(score)

        # Validate customer info
        if invoice.customer and invoice.customer.name:
            fields_extracted += 1

        # Validate currency
        if invoice.currency:
            score, issue = self._validate_currency(invoice.currency)
            field_scores.append(score)
            if issue:
                issues.append(issue)

        # Calculate overall score
        overall_score = self._calculate_overall_score(field_scores, issues)

        # Count issues by severity
        critical_count = sum(
            1 for i in issues if i.severity == ValidationSeverity.CRITICAL
        )
        warning_count = sum(
            1 for i in issues if i.severity == ValidationSeverity.WARNING
        )

        # Determine validity
        is_valid = (
            critical_count == 0 or not self.config.fail_on_critical
        ) and overall_score >= self.config.min_confidence_threshold

        return ValidationSummary(
            is_valid=is_valid,
            overall_score=overall_score,
            field_scores=field_scores,
            issues=issues,
            critical_issues=critical_count,
            warning_issues=warning_count,
            fields_extracted=fields_extracted,
            fields_expected=fields_expected,
        )

    def _validate_required_field(
        self,
        invoice: InvoiceData,
        field_name: str,
    ) -> Optional[ValidationResult]:
        """Check if a required field is present and non-empty."""
        value = getattr(invoice, field_name, None)

        if value is None:
            readable_name = field_name.replace("_", " ")
            return ValidationResult(
                field_name=field_name,
                is_valid=False,
                severity=ValidationSeverity.CRITICAL,
                message=f"Required field '{field_name}' is missing",
                suggestion=f"Ensure the document contains {readable_name}",
            )

        if isinstance(value, str) and not value.strip():
            readable_name = field_name.replace("_", " ")
            return ValidationResult(
                field_name=field_name,
                is_valid=False,
                severity=ValidationSeverity.CRITICAL,
                message=f"Required field '{field_name}' is empty",
                suggestion=f"Verify {readable_name} was extracted correctly",
            )

        return None

    def _validate_invoice_number(
        self,
        invoice_number: str,
    ) -> tuple[FieldScore, Optional[ValidationResult]]:
        """Validate invoice number format."""
        issue = None
        confidence = FieldConfidence.HIGH
        score = 1.0

        # Check for suspicious patterns
        if len(invoice_number) < 2:
            confidence = FieldConfidence.LOW
            score = 0.3
            issue = ValidationResult(
                field_name="invoice_number",
                is_valid=False,
                severity=ValidationSeverity.WARNING,
                message="Invoice number appears too short",
                suggestion="Verify invoice number was extracted correctly",
            )
        elif len(invoice_number) > 50:
            confidence = FieldConfidence.LOW
            score = 0.3
            issue = ValidationResult(
                field_name="invoice_number",
                is_valid=False,
                severity=ValidationSeverity.WARNING,
                message="Invoice number appears too long",
                suggestion="May contain extra text",
            )
        elif not re.match(self.config.invoice_number_pattern, invoice_number):
            confidence = FieldConfidence.MEDIUM
            score = 0.6
            issue = ValidationResult(
                field_name="invoice_number",
                is_valid=True,
                severity=ValidationSeverity.INFO,
                message="Invoice number contains unusual characters",
            )

        field_score = FieldScore(
            field_name="invoice_number",
            score=score,
            confidence=confidence,
            extracted_value=invoice_number,
        )

        return field_score, issue

    def _validate_date_field(
        self,
        field_name: str,
        date_value: date,
    ) -> tuple[FieldScore, Optional[ValidationResult]]:
        """Validate a date field."""
        issue = None
        confidence = FieldConfidence.HIGH
        score = 1.0

        today = date.today()

        # Check for future dates (unusual for invoices)
        if date_value > today:
            confidence = FieldConfidence.MEDIUM
            score = 0.7
            issue = ValidationResult(
                field_name=field_name,
                is_valid=True,
                severity=ValidationSeverity.WARNING,
                message=f"{field_name.replace('_', ' ').title()} is in the future",
                suggestion="Verify the date is correct",
            )

        # Check for very old dates
        years_old = (today - date_value).days / 365
        if years_old > 5:
            confidence = FieldConfidence.MEDIUM
            score = 0.6
            issue = ValidationResult(
                field_name=field_name,
                is_valid=True,
                severity=ValidationSeverity.INFO,
                message=f"{field_name.replace('_', ' ').title()} is over 5 years old",
            )

        field_score = FieldScore(
            field_name=field_name,
            score=score,
            confidence=confidence,
            extracted_value=str(date_value),
        )

        return field_score, issue

    def _validate_monetary_amount(
        self,
        field_name: str,
        amount: Decimal,
    ) -> tuple[FieldScore, Optional[ValidationResult]]:
        """Validate a monetary amount."""
        issue = None
        confidence = FieldConfidence.HIGH
        score = 1.0

        # Check for negative amounts
        if amount < 0:
            confidence = FieldConfidence.LOW
            score = 0.3
            issue = ValidationResult(
                field_name=field_name,
                is_valid=False,
                severity=ValidationSeverity.WARNING,
                message=f"{field_name.replace('_', ' ').title()} is negative",
                suggestion="Verify the amount sign",
            )

        # Check for zero (might be valid but suspicious)
        elif amount == 0:
            confidence = FieldConfidence.MEDIUM
            score = 0.5
            issue = ValidationResult(
                field_name=field_name,
                is_valid=True,
                severity=ValidationSeverity.INFO,
                message=f"{field_name.replace('_', ' ').title()} is zero",
            )

        # Check for unreasonably large amounts
        elif amount > Decimal("10000000"):
            confidence = FieldConfidence.MEDIUM
            score = 0.6
            issue = ValidationResult(
                field_name=field_name,
                is_valid=True,
                severity=ValidationSeverity.INFO,
                message=f"{field_name.replace('_', ' ').title()} is unusually large",
                suggestion="Verify the decimal placement",
            )

        field_score = FieldScore(
            field_name=field_name,
            score=score,
            confidence=confidence,
            extracted_value=str(amount),
        )

        return field_score, issue

    def _validate_line_items(
        self,
        line_items: list[LineItem],
    ) -> tuple[list[FieldScore], list[ValidationResult]]:
        """Validate invoice line items."""
        scores: list[FieldScore] = []
        issues: list[ValidationResult] = []

        for i, item in enumerate(line_items):
            # Check for description
            if not item.description:
                issues.append(
                    ValidationResult(
                        field_name=f"line_item_{i}_description",
                        is_valid=False,
                        severity=ValidationSeverity.WARNING,
                        message=f"Line item {i + 1} missing description",
                    )
                )

            # Check for amount
            if item.amount is None:
                issues.append(
                    ValidationResult(
                        field_name=f"line_item_{i}_amount",
                        is_valid=False,
                        severity=ValidationSeverity.WARNING,
                        message=f"Line item {i + 1} missing amount",
                    )
                )

            # Validate quantity * unit_price = amount
            if (
                item.quantity is not None
                and item.unit_price is not None
                and item.amount is not None
            ):
                expected = Decimal(str(item.quantity)) * item.unit_price
                tolerance = Decimal("0.02")  # Allow 2 cents tolerance
                if abs(item.amount - expected) > tolerance:
                    issues.append(
                        ValidationResult(
                            field_name=f"line_item_{i}_calculation",
                            is_valid=False,
                            severity=ValidationSeverity.WARNING,
                            message=f"Line item {i + 1}: amount != qty × price",
                            suggestion=f"Expected {expected}, got {item.amount}",
                        )
                    )

        # Overall line items score
        if line_items:
            items_with_amounts = sum(
                1 for item in line_items if item.amount is not None
            )
            completeness = items_with_amounts / len(line_items)
            confidence = (
                FieldConfidence.HIGH
                if completeness > 0.8
                else (
                    FieldConfidence.MEDIUM
                    if completeness > 0.5
                    else FieldConfidence.LOW
                )
            )
            scores.append(
                FieldScore(
                    field_name="line_items",
                    score=completeness,
                    confidence=confidence,
                    extracted_value=f"{len(line_items)} items",
                )
            )

        return scores, issues

    def _validate_totals_consistency(
        self,
        invoice: InvoiceData,
    ) -> list[ValidationResult]:
        """Validate that invoice totals are mathematically consistent."""
        issues: list[ValidationResult] = []
        tolerance = Decimal("0.02")

        # Check line items sum to subtotal
        if invoice.line_items and invoice.subtotal is not None:
            items_total = sum(
                item.amount for item in invoice.line_items if item.amount is not None
            )
            if items_total > 0 and abs(invoice.subtotal - items_total) > tolerance:
                hint = f"Items sum: {items_total}, Subtotal: {invoice.subtotal}"
                issues.append(
                    ValidationResult(
                        field_name="subtotal",
                        is_valid=False,
                        severity=ValidationSeverity.WARNING,
                        message="Subtotal doesn't match sum of line items",
                        suggestion=hint,
                    )
                )

        # Check subtotal + tax - discount = total
        if invoice.subtotal is not None and invoice.total_amount is not None:
            calculated = invoice.subtotal
            if invoice.tax_amount is not None:
                calculated += invoice.tax_amount
            if invoice.discount_amount is not None:
                calculated -= invoice.discount_amount
            if invoice.shipping_amount is not None:
                calculated += invoice.shipping_amount

            if abs(invoice.total_amount - calculated) > tolerance:
                # Only warn if we have enough info for calculation
                if invoice.tax_amount is not None or invoice.discount_amount is None:
                    hint = f"Calculated: {calculated}, Got: {invoice.total_amount}"
                    issues.append(
                        ValidationResult(
                            field_name="total_amount",
                            is_valid=False,
                            severity=ValidationSeverity.INFO,
                            message="Total doesn't match calculated total",
                            suggestion=hint,
                        )
                    )

        return issues

    def _validate_currency(
        self,
        currency: str,
    ) -> tuple[FieldScore, Optional[ValidationResult]]:
        """Validate currency code."""
        issue = None
        confidence = FieldConfidence.HIGH
        score = 1.0

        if currency.upper() not in self.config.currency_codes:
            confidence = FieldConfidence.MEDIUM
            score = 0.7
            issue = ValidationResult(
                field_name="currency",
                is_valid=True,
                severity=ValidationSeverity.INFO,
                message=f"Currency '{currency}' is not in common currencies list",
            )

        field_score = FieldScore(
            field_name="currency",
            score=score,
            confidence=confidence,
            extracted_value=currency,
        )

        return field_score, issue

    def _calculate_overall_score(
        self,
        field_scores: list[FieldScore],
        issues: list[ValidationResult],
    ) -> float:
        """Calculate overall validation score."""
        if not field_scores:
            return 0.0

        # Weighted average of field scores
        total_weight = 0.0
        weighted_sum = 0.0

        for fs in field_scores:
            weight = self._field_weights.get(fs.field_name, 0.5)
            weighted_sum += fs.score * weight
            total_weight += weight

        if total_weight == 0:
            base_score = 0.5
        else:
            base_score = weighted_sum / total_weight

        # Penalize for issues
        critical_penalty = 0.3
        warning_penalty = 0.1
        info_penalty = 0.02

        penalty = 0.0
        for issue in issues:
            if issue.severity == ValidationSeverity.CRITICAL:
                penalty += critical_penalty
            elif issue.severity == ValidationSeverity.WARNING:
                penalty += warning_penalty
            elif issue.severity == ValidationSeverity.INFO:
                penalty += info_penalty

        # Cap penalty at 50%
        penalty = min(penalty, 0.5)

        final_score = max(0.0, base_score - penalty)
        return round(final_score, 3)


def validate_extraction(
    data: InvoiceData,
    raw_data: Optional[dict[str, Any]] = None,
    config: Optional[ValidationConfig] = None,
) -> ValidationSummary:
    """
    Convenience function to validate extracted data.

    Args:
        data: Extracted invoice data.
        raw_data: Optional raw extraction for comparison.
        config: Optional validation configuration.

    Returns:
        ValidationSummary with results.
    """
    validator = ExtractionValidator(config)
    return validator.validate_invoice(data, raw_data)
