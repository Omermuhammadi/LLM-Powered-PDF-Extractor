"""
Test script for PDF extraction.
Run from backend directory.
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.pdf.extractor import (  # noqa: E402
    extract_text_from_pdf,
    get_text_preview,
)


def test_pdf_extraction():
    """Test PDF extraction on all sample files."""
    samples_dir = Path(__file__).parent.parent.parent / "samples"
    pdf_files = list(samples_dir.glob("*.pdf"))

    print("\n" + "=" * 60)
    print("PDF EXTRACTION TEST")
    print("=" * 60)
    print(f"Found {len(pdf_files)} PDF files in samples/\n")

    results = []

    for pdf_path in sorted(pdf_files):
        print("\n" + "─" * 60)
        print(f"Testing: {pdf_path.name}")
        print("─" * 60)

        try:
            result = extract_text_from_pdf(pdf_path)

            print("\n📊 Extraction Results:")
            print(f"   • Pages Processed: {result.pages_processed}")
            print(f"   • Character Count: {result.char_count:,}")
            print(f"   • Word Count: {result.word_count:,}")
            print(f"   • Is Scanned: {result.is_scanned}")

            print("\n📋 Metadata:")
            for key, value in result.metadata.items():
                if value:
                    print(f"   • {key}: {value}")

            print("\n📝 Text Preview (first 500 chars):")
            preview = get_text_preview(result.text, 500)
            print(f"   {preview[:200]}...")

            results.append({"file": pdf_path.name, "success": True, "result": result})

        except Exception as e:
            print(f"\n❌ Error: {type(e).__name__}: {str(e)}")
            results.append({"file": pdf_path.name, "success": False, "error": str(e)})

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    successful = sum(1 for r in results if r["success"])
    print(f"✓ Successful: {successful}/{len(results)}")

    for r in results:
        status = "✓" if r["success"] else "✗"
        if r["success"]:
            res = r["result"]
            fname = r["file"]
            print(f"  {status} {fname}: {res.word_count} words, {res.pages_processed}p")
        else:
            print(f"  {status} {r['file']}: {r['error']}")


if __name__ == "__main__":
    test_pdf_extraction()
