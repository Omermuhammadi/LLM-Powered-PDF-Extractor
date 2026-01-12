"""
Invoice-specific Pydantic schemas with field scoring.

This module defines the data models for invoice extraction results,
including line items, totals, and confidence scoring for each field.
"""

import re
from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import Field, field_validator, model_validator

from app.schemas.base import BaseExtractedData, FieldConfidence


def parse_percentage(value) -> Optional[float]:
    """Parse percentage values like '16%', '8.25%', '16' into floats."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        # Remove % sign and any whitespace
        cleaned = re.sub(r"[%\s]", "", value)
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


class LineItem(BaseExtractedData):
    """Model for invoice line items."""

    description: Optional[str] = Field(
        default=None,
        description="Description of the item or service",
    )
    quantity: Optional[float] = Field(
        default=None,
        ge=0,
        description="Quantity of items",
    )
    unit_price: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Price per unit",
    )
    amount: Optional[Decimal] = Field(
        default=None,
        description="Total amount for line item (quantity * unit_price)",
    )
    item_code: Optional[str] = Field(
        default=None,
        description="Product or service code",
    )
    unit: Optional[str] = Field(
        default=None,
        description="Unit of measurement (e.g., 'each', 'hour', 'kg')",
    )
    tax_rate: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Tax rate percentage for this item",
    )

    @field_validator("tax_rate", mode="before")
    @classmethod
    def parse_tax_rate(cls, v):
        return parse_percentage(v)

    # Field confidence scores
    description_confidence: FieldConfidence = Field(
        default=FieldConfidence.LOW,
        description="Confidence score for description field",
    )
    quantity_confidence: FieldConfidence = Field(
        default=FieldConfidence.LOW,
        description="Confidence score for quantity field",
    )
    unit_price_confidence: FieldConfidence = Field(
        default=FieldConfidence.LOW,
        description="Confidence score for unit_price field",
    )
    amount_confidence: FieldConfidence = Field(
        default=FieldConfidence.LOW,
        description="Confidence score for amount field",
    )

    @model_validator(mode="after")
    def validate_line_item_consistency(self) -> "LineItem":
        """Validate line item amount matches quantity * unit_price."""
        try:
            if (
                self.quantity is not None
                and self.unit_price is not None
                and self.amount is not None
            ):
                expected = Decimal(str(self.quantity)) * self.unit_price
                # Allow small tolerance for rounding
                tolerance = Decimal("0.01")
                if abs(self.amount - expected) > tolerance:
                    # Don't fail, but mark as potentially inconsistent
                    self.amount_confidence = FieldConfidence.LOW
        except (ValueError, TypeError, RecursionError):
            # Skip validation on error
            pass
        return self


class VendorInfo(BaseExtractedData):
    """Model for vendor/supplier information."""

    name: Optional[str] = Field(
        default=None,
        description="Vendor/supplier company name",
    )
    address: Optional[str] = Field(
        default=None,
        description="Vendor address",
    )
    phone: Optional[str] = Field(
        default=None,
        description="Vendor phone number",
    )
    email: Optional[str] = Field(
        default=None,
        description="Vendor email address",
    )
    tax_id: Optional[str] = Field(
        default=None,
        description="Vendor tax identification number",
    )
    website: Optional[str] = Field(
        default=None,
        description="Vendor website URL",
    )

    # Field confidence scores
    name_confidence: FieldConfidence = Field(
        default=FieldConfidence.LOW,
        description="Confidence score for name field",
    )
    address_confidence: FieldConfidence = Field(
        default=FieldConfidence.LOW,
        description="Confidence score for address field",
    )


class CustomerInfo(BaseExtractedData):
    """Model for customer/billing information."""

    name: Optional[str] = Field(
        default=None,
        description="Customer/billing name",
    )
    address: Optional[str] = Field(
        default=None,
        description="Customer address",
    )
    phone: Optional[str] = Field(
        default=None,
        description="Customer phone number",
    )
    email: Optional[str] = Field(
        default=None,
        description="Customer email address",
    )
    account_number: Optional[str] = Field(
        default=None,
        description="Customer account number",
    )

    # Field confidence scores
    name_confidence: FieldConfidence = Field(
        default=FieldConfidence.LOW,
        description="Confidence score for name field",
    )
    address_confidence: FieldConfidence = Field(
        default=FieldConfidence.LOW,
        description="Confidence score for address field",
    )


class PaymentInfo(BaseExtractedData):
    """Model for payment information."""

    payment_terms: Optional[str] = Field(
        default=None,
        description="Payment terms (e.g., 'Net 30', 'Due on Receipt')",
    )
    due_date: Optional[date] = Field(
        default=None,
        description="Payment due date",
    )
    payment_method: Optional[str] = Field(
        default=None,
        description="Accepted payment methods",
    )
    bank_name: Optional[str] = Field(
        default=None,
        description="Bank name for payment",
    )
    bank_account: Optional[str] = Field(
        default=None,
        description="Bank account number",
    )
    routing_number: Optional[str] = Field(
        default=None,
        description="Bank routing number",
    )

    # Field confidence scores
    payment_terms_confidence: FieldConfidence = Field(
        default=FieldConfidence.LOW,
        description="Confidence score for payment_terms field",
    )
    due_date_confidence: FieldConfidence = Field(
        default=FieldConfidence.LOW,
        description="Confidence score for due_date field",
    )


class InvoiceData(BaseExtractedData):
    """
    Complete invoice data model with all extracted fields.

    This is the main schema for invoice extraction results,
    containing all relevant invoice information with confidence scores.
    """

    # Core invoice identifiers
    invoice_number: Optional[str] = Field(
        default=None,
        description="Invoice number or ID",
    )
    invoice_date: Optional[date] = Field(
        default=None,
        description="Date the invoice was issued",
    )
    purchase_order: Optional[str] = Field(
        default=None,
        description="Related purchase order number",
    )

    # Parties involved
    vendor: Optional[VendorInfo] = Field(
        default=None,
        description="Vendor/supplier information",
    )
    customer: Optional[CustomerInfo] = Field(
        default=None,
        description="Customer/billing information",
    )

    # Line items
    line_items: list[LineItem] = Field(
        default_factory=list,
        description="List of invoice line items",
    )

    # Financial totals
    subtotal: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Subtotal before tax and discounts",
    )
    tax_amount: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Total tax amount",
    )
    tax_rate: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Overall tax rate percentage",
    )

    @field_validator("tax_rate", "discount_percentage", mode="before")
    @classmethod
    def parse_percentage_fields(cls, v):
        return parse_percentage(v)

    discount_amount: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Total discount amount",
    )
    discount_percentage: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Discount percentage",
    )
    shipping_amount: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Shipping/handling charges",
    )
    total_amount: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Total invoice amount",
    )
    currency: Optional[str] = Field(
        default="USD",
        max_length=3,
        description="Currency code (ISO 4217)",
    )
    amount_due: Optional[Decimal] = Field(
        default=None,
        description="Amount currently due",
    )
    amount_paid: Optional[Decimal] = Field(
        default=None,
        ge=0,
        description="Amount already paid",
    )

    # Payment information
    payment: Optional[PaymentInfo] = Field(
        default=None,
        description="Payment details and terms",
    )

    # Additional fields
    notes: Optional[str] = Field(
        default=None,
        description="Additional notes or comments",
    )
    reference_number: Optional[str] = Field(
        default=None,
        description="Reference or transaction number",
    )

    # Field confidence scores for core fields
    invoice_number_confidence: FieldConfidence = Field(
        default=FieldConfidence.LOW,
        description="Confidence score for invoice_number field",
    )
    invoice_date_confidence: FieldConfidence = Field(
        default=FieldConfidence.LOW,
        description="Confidence score for invoice_date field",
    )
    total_amount_confidence: FieldConfidence = Field(
        default=FieldConfidence.LOW,
        description="Confidence score for total_amount field",
    )
    subtotal_confidence: FieldConfidence = Field(
        default=FieldConfidence.LOW,
        description="Confidence score for subtotal field",
    )
    tax_amount_confidence: FieldConfidence = Field(
        default=FieldConfidence.LOW,
        description="Confidence score for tax_amount field",
    )

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize currency code."""
        if v is None:
            return None
        return v.upper()

    @model_validator(mode="after")
    def validate_totals_consistency(self) -> "InvoiceData":
        """Validate that invoice totals are mathematically consistent."""
        try:
            # Check if line items sum to subtotal
            if self.line_items and self.subtotal is not None:
                items_total = sum(
                    item.amount for item in self.line_items if item.amount is not None
                )
                if items_total > 0:
                    tolerance = Decimal("0.01")
                    if abs(self.subtotal - items_total) > tolerance:
                        # Mark subtotal confidence as low if mismatch
                        self.subtotal_confidence = FieldConfidence.LOW

            # Check if subtotal + tax - discount = total
            if self.subtotal is not None and self.total_amount is not None:
                calculated_total = self.subtotal
                if self.tax_amount is not None:
                    calculated_total += self.tax_amount
                if self.discount_amount is not None:
                    calculated_total -= self.discount_amount
                if self.shipping_amount is not None:
                    calculated_total += self.shipping_amount

                tolerance = Decimal("0.01")
                if abs(self.total_amount - calculated_total) > tolerance:
                    # Don't fail, but could affect confidence
                    pass
        except (ValueError, TypeError, RecursionError):
            # Skip validation on error
            pass

        return self

    def get_line_items_total(self) -> Decimal:
        """Calculate total from line items."""
        return sum(
            item.amount for item in self.line_items if item.amount is not None
        ) or Decimal("0")

    def get_field_summary(self) -> dict[str, bool]:
        """Get summary of which fields were extracted."""
        return {
            "invoice_number": self.invoice_number is not None,
            "invoice_date": self.invoice_date is not None,
            "vendor": self.vendor is not None and self.vendor.name is not None,
            "customer": self.customer is not None and self.customer.name is not None,
            "line_items": len(self.line_items) > 0,
            "subtotal": self.subtotal is not None,
            "tax_amount": self.tax_amount is not None,
            "total_amount": self.total_amount is not None,
            "payment_terms": (
                self.payment is not None and self.payment.payment_terms is not None
            ),
        }


# Type alias for backward compatibility
Invoice = InvoiceData
