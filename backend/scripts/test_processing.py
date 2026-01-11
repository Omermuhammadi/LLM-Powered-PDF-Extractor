#!/usr/bin/env python
"""
Test script for text processing pipeline (Phase 4).

Tests clean_text() and chunk_text() functions on sample PDFs.
Displays before/after comparisons and quality metrics.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.pdf import (  # noqa: E402
    assess_extraction_quality,
    extract_text_from_pdf,
    process_text,
)


def print_separator(title: str = "") -> None:
    """Print a visual separator."""
    if title:
        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print(f"{'=' * 60}")
    else:
        print("-" * 60)


def test_text_processing() -> None:
    """Test text processing on sample PDFs."""
    samples_dir = Path(__file__).parent.parent.parent / "samples"

    if not samples_dir.exists():
        print(f"❌ Samples directory not found: {samples_dir}")
        return

    pdf_files = list(samples_dir.glob("*.pdf"))

    if not pdf_files:
        print("❌ No PDF files found in samples directory")
        return

    print_separator("TEXT PROCESSING PIPELINE TEST")
    print(f"Found {len(pdf_files)} PDF file(s) to process\n")

    for pdf_path in pdf_files:
        print_separator(f"Processing: {pdf_path.name}")

        try:
            # Step 1: Extract text
            print("\n📄 Step 1: Extracting text...")
            result = extract_text_from_pdf(pdf_path, detect_scanned=False)
            raw_text = result.text

            print(f"   Extracted: {result.word_count} words, {result.char_count} chars")

            # Step 2: Process text (clean + chunk)
            print("\n🧹 Step 2: Processing text...")
            processed = process_text(raw_text, max_tokens=3000, overlap_tokens=100)

            # Step 3: Display results
            print("\n📊 RESULTS:")
            print_separator()

            # Quality metrics
            if processed.quality_metrics:
                m = processed.quality_metrics
                print("\n🔍 Quality Metrics:")
                print(f"   Original length:  {m.original_length} chars")
                print(f"   Cleaned length:   {m.cleaned_length} chars")
                print(f"   Reduction:        {m.reduction_ratio:.1%}")
                print(f"   Line count:       {m.line_count}")
                print(f"   Avg line length:  {m.avg_line_length:.1f} chars")
                print(f"   Has structure:    {m.has_structured_data}")
                print(f"   Noise ratio:      {m.noise_ratio:.1%}")

                # Quality assessment
                assessment = assess_extraction_quality(m)
                print("\n📈 Quality Assessment:")
                print(f"   Score:      {assessment['score']:.0f}/100")
                print(f"   Quality:    {assessment['quality'].upper()}")
                print(f"   Status:     {assessment['recommendation']}")
                if assessment["issues"]:
                    print("   Issues:")
                    for issue in assessment["issues"]:
                        print(f"      ⚠️  {issue}")

            # Chunking results
            print(f"\n📦 Chunks: {len(processed.chunks)}")
            for chunk in processed.chunks:
                preview = chunk.content[:80].replace("\n", " ")
                if len(chunk.content) > 80:
                    preview += "..."
                print(f"   [{chunk.index}] {chunk.estimated_tokens} tokens: {preview}")

            # Before/After comparison
            print("\n📝 TEXT COMPARISON:")
            print("\n--- BEFORE (raw, first 300 chars) ---")
            print(raw_text[:300])
            if len(raw_text) > 300:
                print("...")

            print("\n--- AFTER (cleaned, first 300 chars) ---")
            print(processed.cleaned_text[:300])
            if len(processed.cleaned_text) > 300:
                print("...")

        except Exception as e:
            print(f"❌ Error processing {pdf_path.name}: {e}")

    print_separator("TEST COMPLETE")


def test_chunking_large_text() -> None:
    """Test chunking behavior with synthetic large text."""
    print_separator("CHUNKING TEST (Synthetic Large Text)")

    # Create a large synthetic text
    paragraph = (
        "This is a sample paragraph for testing text chunking. "
        "It contains multiple sentences with various punctuation marks. "
        "The chunking algorithm should break at sentence boundaries! "
        "This helps maintain context across chunks. "
    )

    # Repeat to create ~5000 tokens worth of text
    large_text = paragraph * 100  # ~2000 words, ~2500 tokens

    print(f"Input text: {len(large_text)} chars, ~{len(large_text)//4} tokens")

    # Process with small chunk size to test chunking
    processed = process_text(large_text, max_tokens=500, overlap_tokens=50)

    print(f"Created {len(processed.chunks)} chunks:")
    for chunk in processed.chunks:
        print(
            f"  Chunk {chunk.index}: {chunk.estimated_tokens} tokens, "
            f"chars {chunk.start_char}-{chunk.end_char}"
        )

    # Verify overlap
    if len(processed.chunks) >= 2:
        c0_end = processed.chunks[0].content[-100:]
        c1_start = processed.chunks[1].content[:100]
        has_overlap = any(word in c1_start for word in c0_end.split()[-5:])
        msg = "Overlapping content detected" if has_overlap else "No overlap"
        print(f"\n✓ Overlap verification: {msg}")


if __name__ == "__main__":
    test_text_processing()
    print("\n")
    test_chunking_large_text()
