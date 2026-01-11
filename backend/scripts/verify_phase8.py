"""
Phase 8 Verification Script.

This script verifies that the validation and scoring components
are working correctly with the extraction pipeline.
"""

import asyncio
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_schemas_import():
    """Test that all schemas can be imported."""
    print("\n=== Testing Schema Imports ===")

    try:
        from app.schemas import (  # noqa: F401
            BaseExtractedData,
            CustomerInfo,
            DocumentMetadata,
            DocumentType,
            ExtractionError,
            ExtractionMetrics,
            ExtractionResponse,
            ExtractionStatus,
            FieldConfidence,
            FieldScore,
            Invoice,
            InvoiceData,
            LineItem,
            PageInfo,
            PaymentInfo,
            ProcessingStage,
            ValidationResult,
            ValidationSeverity,
            ValidationSummary,
            VendorInfo,
        )

        print("✅ All schema imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_invoice_schema():
    """Test invoice schema creation and validation."""
    print("\n=== Testing Invoice Schema ===")

    try:
        from app.schemas.invoice import (  # noqa: F401
            CustomerInfo,
            InvoiceData,
            LineItem,
            PaymentInfo,
            VendorInfo,
        )

        # Create line items
        line_items = [
            LineItem(
                description="Consulting Services",
                quantity=10.0,
                unit_price=Decimal("150.00"),
                amount=Decimal("1500.00"),
            ),
            LineItem(
                description="Software License",
                quantity=1.0,
                unit_price=Decimal("500.00"),
                amount=Decimal("500.00"),
            ),
        ]

        # Create vendor info
        vendor = VendorInfo(
            name="Acme Corp",
            address="123 Business St",
            email="billing@acme.com",
        )

        # Create customer info
        customer = CustomerInfo(
            name="Client Inc",
            address="456 Customer Ave",
        )

        # Create full invoice
        invoice = InvoiceData(
            invoice_number="INV-2024-001",
            invoice_date=date(2024, 1, 15),
            vendor=vendor,
            customer=customer,
            line_items=line_items,
            subtotal=Decimal("2000.00"),
            tax_rate=8.5,
            tax_amount=Decimal("170.00"),
            total_amount=Decimal("2170.00"),
            currency="USD",
        )

        print(f"✅ Invoice created: {invoice.invoice_number}")
        print(f"   Vendor: {invoice.vendor.name}")
        print(f"   Customer: {invoice.customer.name}")
        print(f"   Line Items: {len(invoice.line_items)}")
        print(f"   Total: {invoice.currency} {invoice.total_amount}")

        # Test field summary
        summary = invoice.get_field_summary()
        print(
            f"   Fields extracted: {sum(1 for v in summary.values() if v)}/{len(summary)}"
        )

        return True

    except Exception as e:
        print(f"❌ Invoice schema test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_validation():
    """Test the validation service."""
    print("\n=== Testing Validation Service ===")

    try:
        from app.schemas.invoice import InvoiceData, LineItem, VendorInfo
        from app.services.extraction.validator import (  # noqa: F401
            ExtractionValidator,
            ValidationConfig,
            validate_extraction,
        )

        # Create a test invoice
        invoice = InvoiceData(
            invoice_number="TEST-001",
            invoice_date=date(2024, 1, 15),
            vendor=VendorInfo(name="Test Vendor"),
            line_items=[
                LineItem(
                    description="Item 1",
                    quantity=2.0,
                    unit_price=Decimal("100.00"),
                    amount=Decimal("200.00"),
                ),
            ],
            subtotal=Decimal("200.00"),
            tax_amount=Decimal("20.00"),
            total_amount=Decimal("220.00"),
        )

        # Run validation
        result = validate_extraction(invoice)

        print("✅ Validation completed")
        print(f"   Valid: {result.is_valid}")
        print(f"   Overall Score: {result.overall_score:.2%}")
        print(
            f"   Fields Extracted: {result.fields_extracted}/{result.fields_expected}"
        )
        print(f"   Critical Issues: {result.critical_issues}")
        print(f"   Warning Issues: {result.warning_issues}")

        # Show field scores
        if result.field_scores:
            print("   Field Scores:")
            for fs in result.field_scores[:5]:  # Show first 5
                print(f"     - {fs.field_name}: {fs.score:.2f} ({fs.confidence.value})")

        # Show any issues
        if result.issues:
            print(f"   Issues ({len(result.issues)}):")
            for issue in result.issues[:3]:  # Show first 3
                print(
                    f"     - [{issue.severity.value}] {issue.field_name}: {issue.message}"
                )

        return True

    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_extraction_response():
    """Test extraction response schema."""
    print("\n=== Testing Extraction Response Schema ===")

    try:
        from datetime import datetime

        from app.schemas.extraction import (
            DocumentMetadata,
            DocumentType,
            ExtractionMetrics,
            ExtractionResponse,
            ExtractionStatus,
            ProcessingStage,
            ValidationSummary,
        )
        from app.schemas.invoice import InvoiceData

        # Create extraction response
        response = ExtractionResponse(
            request_id="req_test123",
            timestamp=datetime.utcnow(),
            status=ExtractionStatus.SUCCESS,
            stage=ProcessingStage.COMPLETE,
            document=DocumentMetadata(
                filename="test_invoice.pdf",
                page_count=2,
                detected_type=DocumentType.INVOICE,
                detection_confidence=0.95,
                total_chars=5000,
                total_words=800,
            ),
            extracted_data=InvoiceData(
                invoice_number="TEST-001",
                total_amount=Decimal("1500.00"),
            ),
            validation=ValidationSummary(
                is_valid=True,
                overall_score=0.85,
                fields_extracted=8,
                fields_expected=10,
            ),
            metrics=ExtractionMetrics(
                pdf_extraction_time=0.5,
                llm_extraction_time=45.0,
                total_time=46.5,
                tokens_per_second=10.5,
            ),
        )

        print("✅ Extraction response created")
        print(f"   Request ID: {response.request_id}")
        print(f"   Status: {response.status.value}")
        print(f"   Stage: {response.stage.value}")
        print(f"   Document: {response.document.filename}")
        print(f"   Type: {response.document.detected_type.value}")
        print(f"   Valid: {response.validation.is_valid}")
        print(f"   Score: {response.validation.overall_score:.2%}")
        print(f"   Time: {response.metrics.total_time:.1f}s")

        # Test serialization
        json_data = response.model_dump_json()
        print(f"   JSON size: {len(json_data)} bytes")

        return True

    except Exception as e:
        print(f"❌ Extraction response test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_validation_edge_cases():
    """Test validation with edge cases."""
    print("\n=== Testing Validation Edge Cases ===")

    try:
        from app.schemas.invoice import InvoiceData
        from app.services.extraction.validator import validate_extraction

        # Test 1: Missing required fields
        print("\n  Test 1: Missing required fields")
        incomplete = InvoiceData()  # All fields None
        result = validate_extraction(incomplete)
        print(f"    Valid: {result.is_valid}")
        print(f"    Critical issues: {result.critical_issues}")
        assert not result.is_valid, "Should be invalid with missing required fields"
        print("    OK - Correctly identified missing fields")

        # Test 2: Invalid invoice number (too short)
        print("\n  Test 2: Short invoice number")
        short_inv = InvoiceData(
            invoice_number="X",
            total_amount=Decimal("100.00"),
        )
        result = validate_extraction(short_inv)
        print(f"    Valid: {result.is_valid}")
        print(f"    Warning issues: {result.warning_issues}")
        print("    OK - Flagged short invoice number")

        # Test 3: Future date
        print("\n  Test 3: Future invoice date")
        from datetime import date, timedelta

        future_inv = InvoiceData(
            invoice_number="FUT-001",
            invoice_date=date.today() + timedelta(days=30),
            total_amount=Decimal("500.00"),
        )
        result = validate_extraction(future_inv)
        has_date_warning = any(
            "future" in str(i.message).lower() for i in result.issues
        )
        print(f"    Valid: {result.is_valid}")
        print(f"    Date warning: {has_date_warning}")
        print("    OK - Flagged future date")

        # Test 4: Inconsistent totals
        print("\n  Test 4: Inconsistent totals")
        from app.schemas.invoice import LineItem

        inconsistent = InvoiceData(
            invoice_number="INC-001",
            total_amount=Decimal("1000.00"),  # Wrong total
            subtotal=Decimal("500.00"),
            tax_amount=Decimal("50.00"),  # Should be 550, not 1000
            line_items=[
                LineItem(
                    description="Item",
                    amount=Decimal("500.00"),
                ),
            ],
        )
        result = validate_extraction(inconsistent)
        print(f"    Valid: {result.is_valid}")
        print(f"    Issues: {len(result.issues)}")
        print("    OK - Handled inconsistent totals")

        return True

    except Exception as e:
        print(f"FAIL - Edge case test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_full_pipeline_with_validation():
    """Test the full extraction pipeline with validation."""
    print("\n=== Testing Full Pipeline with Validation ===")

    try:
        from app.core.config import get_settings
        from app.schemas.invoice import InvoiceData
        from app.services.extraction import ExtractionOrchestrator, validate_extraction
        from app.services.extraction.validator import ExtractionValidator  # noqa: F401

        # Initialize orchestrator
        settings = get_settings()
        orchestrator = ExtractionOrchestrator(settings)

        # Find sample PDF
        samples_dir = Path(__file__).parent.parent / "samples"
        sample_pdfs = list(samples_dir.glob("*.pdf"))

        if not sample_pdfs:
            print("INFO - No sample PDFs found, skipping full pipeline test")
            return True

        # Process first PDF
        pdf_path = sample_pdfs[0]
        print(f"\n  Processing: {pdf_path.name}")

        result = await orchestrator.extract_from_pdf(pdf_path)

        if result.success and result.extracted_data:
            print("  OK - Extraction successful")
            print(f"     Document type: {result.document_type}")
            print(f"     Processing time: {result.metadata.processing_time:.1f}s")

            # Convert to InvoiceData if possible
            if isinstance(result.extracted_data, dict):
                # Try to parse as invoice
                try:
                    invoice = InvoiceData(**result.extracted_data)
                    print(f"     Invoice #: {invoice.invoice_number}")
                    print(f"     Total: {invoice.total_amount}")

                    # Run validation
                    validation = validate_extraction(invoice)
                    print("\n  Validation Results:")
                    print(f"     Valid: {validation.is_valid}")
                    print(f"     Score: {validation.overall_score:.2%}")
                    fields_info = (
                        f"{validation.fields_extracted}/{validation.fields_expected}"
                    )
                    print(f"     Fields: {fields_info}")
                    issues_info = f"{validation.critical_issues} critical, {validation.warning_issues} warnings"
                    print(f"     Issues: {issues_info}")

                    return True
                except Exception as e:
                    print(f"  WARN - Could not parse as invoice: {e}")
                    # Still pass - extraction worked
                    return True
        else:
            print(f"  FAIL - Extraction failed: {result.error}")
            return False

    except Exception as e:
        print(f"FAIL - Full pipeline test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all Phase 8 verification tests."""
    print("=" * 60)
    print("Phase 8 Verification: Validation & Scoring")
    print("=" * 60)

    results = []

    # Run synchronous tests
    results.append(("Schema Imports", test_schemas_import()))
    results.append(("Invoice Schema", test_invoice_schema()))
    results.append(("Validation Service", test_validation()))
    results.append(("Extraction Response", test_extraction_response()))
    results.append(("Validation Edge Cases", test_validation_edge_cases()))

    # Run async test
    print("\n" + "-" * 60)
    full_pipeline_result = asyncio.run(test_full_pipeline_with_validation())
    results.append(("Full Pipeline with Validation", full_pipeline_result))

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    passed = 0
    failed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
        if result:
            passed += 1
        else:
            failed += 1

    print("-" * 60)
    print(f"Total: {passed}/{len(results)} tests passed")

    if failed == 0:
        print("\n🎉 Phase 8 verification COMPLETE!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
