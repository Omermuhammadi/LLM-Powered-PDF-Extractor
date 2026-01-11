#!/usr/bin/env python
"""
Test script for LLM client (Phase 5).

Tests Ollama + Phi-3 Mini integration with various prompts.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.llm import LLMClient, OllamaClient  # noqa: E402


def print_separator(title: str = "") -> None:
    """Print a visual separator."""
    if title:
        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print(f"{'=' * 60}")
    else:
        print("-" * 60)


def test_ollama_direct() -> bool:
    """Test direct Ollama client."""
    print_separator("TEST 1: Direct Ollama Client")

    client = OllamaClient()

    # Test simple prompt
    print("\n📝 Sending simple prompt...")
    prompt = "What is 2 + 2? Answer with just the number."

    try:
        response = client.generate_sync(
            prompt=prompt,
            temperature=0.0,
            max_tokens=50,
        )

        print("\n✅ Response received:")
        print(f"   Content: {response.content}")
        print(f"   Model: {response.model}")
        print(f"   Duration: {response.total_duration_ms:.0f}ms")
        print(f"   Tokens: {response.eval_count} generated")
        print(f"   Speed: {response.tokens_per_second:.1f} tok/s")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def test_json_generation() -> bool:
    """Test JSON mode generation."""
    print_separator("TEST 2: JSON Mode Generation")

    client = OllamaClient()

    prompt = """Extract the following information as JSON:

Name: John Smith
Email: john@example.com
Phone: 555-1234

Return a JSON object with keys: name, email, phone"""

    print("\n📝 Requesting JSON output...")

    try:
        response = client.generate_sync(
            prompt=prompt,
            temperature=0.0,
            max_tokens=200,
            json_mode=True,
        )

        print("\n✅ JSON Response:")
        print(f"   {response.content}")
        print(f"   Duration: {response.total_duration_ms:.0f}ms")

        # Try to parse the JSON
        import json

        try:
            parsed = json.loads(response.content)
            print(f"\n✅ Valid JSON parsed: {parsed}")
            return True
        except json.JSONDecodeError:
            print("\n⚠️  Response is not valid JSON")
            return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def test_invoice_extraction() -> bool:
    """Test invoice-like extraction prompt."""
    print_separator("TEST 3: Invoice Extraction Simulation")

    client = OllamaClient()

    # Simulated invoice text
    invoice_text = """
    INVOICE
    From: TechCorp Inc.
    Invoice #: INV-2024-001
    Date: 2024-03-15

    Bill To: Acme Corp

    Item              Qty    Price     Total
    Widget A           5    $100.00   $500.00
    Service Fee        1    $150.00   $150.00

    Subtotal: $650.00
    Tax (10%): $65.00
    Total: $715.00
    """

    prompt = f"""You are a document extraction AI. Extract fields from the invoice:

REQUIRED FIELDS:
- vendor_name (string): The company issuing the invoice
- invoice_number (string): The invoice ID/number
- invoice_date (string): Date in YYYY-MM-DD format
- total_amount (number): Final total amount

RULES:
- Return ONLY valid JSON
- Use null for missing fields
- Do NOT invent information

INVOICE TEXT:
{invoice_text}

JSON:"""

    print("\n📝 Extracting invoice data...")

    try:
        response = client.generate_sync(
            prompt=prompt,
            temperature=0.0,
            max_tokens=300,
            json_mode=True,
        )

        print("\n✅ Extraction Response:")
        print(f"   {response.content}")
        print(f"   Duration: {response.total_duration_ms:.0f}ms")

        # Validate JSON
        import json

        try:
            result = json.loads(response.content)
            print("\n📊 Extracted Fields:")
            for key, value in result.items():
                print(f"   {key}: {value}")

            # Check required fields
            required = ["vendor_name", "invoice_number", "invoice_date", "total_amount"]
            missing = [f for f in required if f not in result]

            if missing:
                print(f"\n⚠️  Missing fields: {missing}")
            else:
                print("\n✅ All required fields present!")

            return len(missing) == 0

        except json.JSONDecodeError:
            print("\n⚠️  Response is not valid JSON")
            return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def test_llm_client_abstraction() -> bool:
    """Test the unified LLM client."""
    print_separator("TEST 4: Unified LLM Client")

    try:
        client = LLMClient(mode="local")

        print("\n📊 Client Info:")
        print(f"   Mode: {client.current_mode}")
        print(f"   Provider: {client.provider}")

        prompt = "Say 'Hello from Phi-3!' exactly."

        print("\n📝 Testing unified client...")

        response = client.generate_sync(
            prompt=prompt,
            temperature=0.0,
            max_tokens=50,
        )

        print("\n✅ Response:")
        print(f"   Content: {response.content}")
        print(f"   Provider: {response.provider}")
        print(f"   Model: {response.model}")
        print(f"   Duration: {response.duration_ms:.0f}ms")
        print(f"   Tokens: {response.total_tokens}")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def main() -> None:
    """Run all tests."""
    print_separator("LLM CLIENT TEST SUITE")
    print("Testing Ollama + Phi-3 Mini integration\n")

    results = []

    # Run tests
    results.append(("Direct Ollama", test_ollama_direct()))
    results.append(("JSON Generation", test_json_generation()))
    results.append(("Invoice Extraction", test_invoice_extraction()))
    results.append(("LLM Client Abstraction", test_llm_client_abstraction()))

    # Summary
    print_separator("TEST SUMMARY")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")

    print(f"\n📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! LLM client is ready.")
    else:
        print("\n⚠️  Some tests failed. Check output above.")


if __name__ == "__main__":
    main()
