"""
Phase 9 Verification Script.

Verifies the FastAPI backend API layer is properly implemented.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


def print_result(test_name: str, passed: bool, details: str = ""):
    """Print test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details and not passed:
        print(f"       Details: {details}")


async def test_imports():
    """Test that all API modules can be imported."""
    try:
        # Test deps imports
        from app.api.deps import (  # noqa: F401
            ExtractionParams,
            Orchestrator,
            Validator,
            check_rate_limit,
            get_orchestrator,
            validate_file_extension,
            validate_file_size,
        )

        # Test router imports
        from app.api.v1 import api_router  # noqa: F401
        from app.api.v1.endpoints import extract_router, health_router  # noqa: F401

        print_result("API Module Imports", True)
        return True
    except Exception as e:
        print_result("API Module Imports", False, str(e))
        return False


async def test_router_configuration():
    """Test that routers are properly configured."""
    try:
        from app.api.v1 import api_router
        from app.api.v1.endpoints import extract_router, health_router

        # Check extract router has routes
        extract_routes = [r.path for r in extract_router.routes]
        has_extract_route = (
            any("extract" in str(r.path) for r in extract_router.routes)
            or len(extract_routes) > 0
        )
        assert (
            has_extract_route
        ), f"Extract router missing routes. Found: {extract_routes}"

        # Check health router has routes
        health_routes = [r.path for r in health_router.routes]
        has_health_route = len(health_routes) > 0
        assert has_health_route, f"Health router missing routes. Found: {health_routes}"

        # Check main router includes sub-routers
        main_routes = [r.path for r in api_router.routes]
        has_extract = any("/extract" in str(r.path) for r in api_router.routes)
        has_health = any("/health" in str(r.path) for r in api_router.routes)

        assert has_extract, f"API router missing /extract. Found: {main_routes}"
        assert has_health, f"API router missing /health. Found: {main_routes}"

        print_result("Router Configuration", True)
        return True
    except Exception as e:
        print_result("Router Configuration", False, str(e))
        return False


async def test_fastapi_app():
    """Test that FastAPI app is properly configured."""
    try:
        from app.main import app

        # Check app has routes
        routes = [r.path for r in app.routes]
        assert "/" in routes, "App missing root endpoint"
        assert "/health" in routes, "App missing health endpoint"

        # Check API v1 routes are included
        has_api_routes = any("/api/v1" in str(r.path) for r in app.routes)
        assert has_api_routes, "App missing API v1 routes"

        print_result("FastAPI App Configuration", True)
        return True
    except Exception as e:
        print_result("FastAPI App Configuration", False, str(e))
        return False


async def test_dependency_injection():
    """Test dependency injection utilities."""
    try:
        from app.api.deps import (
            RateLimiter,
            get_validator_config,
            validate_file_extension,
            validate_file_size,
        )

        # Test rate limiter
        limiter = RateLimiter(requests_per_minute=5)
        result = await limiter.check_rate_limit("test_client")
        if not result:
            raise AssertionError("Rate limiter should allow first request")

        # Test validator config
        config = get_validator_config()
        if config.fail_on_critical is not True:
            raise AssertionError("Validator config should fail on critical")

        # Test file validation
        ext = validate_file_extension("test.pdf")
        if ext != ".pdf":
            raise AssertionError(f"Expected .pdf, got {ext}")

        # Test file size validation (should pass for small file)
        validate_file_size(1024)  # 1KB should pass

        # Test file size validation (should fail for huge file)
        try:
            validate_file_size(100 * 1024 * 1024 * 1024)  # 100GB should fail
            raise AssertionError("Should have raised exception")
        except AssertionError:
            raise  # Re-raise our assertion
        except Exception:
            pass  # Expected exception from validate_file_size

        print_result("Dependency Injection", True)
        return True
    except Exception as e:
        print_result("Dependency Injection", False, str(e))
        return False


async def test_health_endpoints():
    """Test health endpoint response models."""
    try:
        from app.api.v1.endpoints.health import ComponentStatus, HealthResponse

        # Test component status model
        status = ComponentStatus(
            name="test",
            status="healthy",
            latency_ms=10.5,
            message="OK",
        )
        assert status.name == "test"
        assert status.status == "healthy"

        # Test health response model
        response = HealthResponse(
            status="healthy",
            version="1.0.0",
            timestamp="2024-01-01T00:00:00Z",
            environment="development",
            uptime_seconds=100.0,
        )
        assert response.status == "healthy"

        print_result("Health Endpoints", True)
        return True
    except Exception as e:
        print_result("Health Endpoints", False, str(e))
        return False


async def test_extract_endpoint():
    """Test extract endpoint helpers."""
    try:
        from app.api.v1.endpoints.extract import (
            ALLOWED_EXTENSIONS,
            MAX_FILE_SIZE,
            build_error_response,
            build_success_response,
        )

        # Check constants
        assert ".pdf" in ALLOWED_EXTENSIONS
        assert MAX_FILE_SIZE > 0

        # Test error response builder
        error_resp = build_error_response(
            request_id="test-123",
            error_message="Test error",
            stage="llm_extraction",
        )
        if error_resp.status.value != "failed":
            raise AssertionError(
                f"Expected failed status, got {error_resp.status.value}"
            )
        if error_resp.request_id != "test-123":
            raise AssertionError(f"Expected test-123, got {error_resp.request_id}")

        # Test success response builder
        success_resp = build_success_response(
            request_id="test-456",
            document_type="invoice",
            extracted_data={"invoice_number": "INV-001"},
            processing_time=1.5,
            file_path=None,
            original_filename="test.pdf",
        )
        if success_resp.status.value != "success":
            raise AssertionError(
                f"Expected success status, got {success_resp.status.value}"
            )
        if success_resp.request_id != "test-456":
            raise AssertionError(f"Expected test-456, got {success_resp.request_id}")

        print_result("Extract Endpoint", True)
        return True
    except Exception as e:
        print_result("Extract Endpoint", False, str(e))
        return False


async def main():
    """Run all Phase 9 verification tests."""
    print("\n" + "=" * 60)
    print("Phase 9: FastAPI Backend API Layer - Verification")
    print("=" * 60 + "\n")

    tests = [
        test_imports,
        test_router_configuration,
        test_fastapi_app,
        test_dependency_injection,
        test_health_endpoints,
        test_extract_endpoint,
    ]

    results = []
    for test in tests:
        result = await test()
        results.append(result)

    print("\n" + "-" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n✅ Phase 9 verification PASSED!")
        print("   FastAPI backend API layer is properly implemented.")
        return 0
    else:
        print("\n❌ Phase 9 verification FAILED!")
        print("   Please review the failing tests above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
