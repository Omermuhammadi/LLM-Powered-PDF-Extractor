#!/usr/bin/env python3
"""Quick test for the multipage invoice."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # noqa: E402

from app.services.extraction import ExtractionOrchestrator  # noqa: E402

orchestrator = ExtractionOrchestrator()
result = orchestrator.extract_from_pdf(
    Path(__file__).parent.parent.parent / "samples" / "sample_multipage_invoice.pdf"
)

print("Success:", result.success)
print("Doc Type:", result.document_type)
if result.error:
    print("Error:", result.error)
if result.extracted_fields:
    for k, v in list(result.extracted_fields.items())[:8]:
        print(f"  {k}: {v}")
