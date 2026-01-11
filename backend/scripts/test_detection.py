#!/usr/bin/env python
"""
Test script for document type detection (Phase 6).

Tests detect_document_type() function on sample texts and PDFs.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.pdf import (  # noqa: E402
    detect_document_type,
    extract_text_from_pdf,
    is_invoice,
    is_resume,
)


def print_separator(title: str = "") -> None:
    """Print a visual separator."""
    if title:
        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print(f"{'=' * 60}")
    else:
        print("-" * 60)


# Sample texts for testing
SAMPLE_INVOICE_TEXT = """
INVOICE

TechCorp Solutions Inc.
123 Business Street
Invoice Number: INV-2024-0892
Invoice Date: 2024-03-15
Due Date: 2024-04-15

Bill To:
Acme Corporation
456 Client Avenue

Description          Qty    Unit Price    Amount
Consulting Services   10     $150.00      $1,500.00
Software License       1     $500.00        $500.00

                              Subtotal:   $2,000.00
                              Tax (8%):     $160.00
                              Total:      $2,160.00

Payment Terms: Net 30
Please remit payment to the address above.
"""

SAMPLE_RESUME_TEXT = """
JOHN SMITH
Software Engineer

Email: john.smith@email.com
Phone: (555) 123-4567
LinkedIn: linkedin.com/in/johnsmith
GitHub: github.com/johnsmith

PROFESSIONAL SUMMARY
Experienced software engineer with 5+ years of expertise in Python,
JavaScript, and cloud technologies. Strong background in building
scalable web applications.

WORK EXPERIENCE

Senior Software Engineer | TechCorp Inc.
January 2020 - Present
- Led development of microservices architecture
- Mentored junior developers
- Improved system performance by 40%

Software Developer | StartupXYZ
June 2018 - December 2019
- Developed RESTful APIs using Python/Flask
- Implemented CI/CD pipelines

EDUCATION

Bachelor of Science in Computer Science
University of Technology | 2018
GPA: 3.8/4.0

SKILLS
Python, JavaScript, React, Node.js, AWS, Docker, PostgreSQL, Git

CERTIFICATIONS
- AWS Certified Solutions Architect
- Google Cloud Professional Developer
"""

SAMPLE_UNKNOWN_TEXT = """
Meeting Notes - January 2024

Attendees: Alice, Bob, Charlie

Discussion Points:
1. Project timeline review
2. Budget allocation
3. Resource planning

Action Items:
- Alice to prepare report
- Bob to schedule follow-up
- Charlie to update documentation

Next meeting: February 1, 2024
"""


def test_invoice_detection() -> bool:
    """Test invoice detection."""
    print_separator("TEST 1: Invoice Detection")

    result = detect_document_type(SAMPLE_INVOICE_TEXT)

    print("\n📊 Detection Result:")
    print(f"   Type: {result.document_type.value}")
    print(f"   Confidence: {result.confidence:.1%}")
    print(f"   Invoice Score: {result.scores['invoice']:.1%}")
    print(f"   Resume Score: {result.scores['resume']:.1%}")

    print("\n🔑 Matched Keywords:")
    for kw in result.matched_keywords[:5]:
        print(f"   • {kw}")

    print("\n🔍 Matched Patterns:")
    for p in result.matched_patterns[:3]:
        print(f"   • {p}")

    # Assertions
    is_correct = result.document_type.value == "invoice"
    is_confident = result.confidence >= 0.5

    print(f"\n✅ Type correct: {is_correct}")
    print(f"✅ Confidence >= 50%: {is_confident}")

    return is_correct and is_confident


def test_resume_detection() -> bool:
    """Test resume detection."""
    print_separator("TEST 2: Resume Detection")

    result = detect_document_type(SAMPLE_RESUME_TEXT)

    print("\n📊 Detection Result:")
    print(f"   Type: {result.document_type.value}")
    print(f"   Confidence: {result.confidence:.1%}")
    print(f"   Invoice Score: {result.scores['invoice']:.1%}")
    print(f"   Resume Score: {result.scores['resume']:.1%}")

    print("\n🔑 Matched Keywords:")
    for kw in result.matched_keywords[:5]:
        print(f"   • {kw}")

    print("\n🔍 Matched Patterns:")
    for p in result.matched_patterns[:3]:
        print(f"   • {p}")

    is_correct = result.document_type.value == "resume"
    is_confident = result.confidence >= 0.5

    print(f"\n✅ Type correct: {is_correct}")
    print(f"✅ Confidence >= 50%: {is_confident}")

    return is_correct and is_confident


def test_unknown_detection() -> bool:
    """Test unknown document detection."""
    print_separator("TEST 3: Unknown Document Detection")

    result = detect_document_type(SAMPLE_UNKNOWN_TEXT)

    print("\n📊 Detection Result:")
    print(f"   Type: {result.document_type.value}")
    print(f"   Confidence: {result.confidence:.1%}")
    print(f"   Invoice Score: {result.scores['invoice']:.1%}")
    print(f"   Resume Score: {result.scores['resume']:.1%}")

    # For unknown, we expect low confidence for both types
    low_confidence = result.confidence < 0.5

    print(f"\n✅ Low confidence (unknown): {low_confidence}")

    return low_confidence


def test_helper_functions() -> bool:
    """Test is_invoice() and is_resume() helpers."""
    print_separator("TEST 4: Helper Functions")

    invoice_check = is_invoice(SAMPLE_INVOICE_TEXT)
    resume_check = is_resume(SAMPLE_RESUME_TEXT)
    not_invoice = not is_invoice(SAMPLE_RESUME_TEXT)
    not_resume = not is_resume(SAMPLE_INVOICE_TEXT)

    print(f"   is_invoice(invoice_text): {invoice_check}")
    print(f"   is_resume(resume_text): {resume_check}")
    print(f"   NOT is_invoice(resume_text): {not_invoice}")
    print(f"   NOT is_resume(invoice_text): {not_resume}")

    return invoice_check and resume_check and not_invoice and not_resume


def test_pdf_detection() -> bool:
    """Test detection on actual PDF files."""
    print_separator("TEST 5: PDF File Detection")

    samples_dir = Path(__file__).parent.parent.parent / "samples"

    if not samples_dir.exists():
        print("⚠️  Samples directory not found, skipping PDF test")
        return True

    pdf_files = list(samples_dir.glob("*.pdf"))

    if not pdf_files:
        print("⚠️  No PDF files found, skipping")
        return True

    all_passed = True

    for pdf_path in pdf_files:
        try:
            # Extract text
            extraction = extract_text_from_pdf(pdf_path, detect_scanned=False)

            # Detect type
            result = detect_document_type(extraction.text)

            status = "✅" if result.document_type.value == "invoice" else "⚠️"
            print(f"   {status} {pdf_path.name}:")
            print(f"      Type: {result.document_type.value}")
            print(f"      Confidence: {result.confidence:.1%}")

            # Our sample PDFs should be invoices
            if "invoice" in pdf_path.name.lower():
                if result.document_type.value != "invoice":
                    all_passed = False

        except Exception as e:
            print(f"   ❌ {pdf_path.name}: Error - {e}")
            all_passed = False

    return all_passed


def main() -> None:
    """Run all detection tests."""
    print_separator("DOCUMENT TYPE DETECTION TEST SUITE")

    results = []

    results.append(("Invoice Detection", test_invoice_detection()))
    results.append(("Resume Detection", test_resume_detection()))
    results.append(("Unknown Detection", test_unknown_detection()))
    results.append(("Helper Functions", test_helper_functions()))
    results.append(("PDF Detection", test_pdf_detection()))

    # Summary
    print_separator("TEST SUMMARY")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")

    print(f"\n📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Document detection is ready.")
    else:
        print("\n⚠️  Some tests failed. Check output above.")


if __name__ == "__main__":
    main()
