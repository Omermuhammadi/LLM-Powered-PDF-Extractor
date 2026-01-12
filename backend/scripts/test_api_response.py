#!/usr/bin/env python
"""Test API response format to debug frontend issues."""

import json
from pathlib import Path

import requests


def test_extraction_api():
    """Call extraction API and print the response format."""

    # Find a sample PDF
    samples_dir = Path(__file__).parent.parent.parent / "samples"
    pdf_files = list(samples_dir.glob("*.pdf"))

    if not pdf_files:
        print("No PDF files found in samples/")
        return

    pdf_path = pdf_files[0]
    print(f"Testing with: {pdf_path.name}")

    # Call API
    url = "http://localhost:8000/api/v1/extract/"

    with open(pdf_path, "rb") as f:
        files = {"file": (pdf_path.name, f, "application/pdf")}
        data = {"validate_output": "true", "include_raw_text": "false"}

        print("Sending request...")
        try:
            response = requests.post(url, files=files, data=data, timeout=300)

            print(f"\nStatus Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")

            if response.status_code == 200:
                result = response.json()
                print("\n=== RESPONSE JSON ===")
                print(json.dumps(result, indent=2, default=str))

                # Check critical fields that frontend expects
                print("\n=== FRONTEND COMPATIBILITY CHECK ===")
                print(f"request_id: {result.get('request_id')}")
                print(f"status: {result.get('status')}")
                print(f"document: {result.get('document')}")
                print(f"extracted_data type: {type(result.get('extracted_data'))}")
                print(f"validation: {result.get('validation')}")
                print(f"metrics: {result.get('metrics')}")
            else:
                print(f"\nError Response: {response.text}")

        except requests.exceptions.Timeout:
            print("Request timed out after 300s")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    test_extraction_api()
