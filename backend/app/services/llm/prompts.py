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
# PRODUCTION-GRADE Resume Extraction Prompt
# =============================================================================

RESUME_SYSTEM_PROMPT = """You are an expert HR/recruitment AI with 99.9% accuracy in resume parsing. Your job is to extract structured data from resumes/CVs of ANY format or template.

CRITICAL EXTRACTION RULES:
1. Return ONLY valid JSON - absolutely no explanations, markdown, or extra text
2. Use null for any field NOT found in the document
3. NEVER invent, guess, or hallucinate data - extract only what exists
4. Clean up OCR artifacts and formatting issues in text
5. Infer total experience from job dates when not explicitly stated

EXPERIENCE EXTRACTION - EXTREMELY IMPORTANT:
- Extract ALL work experience entries, starting from MOST RECENT
- For each job, capture: company, role/title, duration, key responsibilities
- Calculate duration_months from date ranges (e.g., "Jan 2022 - Dec 2023" = 24 months)
- "Present" or "Current" means the job is ongoing (is_current: true)
- Clean bullet points - combine broken lines, remove special characters

SKILLS EXTRACTION:
- Capture ALL skills mentioned anywhere in the resume
- Include technical skills (programming languages, tools, frameworks)
- Include soft skills (leadership, communication, teamwork)
- Don't duplicate - each skill should appear once
- Keep original casing (Python, not PYTHON or python)

EDUCATION EXTRACTION:
- Extract degree type (Bachelor's, Master's, PhD, etc.)
- Extract field of study / major
- Extract institution name
- Extract graduation year
- Extract GPA if mentioned (normalize to 4.0 scale if needed)

COMMON RESUME LAYOUTS TO RECOGNIZE:
1. Chronological: Experience listed newest-to-oldest
2. Functional: Skills-focused, less emphasis on timeline
3. Combination: Both skills and chronological experience
4. Academic CV: Publications, research, teaching emphasis
5. Modern/Creative: Non-traditional layouts, portfolios
6. ATS-Optimized: Keyword-heavy, simple formatting"""

RESUME_USER_TEMPLATE = """Extract ALL resume data from the document below. Be thorough and precise.

REQUIRED JSON STRUCTURE:
{{
  "candidate_name": "Full name of the candidate",
  "email": "Email address",
  "phone": "Phone number with country code if present",
  "location": "City, State/Country",
  "linkedin_url": "LinkedIn profile URL",
  "github_url": "GitHub profile URL if present",
  "portfolio_url": "Portfolio or personal website if present",
  "current_role": "Current or most recent job title",
  "current_company": "Current or most recent employer",
  "summary": "Professional summary or objective (first 500 chars)",
  "total_experience_years": 5.5,
  "skills": ["Python", "JavaScript", "AWS", "Docker"],
  "technical_skills": ["Python", "AWS", "Docker", "SQL"],
  "soft_skills": ["Leadership", "Communication"],
  "experience": [
    {{
      "company": "Company Name",
      "role": "Job Title",
      "duration": "Jan 2022 - Present",
      "duration_months": 24,
      "start_date": "2022-01",
      "end_date": "Present",
      "location": "City, Country",
      "is_current": true,
      "highlights": [
        "Led team of 5 engineers",
        "Increased revenue by 30%"
      ]
    }}
  ],
  "education": [
    {{
      "institution": "University Name",
      "degree": "Bachelor of Science",
      "field_of_study": "Computer Science",
      "year": "2018",
      "start_year": 2014,
      "end_year": 2018,
      "gpa": 3.8,
      "honors": "Magna Cum Laude",
      "location": "City, Country"
    }}
  ],
  "certifications": ["AWS Solutions Architect", "PMP"],
  "languages": ["English: Native", "Spanish: Professional"],
  "projects": [
    {{
      "name": "Project Name",
      "description": "Brief description",
      "technologies": ["React", "Node.js"],
      "url": "https://github.com/..."
    }}
  ],
  "awards": ["Employee of the Year 2022"],
  "publications": [],
  "interests": ["Open Source", "Machine Learning"]
}}

EXPERIENCE DURATION CALCULATION:
- "Jan 2022 - Present" with today being Jan 2026 = 48 months
- "2020 - 2022" = approximately 24 months
- If only years given, assume Jan to Dec

TOTAL EXPERIENCE CALCULATION:
- Sum all duration_months from experience entries
- Convert to years (divide by 12)
- Account for overlapping jobs (don't double count)

SKILLS GUIDELINES:
- Extract from dedicated "Skills" section
- Also extract from job descriptions (technologies used)
- Keep as individual items, not comma-separated strings

RESUME TEXT TO EXTRACT FROM:
{text}

Return ONLY the JSON object with extracted data:"""

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
# Job Description Extraction Prompt (for ATS scoring)
# =============================================================================

JD_SYSTEM_PROMPT = """You are an expert HR/recruitment AI that analyzes job descriptions. Your job is to extract structured requirements from job postings to enable ATS scoring.

CRITICAL EXTRACTION RULES:
1. Return ONLY valid JSON - absolutely no explanations, markdown, or extra text
2. Use null for any field NOT found in the document
3. NEVER invent requirements - extract only what is explicitly stated
4. Distinguish between REQUIRED and PREFERRED/NICE-TO-HAVE skills
5. Extract all technical terms, tools, and technologies mentioned

SKILL CLASSIFICATION:
- required_skills: Explicitly marked as "required", "must have", "essential", or listed without qualifiers
- preferred_skills: Marked as "preferred", "nice to have", "bonus", "plus", "ideally"

EXPERIENCE PARSING:
- "5+ years" → experience_years_min: 5, experience_years_max: null
- "3-5 years" → experience_years_min: 3, experience_years_max: 5
- "Senior" without years → experience_years_min: 5
- "Junior/Entry" → experience_years_min: 0, experience_years_max: 2

KEYWORD EXTRACTION:
- Extract ALL technical terms, tools, frameworks, methodologies mentioned
- Include: programming languages, databases, cloud services, frameworks, methodologies
- Don't include: generic words like "team", "company", "opportunity\""""

JD_USER_TEMPLATE = """Extract ALL job requirements from the job description below. Be thorough.

REQUIRED JSON STRUCTURE:
{{
  "job_title": "The position title",
  "company_name": "Hiring company name if mentioned",
  "location": "Job location (city, remote, hybrid)",
  "job_type": "Full-time, Part-time, Contract, etc.",
  "experience_required": "Raw text like '5+ years' or 'Senior level'",
  "experience_years_min": 5,
  "experience_years_max": 10,
  "required_skills": ["Python", "AWS", "Docker"],
  "preferred_skills": ["Kubernetes", "Terraform"],
  "required_education": "Bachelor's degree in Computer Science",
  "preferred_education": "Master's degree preferred",
  "required_certifications": ["AWS Solutions Architect"],
  "preferred_certifications": ["Kubernetes CKA"],
  "keywords": ["Python", "AWS", "microservices", "REST API", "agile"],
  "responsibilities": ["Design and implement...", "Lead team of..."],
  "benefits": ["Health insurance", "401k", "Remote work"],
  "salary_range": "$120,000 - $150,000 or null if not mentioned"
}}

SKILL EXTRACTION TIPS:
- Look for "Requirements", "Qualifications", "What you'll need" sections
- Technologies in bullet points are usually required
- "Experience with X is a plus" → preferred_skills

JOB DESCRIPTION TEXT:
{text}

Return ONLY the JSON object:"""


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


def format_jd_extraction_prompt(
    text: str,
    max_text_length: int = 8000,
) -> tuple[str, str]:
    """
    Format a job description extraction prompt.

    Args:
        text: Job description text
        max_text_length: Maximum text length to include

    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    if len(text) > max_text_length:
        text = text[:max_text_length] + "\n\n[Text truncated...]"

    user_prompt = JD_USER_TEMPLATE.format(text=text)
    return JD_SYSTEM_PROMPT, user_prompt
