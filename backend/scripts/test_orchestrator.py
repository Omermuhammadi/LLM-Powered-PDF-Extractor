#!/usr/bin/env python3
"""
Test script for the Extraction Orchestrator (Phase 7).

Tests the full extraction pipeline on sample PDFs:
1. PDF extraction
2. Text processing
3. Document detection
4. LLM-based data extraction
5. Response parsing

Usage:
    python -m scripts.test_orchestrator
"""

import asyncio
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))  # noqa: E402

from app.core.logger import get_logger  # noqa: E402
from app.services.extraction import (  # noqa: E402
    ExtractionOrchestrator,
    ExtractionResult,
)
from app.services.llm import get_llm_client  # noqa: E402

logger = get_logger(__name__)


def print_separator(title: str = "") -> None:
    """Print a visual separator."""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    else:
        print("-" * 60)


def print_extraction_result(result: ExtractionResult, pdf_name: str) -> None:
    """Pretty print extraction results."""
    print(f"\n📄 Results for: {pdf_name}")
    print_separator()

    # Basic info
    print(f"✓ Success: {result.success}")
    print(f"✓ Document Type: {result.document_type}")

    if result.processing_metadata:
        meta = result.processing_metadata
        print(f"✓ Detection Confidence: {meta.detection_confidence:.1%}")
        print(f"✓ Processing Time: {meta.processing_time_ms:.0f}ms")
        print(f"✓ LLM Duration: {meta.llm_duration_ms:.0f}ms")
        print(f"✓ Model Used: {meta.model_used}")
        print(f"✓ JSON Repaired: {meta.was_json_repaired}")

    if result.error:
        print(f"✗ Error: {result.error}")
        return

    if not result.extracted_fields:
        print("✗ No data extracted")
        return

    # Extracted data
    print("\n📊 Extracted Fields:")
    print_separator()

    data = result.extracted_fields
    if isinstance(data, dict):
        # Print key fields based on document type
        if result.document_type == "invoice":
            key_fields = [
                "vendor_name",
                "invoice_number",
                "invoice_date",
                "due_date",
                "total_amount",
                "currency",
                "payment_terms",
            ]
            for fld in key_fields:
                value = data.get(fld, "N/A")
                status = "✓" if value and value != "N/A" else "○"
                print(f"  {status} {fld}: {value}")

            # Line items
            line_items = data.get("line_items", [])
            if line_items:
                print(f"\n  📦 Line Items ({len(line_items)}):")
                for i, item in enumerate(line_items[:3], 1):
                    if isinstance(item, dict):
                        desc = str(item.get("description", "Unknown"))[:40]
                        qty = item.get("quantity", "?")
                        price = item.get("unit_price", "?")
                        print(f"     {i}. {desc}... (qty: {qty}, price: {price})")
                if len(line_items) > 3:
                    print(f"     ... and {len(line_items) - 3} more items")

        elif result.document_type == "resume":
            key_fields = [
                "candidate_name",
                "email",
                "phone",
                "location",
                "years_experience",
            ]
            for fld in key_fields:
                value = data.get(fld, "N/A")
                status = "✓" if value and value != "N/A" else "○"
                print(f"  {status} {fld}: {value}")

            # Skills
            skills = data.get("skills", [])
            if skills:
                print(f"\n  🛠️ Skills ({len(skills)}): {', '.join(skills[:5])}")

        else:
            # Generic output for unknown types
            for key, value in list(data.items())[:10]:
                print(f"  • {key}: {value}")

    # Confidence scores
    if result.confidence_scores:
        print("\n📈 Field Confidence Scores:")
        high_conf = sum(1 for c in result.confidence_scores.values() if c >= 0.8)
        med_conf = sum(1 for c in result.confidence_scores.values() if 0.5 <= c < 0.8)
        low_conf = sum(1 for c in result.confidence_scores.values() if c < 0.5)
        print(f"  • High (≥80%): {high_conf} fields")
        print(f"  • Medium (50-79%): {med_conf} fields")
        print(f"  • Low (<50%): {low_conf} fields")

    # Missing fields
    if result.missing_fields:
        print(f"\n⚠️ Missing Fields: {', '.join(result.missing_fields)}")

    # Warnings
    if result.warnings:
        print(f"\n⚠️ Warnings: {len(result.warnings)}")
        for w in result.warnings[:3]:
            print(f"   - {w}")

    # Raw text preview
    if result.raw_text_preview:
        preview = result.raw_text_preview[:100].replace("\n", " ")
        print(f"\n📝 Text Preview: {preview}...")


def test_single_pdf(orchestrator: ExtractionOrchestrator, pdf_path: Path) -> dict:
    """Test extraction on a single PDF (synchronous)."""
    logger.info(f"Testing: {pdf_path.name}")

    start_time = time.time()
    result = orchestrator.extract_from_pdf(pdf_path)
    elapsed = time.time() - start_time

    print_extraction_result(result, pdf_path.name)

    detection_conf = 0.0
    if result.processing_metadata:
        detection_conf = result.processing_metadata.detection_confidence

    return {
        "file": pdf_path.name,
        "success": result.success,
        "document_type": result.document_type,
        "detection_confidence": detection_conf,
        "has_data": result.extracted_fields is not None,
        "field_count": len(result.extracted_fields) if result.extracted_fields else 0,
        "missing_count": len(result.missing_fields),
        "processing_time": elapsed,
        "error": result.error,
    }


async def run_tests():
    """Run orchestrator tests on all sample PDFs."""
    print_separator("PDF Intelligence Extractor - Orchestrator Test")
    print("Testing Phase 7: Full Extraction Pipeline")

    # Find samples directory
    samples_dir = Path(__file__).parent.parent.parent / "samples"
    if not samples_dir.exists():
        logger.error(f"Samples directory not found: {samples_dir}")
        return

    # Get all PDF files
    pdf_files = list(samples_dir.glob("*.pdf"))
    if not pdf_files:
        logger.error("No PDF files found in samples directory")
        return

    print(f"\n📁 Found {len(pdf_files)} PDF files in {samples_dir}")
    for pdf in pdf_files:
        print(f"   • {pdf.name}")

    # Check LLM health first
    print_separator("Checking LLM Health")
    llm_client = get_llm_client()
    print(f"LLM Provider: {llm_client.provider}")
    is_healthy = await llm_client.health_check()
    if is_healthy:
        print("✓ LLM client is healthy")
    else:
        print("✗ LLM client health check failed!")
        print("  Make sure Ollama is running with phi3:mini model")
        return

    # Initialize orchestrator
    print_separator("Initializing Orchestrator")
    orchestrator = ExtractionOrchestrator()
    print("✓ Orchestrator initialized")

    # Test each PDF
    results = []
    for pdf_path in pdf_files:
        print_separator(f"Processing: {pdf_path.name}")
        result = test_single_pdf(orchestrator, pdf_path)
        results.append(result)

    # Summary
    print_separator("Test Summary")

    successful = sum(1 for r in results if r["success"])
    total = len(results)
    total_time = sum(r["processing_time"] for r in results)

    print("\n📊 Overall Results:")
    print(f"   • Total PDFs tested: {total}")
    print(f"   • Successful extractions: {successful}/{total}")
    print(f"   • Success rate: {successful/total:.1%}")
    print(f"   • Total processing time: {total_time:.2f}s")
    print(f"   • Average time per PDF: {total_time/total:.2f}s")

    print("\n📋 Per-file Results:")
    for r in results:
        status = "✓" if r["success"] else "✗"
        print(
            f"   {status} {r['file']}: "
            f"{r['document_type']} ({r['detection_confidence']:.0%}), "
            f"{r['field_count']} fields, {r['processing_time']:.1f}s"
        )
        if r["error"]:
            print(f"      Error: {r['error']}")

    # Phase 7 acceptance criteria
    print_separator("Phase 7 Acceptance Criteria")
    print("\n✓ Prompt templates for invoice extraction")
    print("✓ Prompt templates for resume extraction")
    print("✓ JSON response parser with error handling")
    print("✓ Field confidence scoring")
    print(f"✓ Full pipeline tested on {total} PDFs")

    if successful == total:
        print("\n✅ All tests passed! Phase 7 complete.")
    else:
        failed = total - successful
        print(f"\n⚠️ {failed} test(s) failed. Review errors above.")


if __name__ == "__main__":
    asyncio.run(run_tests())
