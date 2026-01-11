"""
Prompt templates for document extraction.

Provides structured prompts optimized for Phi-3 Mini to extract
fields from invoices, resumes, and other document types.
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
# Invoice Extraction Prompt
# =============================================================================

INVOICE_SYSTEM_PROMPT = """You are a precise document extraction AI. Your task is to extract structured data from invoice text.

IMPORTANT RULES:
1. Return ONLY valid JSON - no explanations, no markdown, no extra text
2. Use null for any field you cannot find or are unsure about
3. Do NOT invent or hallucinate information
4. Extract exact values as they appear in the document
5. For dates, convert to YYYY-MM-DD format when possible
6. For amounts, extract as numbers without currency symbols"""

INVOICE_USER_TEMPLATE = """Extract the following fields from this invoice:

REQUIRED FIELDS:
- vendor_name (string): The company/person issuing the invoice
- invoice_number (string): The invoice ID/number/reference
- invoice_date (string): Invoice date in YYYY-MM-DD format
- total_amount (number): The final total amount to pay

OPTIONAL FIELDS:
- currency (string): Currency code like USD, EUR, GBP (default: USD)
- tax_amount (number): Tax amount if shown separately
- subtotal (number): Subtotal before tax
- due_date (string): Payment due date in YYYY-MM-DD format
- bill_to (string): Customer/recipient name or company
- line_items (array): List of items with description, quantity, price

EXAMPLE OUTPUT:
{{"vendor_name": "ABC Corp", "invoice_number": "INV-001", "invoice_date": "2024-03-15", "total_amount": 1500.00, "currency": "USD", "tax_amount": 100.00, "subtotal": 1400.00, "due_date": "2024-04-15", "bill_to": "Customer Inc", "line_items": [{{"description": "Service", "quantity": 1, "price": 1400.00}}]}}

INVOICE TEXT:
{text}

JSON:"""

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
