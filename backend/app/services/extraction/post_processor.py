"""
Invoice data post-processor for production-grade accuracy.

Normalizes, validates, and enhances extracted invoice data.
Handles various date formats, currency detection, and amount validation.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.core import logger


@dataclass
class ProcessingResult:
    """Result of post-processing."""

    data: Dict[str, Any]
    confidence_adjustments: Dict[str, float]
    warnings: List[str]
    corrections: List[str]


# Currency symbols to codes mapping
CURRENCY_SYMBOLS = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY",
    "₹": "INR",
    "₽": "RUB",
    "R$": "BRL",
    "C$": "CAD",
    "A$": "AUD",
    "₩": "KRW",
    "₪": "ILS",
    "฿": "THB",
    "₱": "PHP",
    "zł": "PLN",
    "kr": "SEK",  # Also NOK, DKK
    "CHF": "CHF",
    "Rs": "PKR",  # Pakistani Rupee
    "Rs.": "PKR",
    "PKR": "PKR",
}

# Common date format patterns
DATE_PATTERNS = [
    # ISO format
    (r"(\d{4})-(\d{1,2})-(\d{1,2})", "%Y-%m-%d"),
    # US format
    (r"(\d{1,2})/(\d{1,2})/(\d{4})", "%m/%d/%Y"),
    (r"(\d{1,2})/(\d{1,2})/(\d{2})", "%m/%d/%y"),
    # European format
    (r"(\d{1,2})\.(\d{1,2})\.(\d{4})", "%d.%m.%Y"),
    (r"(\d{1,2})-(\d{1,2})-(\d{4})", "%d-%m-%Y"),
    # Written formats
    (r"(\w+)\s+(\d{1,2}),?\s+(\d{4})", "month_name"),
    (r"(\d{1,2})\s+(\w+)\s+(\d{4})", "day_month_year"),
]

MONTH_NAMES = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


def parse_date(date_str: Optional[str]) -> Optional[str]:
    """
    Parse various date formats and return ISO format (YYYY-MM-DD).

    Args:
        date_str: Date string in various formats

    Returns:
        ISO format date string or None if parsing fails
    """
    if not date_str:
        return None

    date_str = str(date_str).strip()

    # Already in ISO format
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return date_str

    # Try common patterns
    for pattern, fmt in DATE_PATTERNS:
        match = re.search(pattern, date_str, re.IGNORECASE)
        if match:
            try:
                if fmt == "month_name":
                    month_str, day, year = match.groups()
                    month = MONTH_NAMES.get(month_str.lower()[:3])
                    if month:
                        return f"{year}-{month:02d}-{int(day):02d}"
                elif fmt == "day_month_year":
                    day, month_str, year = match.groups()
                    month = MONTH_NAMES.get(month_str.lower()[:3])
                    if month:
                        return f"{year}-{month:02d}-{int(day):02d}"
                else:
                    dt = datetime.strptime(match.group(), fmt)
                    return dt.strftime("%Y-%m-%d")
            except (ValueError, AttributeError):
                continue

    return date_str  # Return original if no parsing worked


def parse_amount(amount_str: Any) -> Optional[float]:
    """
    Parse amount string to float, handling various formats.

    Args:
        amount_str: Amount as string or number

    Returns:
        Float amount or None
    """
    if amount_str is None:
        return None

    if isinstance(amount_str, (int, float)):
        return float(amount_str)

    if not isinstance(amount_str, str):
        return None

    # Remove currency symbols and whitespace
    cleaned = amount_str.strip()
    for symbol in CURRENCY_SYMBOLS.keys():
        cleaned = cleaned.replace(symbol, "")

    # Remove thousand separators (but be careful with European format)
    # If format is 1.234,56 (European), convert to 1234.56
    if re.match(r"^\d{1,3}(\.\d{3})+,\d{2}$", cleaned):
        cleaned = cleaned.replace(".", "").replace(",", ".")
    else:
        # Standard format: remove commas
        cleaned = cleaned.replace(",", "")

    # Remove any remaining non-numeric characters except decimal point and minus
    cleaned = re.sub(r"[^\d.\-]", "", cleaned)

    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def detect_currency(data: Dict[str, Any], text: str = "") -> str:
    """
    Detect currency from data or text.

    Args:
        data: Extracted invoice data
        text: Original document text (optional)

    Returns:
        Currency code (default: USD)
    """
    # Check if currency is already set
    if data.get("currency") and len(str(data["currency"])) == 3:
        return str(data["currency"]).upper()

    # Look for currency symbols in amounts
    for field in ["total_amount", "subtotal", "tax_amount"]:
        value = data.get(field)
        if isinstance(value, str):
            for symbol, code in CURRENCY_SYMBOLS.items():
                if symbol in value:
                    return code

    # Look in text
    for symbol, code in CURRENCY_SYMBOLS.items():
        if symbol in text:
            return code

    return "USD"  # Default


def normalize_line_items(line_items: Optional[List[Dict]]) -> List[Dict]:
    """
    Normalize line items to consistent format.

    Args:
        line_items: List of line item dicts

    Returns:
        Normalized line items
    """
    if not line_items:
        return []

    normalized = []
    for item in line_items:
        if not isinstance(item, dict):
            continue

        normalized_item = {
            "description": str(item.get("description", "")).strip() or None,
            "quantity": None,
            "unit_price": None,
            "amount": None,
            "sku": item.get("sku"),
            "discount": parse_amount(item.get("discount")) or 0.0,
        }

        # Parse quantity
        qty = item.get("quantity") or item.get("qty")
        if qty is not None:
            try:
                normalized_item["quantity"] = float(qty)
            except (ValueError, TypeError):
                pass

        # Parse unit price (may be called 'rate', 'price', 'unit_price')
        price = (
            item.get("unit_price")
            or item.get("rate")
            or item.get("price")
            or item.get("price_each")
        )
        normalized_item["unit_price"] = parse_amount(price)

        # Parse amount
        amount = item.get("amount") or item.get("total") or item.get("line_total")
        normalized_item["amount"] = parse_amount(amount)

        # Validate/calculate missing values
        if (
            normalized_item["quantity"]
            and normalized_item["unit_price"]
            and not normalized_item["amount"]
        ):
            normalized_item["amount"] = round(
                normalized_item["quantity"] * normalized_item["unit_price"], 2
            )
        elif (
            normalized_item["quantity"]
            and normalized_item["amount"]
            and not normalized_item["unit_price"]
        ):
            normalized_item["unit_price"] = round(
                normalized_item["amount"] / normalized_item["quantity"], 2
            )
        elif (
            normalized_item["unit_price"]
            and normalized_item["amount"]
            and not normalized_item["quantity"]
        ):
            # Only infer quantity if it makes sense
            calc_qty = normalized_item["amount"] / normalized_item["unit_price"]
            if calc_qty == int(calc_qty):  # Whole number
                normalized_item["quantity"] = int(calc_qty)

        normalized.append(normalized_item)

    return normalized


def validate_amounts(data: Dict[str, Any]) -> Tuple[Dict[str, float], List[str]]:
    """
    Validate that amounts are consistent.

    Args:
        data: Invoice data with amounts

    Returns:
        Tuple of (confidence adjustments, warnings)
    """
    adjustments = {}
    warnings = []

    subtotal = parse_amount(data.get("subtotal"))
    tax = parse_amount(data.get("tax_amount")) or 0.0
    shipping = parse_amount(data.get("shipping_amount")) or 0.0
    discount = parse_amount(data.get("discount_amount")) or 0.0
    total = parse_amount(data.get("total_amount"))

    # Calculate sum of line items
    line_items = data.get("line_items", [])
    if line_items:
        line_sum = sum(
            parse_amount(item.get("amount")) or 0.0
            for item in line_items
            if isinstance(item, dict)
        )

        # Check subtotal matches line items
        if subtotal and line_sum > 0:
            diff = abs(subtotal - line_sum)
            if diff > 0.02:  # Allow 2 cent rounding
                warnings.append(
                    f"Subtotal ({subtotal}) doesn't match line items sum ({line_sum:.2f})"
                )
                adjustments["subtotal"] = -0.1

    # Check total calculation
    if total and subtotal:
        expected_total = subtotal + tax + shipping - discount
        diff = abs(total - expected_total)
        if diff > 0.02:
            warnings.append(
                f"Total ({total}) doesn't match calculated ({expected_total:.2f})"
            )
            adjustments["total_amount"] = -0.1

    return adjustments, warnings


def normalize_line_item_currencies(
    line_items: List[Dict], currency: str
) -> Tuple[List[Dict], List[str]]:
    """
    Ensure all line items use consistent currency.

    Args:
        line_items: List of line item dicts
        currency: The detected/expected currency code

    Returns:
        Tuple of (normalized line items, corrections made)
    """
    corrections = []
    normalized = []

    for item in line_items:
        if not isinstance(item, dict):
            continue

        normalized_item = dict(item)

        # Check and fix unit_price
        unit_price = item.get("unit_price")
        if isinstance(unit_price, str):
            # Check if it has wrong currency symbol
            for symbol, code in CURRENCY_SYMBOLS.items():
                if symbol in str(unit_price) and code != currency:
                    # Remove wrong currency symbol
                    original = unit_price
                    cleaned = parse_amount(unit_price)
                    if cleaned is not None:
                        normalized_item["unit_price"] = cleaned
                        corrections.append(
                            f"Fixed currency in line item unit_price: {original} → {cleaned}"
                        )
                    break

        # Check and fix amount
        amount = item.get("amount")
        if isinstance(amount, str):
            for symbol, code in CURRENCY_SYMBOLS.items():
                if symbol in str(amount) and code != currency:
                    original = amount
                    cleaned = parse_amount(amount)
                    if cleaned is not None:
                        normalized_item["amount"] = cleaned
                        corrections.append(
                            f"Fixed currency in line item amount: {original} → {cleaned}"
                        )
                    break

        normalized.append(normalized_item)

    return normalized, corrections


def post_process_invoice(
    data: Dict[str, Any], original_text: str = ""
) -> ProcessingResult:
    """
    Post-process extracted invoice data for production quality.

    Args:
        data: Raw extracted invoice data
        original_text: Original document text for context

    Returns:
        ProcessingResult with normalized data and metadata
    """
    if not data:
        return ProcessingResult(
            data={},
            confidence_adjustments={},
            warnings=["No data to process"],
            corrections=[],
        )

    warnings = []
    corrections = []
    adjustments = {}

    processed = dict(data)

    # 1. Normalize dates
    for date_field in ["invoice_date", "due_date"]:
        if processed.get(date_field):
            original = processed[date_field]
            parsed = parse_date(original)
            if parsed and parsed != original:
                processed[date_field] = parsed
                corrections.append(f"Normalized {date_field}: {original} → {parsed}")

    # 2. Detect and normalize currency - MUST happen before line item processing
    # First check if currency is explicitly stated in the data
    currency = None
    if processed.get("currency") and len(str(processed["currency"])) == 3:
        currency = str(processed["currency"]).upper()

    # If not, check total/subtotal fields for currency indicators
    if not currency:
        for field in ["total_amount", "subtotal", "grand_total"]:
            value = processed.get(field)
            if isinstance(value, str):
                # Check for currency codes like PKR, USD, EUR
                for code in ["PKR", "USD", "EUR", "GBP", "INR", "CAD", "AUD", "JPY"]:
                    if code in value.upper():
                        currency = code
                        break
                if currency:
                    break

    # If still not found, use symbol detection
    if not currency:
        currency = detect_currency(processed, original_text)

    processed["currency"] = currency
    logger.debug(f"Detected currency: {currency}")

    # 3. Normalize amounts - remove currency symbols and convert to numbers
    amount_fields = [
        "total_amount",
        "subtotal",
        "tax_amount",
        "shipping_amount",
        "discount_amount",
        "amount_paid",
        "balance_due",
        "grand_total",
    ]
    for field in amount_fields:
        if processed.get(field):
            original = processed[field]
            parsed = parse_amount(original)
            if parsed is not None:
                processed[field] = parsed
                if str(original) != str(parsed):
                    corrections.append(f"Parsed {field}: {original} → {parsed}")

    # 4. Normalize line items FIRST (basic normalization)
    if processed.get("line_items"):
        processed["line_items"] = normalize_line_items(processed["line_items"])

        # 5. Fix currency consistency in line items
        processed["line_items"], currency_corrections = normalize_line_item_currencies(
            processed["line_items"], currency
        )
        corrections.extend(currency_corrections)

        if currency_corrections:
            logger.info(
                f"Fixed {len(currency_corrections)} currency inconsistencies in line items"
            )

    # 6. Validate amounts
    amount_adjustments, amount_warnings = validate_amounts(processed)
    adjustments.update(amount_adjustments)
    warnings.extend(amount_warnings)

    # 7. Check required fields
    required_fields = ["invoice_number", "total_amount"]
    for field in required_fields:
        if not processed.get(field):
            warnings.append(f"Missing required field: {field}")
            adjustments[field] = -0.2

    # 8. Confidence boost for complete data
    completeness = (
        sum(1 for k, v in processed.items() if v is not None) / len(processed)
        if processed
        else 0
    )
    if completeness > 0.7:
        adjustments["overall"] = 0.1

    logger.debug(
        f"Post-processing complete: {len(corrections)} corrections, {len(warnings)} warnings"
    )

    return ProcessingResult(
        data=processed,
        confidence_adjustments=adjustments,
        warnings=warnings,
        corrections=corrections,
    )
