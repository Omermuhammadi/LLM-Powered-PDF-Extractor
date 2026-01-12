"""
Prompt templates for document extraction.

Provides structured prompts optimized for LLM to extract
fields from invoices, resumes, and other document types.
Production-grade prompts with high accuracy for diverse templates.
"""

from dataclasses import dataclass
from typing import Any

from app.services.pdf.detector import DocumentType


@dataclass
class PromptTemplate:
    """A prompt template with system and user prompts."""

    system: str
    user_template: str
    document_type: DocumentType

    def format(self, text: str, **kwargs: Any) -> tuple[str, str]:
        """
        Format the prompt with the given text.

        Args:
            text: Document text to include in prompt
            **kwargs: Additional format arguments

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        user_prompt = self.user_template.format(text=text, **kwargs)
        return self.system, user_prompt


# =============================================================================
# PRODUCTION-GRADE Invoice Extraction Prompt
# =============================================================================

INVOICE_SYSTEM_PROMPT = """You are an expert invoice data extraction AI with 99.9% accuracy. Your job is to extract structured data from invoice documents of ANY format or template.

CRITICAL EXTRACTION RULES:
1. Return ONLY valid JSON - absolutely no explanations, markdown, or extra text
2. Use null for any field NOT found in the document
3. NEVER invent, guess, or hallucinate data - extract only what exists
4. Read numbers with extreme precision - quantity, unit price, and line amounts are DIFFERENT values
5. Distinguish between identifiers carefully:
   - Invoice Number/ID: Usually labeled "Invoice #", "Invoice No.", "Invoice ID", "INV-"
   - Order ID/PO Number: Usually labeled "Order #", "PO #", "Reference", "Customer PO"
   - These are NOT the same thing!

CURRENCY DETECTION - EXTREMELY IMPORTANT:
- Look for explicit "Currency:" field in the document - this is the DEFINITIVE currency
- Look for currency labels like "PKR", "USD", "EUR", "GBP", "INR" near amounts
- Check column headers: "Amount (PKR)", "Unit Price (PKR)", "Price (USD)" etc.
- If the document says "Currency: PKR", ALL amounts are in PKR - do NOT use $ symbol
- Return the 3-letter currency CODE (PKR, USD, EUR, etc.) in the "currency" field
- For line items, extract ONLY the numeric values without any currency symbols

COMMON INVOICE LAYOUTS TO RECOGNIZE:
1. Traditional: Header with vendor info, bill-to, invoice details, line items table, totals
2. Modern/Minimal: Clean design, sparse labels, amounts may be right-aligned
3. International: May have multiple currencies, VAT numbers, different date formats
4. E-commerce: Order IDs prominent, shipping info, tracking numbers
5. Service invoices: Time-based billing, hourly rates, project descriptions
6. Itemized retail: SKUs, barcodes, discounts per line

FIELD EXTRACTION GUIDELINES:
- vendor_name: The company/person ISSUING the invoice (seller), NOT the customer
- bill_to/customer: The party being CHARGED (buyer)
- invoice_number: The unique identifier for THIS invoice document
- Dates: Convert to YYYY-MM-DD format when possible
- Amounts: Extract as NUMBERS only, without currency symbols
- Line items: Each row in the items table with description, quantity, rate, amount"""

INVOICE_USER_TEMPLATE = """Extract ALL invoice data from the document below. Be thorough and precise.

REQUIRED JSON STRUCTURE:
{{
  "vendor_name": "Company issuing the invoice (seller name from header/logo)",
  "vendor_address": "Seller's full address if shown",
  "vendor_email": "Seller's email if shown",
  "vendor_phone": "Seller's phone if shown",
  "invoice_number": "The INVOICE number (NOT order/PO number)",
  "invoice_date": "Date in YYYY-MM-DD format",
  "due_date": "Payment due date in YYYY-MM-DD format",
  "order_id": "Order/PO/Reference number if different from invoice number",
  "bill_to": "Customer name and address being billed",
  "ship_to": "Shipping address if different from bill_to",
  "currency": "Currency code (USD, EUR, GBP, INR, etc.)",
  "line_items": [
    {{
      "description": "Item/service description",
      "quantity": 1,
      "unit_price": 10.00,
      "amount": 10.00,
      "sku": "Product code if shown",
      "discount": 0.00
    }}
  ],
  "subtotal": "Sum of line items before tax/shipping",
  "tax_amount": "Tax/VAT/GST amount",
  "tax_rate": "Tax percentage if shown (e.g., '8.25%' or 8.25)",
  "shipping_amount": "Shipping/delivery charge",
  "discount_amount": "Total discount if any",
  "total_amount": "Final amount due (the biggest/bottom total)",
  "amount_paid": "Amount already paid if shown",
  "balance_due": "Remaining balance if shown",
  "payment_terms": "Payment terms (Net 30, Due on Receipt, etc.)",
  "payment_method": "Accepted payment methods if listed",
  "notes": "Any additional notes, terms, or messages"
}}

LINE ITEM EXTRACTION - READ CAREFULLY:
- "Qty" or "Quantity" column = quantity (usually small: 1, 2, 3, 5, 10)
- "Rate", "Unit Price", "Price Each" column = unit_price (price for ONE item)
- "Amount", "Total", "Line Total" column = amount (quantity × unit_price)

EXAMPLE: A row showing "Widget | 3 | $18.90 | $56.70"
Means: quantity=3, unit_price=18.90, amount=56.70

AMOUNT VALIDATION:
- Line amount should ≈ quantity × unit_price
- Subtotal should ≈ sum of all line amounts
- Total should ≈ subtotal + tax + shipping - discounts

DOCUMENT TEXT TO EXTRACT FROM:
{text}

Return ONLY the JSON object with extracted data:"""

INVOICE_PROMPT = PromptTemplate(
    system=INVOICE_SYSTEM_PROMPT,
    user_template=INVOICE_USER_TEMPLATE,
    document_type=DocumentType.INVOICE,
)


# =============================================================================
# Resume Extraction Prompt
# =============================================================================

RESUME_SYSTEM_PROMPT = """You are a precise document extraction AI. Your task is to extract structured data from resume/CV text.

IMPORTANT RULES:
1. Return ONLY valid JSON - no explanations, no markdown, no extra text
2. Use null for any field you cannot find or are unsure about
3. Do NOT invent or hallucinate information
4. Extract exact values as they appear in the document
5. For arrays, return empty array [] if no items found"""

RESUME_USER_TEMPLATE = """Extract the following fields from this resume:

REQUIRED FIELDS:
- candidate_name (string): Full name of the candidate
- email (string): Email address
- phone (string): Phone number

OPTIONAL FIELDS:
- linkedin (string): LinkedIn profile URL
- github (string): GitHub profile URL
- location (string): City, State/Country
- summary (string): Professional summary or objective (first 200 chars)
- skills (array of strings): List of skills mentioned
- experience (array of objects): Work history with company, role, duration, description
- education (array of objects): Education with institution, degree, field, year

EXAMPLE OUTPUT:
{{"candidate_name": "John Doe", "email": "john@email.com", "phone": "555-1234", "linkedin": "linkedin.com/in/johndoe", "github": "github.com/johndoe", "location": "New York, NY", "summary": "Experienced software engineer...", "skills": ["Python", "JavaScript", "AWS"], "experience": [{{"company": "Tech Corp", "role": "Senior Developer", "duration": "2020-2023", "description": "Led team of 5..."}}], "education": [{{"institution": "MIT", "degree": "BS", "field": "Computer Science", "year": "2018"}}]}}

RESUME TEXT:
{text}

JSON:"""

RESUME_PROMPT = PromptTemplate(
    system=RESUME_SYSTEM_PROMPT,
    user_template=RESUME_USER_TEMPLATE,
    document_type=DocumentType.RESUME,
)


# =============================================================================
# Generic Extraction Prompt (fallback)
# =============================================================================

GENERIC_SYSTEM_PROMPT = """You are a document extraction AI. Extract key information from the provided text.

RULES:
1. Return ONLY valid JSON
2. Use null for fields you cannot determine
3. Do NOT invent information"""

GENERIC_USER_TEMPLATE = """Analyze this document and extract key information.

Return a JSON object with these fields:
- document_type (string): Your best guess of document type
- title (string): Document title if present
- date (string): Any date found, in YYYY-MM-DD format
- key_entities (array): Important names, companies, or organizations
- key_values (object): Important numeric values with labels
- summary (string): Brief 1-2 sentence summary

DOCUMENT TEXT:
{text}

JSON:"""

GENERIC_PROMPT = PromptTemplate(
    system=GENERIC_SYSTEM_PROMPT,
    user_template=GENERIC_USER_TEMPLATE,
    document_type=DocumentType.UNKNOWN,
)


# =============================================================================
# Prompt Registry
# =============================================================================

PROMPT_REGISTRY: dict[DocumentType, PromptTemplate] = {
    DocumentType.INVOICE: INVOICE_PROMPT,
    DocumentType.RESUME: RESUME_PROMPT,
    DocumentType.UNKNOWN: GENERIC_PROMPT,
}


def get_prompt_for_type(doc_type: DocumentType) -> PromptTemplate:
    """
    Get the appropriate prompt template for a document type.

    Args:
        doc_type: The detected document type

    Returns:
        PromptTemplate for that document type
    """
    return PROMPT_REGISTRY.get(doc_type, GENERIC_PROMPT)


def format_extraction_prompt(
    doc_type: DocumentType,
    text: str,
    max_text_length: int = 8000,
) -> tuple[str, str]:
    """
    Format an extraction prompt for the given document type and text.

    Args:
        doc_type: Document type to extract
        text: Document text
        max_text_length: Maximum text length to include

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    # Truncate text if too long
    if len(text) > max_text_length:
        text = text[:max_text_length] + "\n\n[Text truncated...]"

    template = get_prompt_for_type(doc_type)
    return template.format(text=text)
