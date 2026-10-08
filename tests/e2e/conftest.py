"""Pytest configuration and fixtures for CineMatch E2E test suite."""

import os
import sys
from collections.abc import Generator
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tests.e2e.contracts.mock_app import create_contract_app

# Singleton contract app instance
_contract_app = create_contract_app()


@pytest.fixture(scope="session")
def api_base_url() -> str | None:
    """Return base URL if testing against a live server, else None."""
    return os.environ.get("CINEMATCH_BASE_URL")


@pytest.fixture(scope="function")
def client(api_base_url: str | None) -> Generator[httpx.Client | TestClient, None, None]:
    """Provide HTTP client configured for live or contract app.

    Resets profile state before each test to guarantee complete test isolation.
    """
    if api_base_url:
        with httpx.Client(base_url=api_base_url, timeout=10.0) as http_client:
            # Trigger reset if endpoint exists
            try:
                resp = http_client.post("/api/v1/profiles/reset")
                resp.raise_for_status()
            except (httpx.HTTPError, OSError):
                # Reset endpoint is optional on some external live server deployments
                pass
            yield http_client
    else:
        # Check if actual backend app exists and is requested
        if os.environ.get("USE_LIVE_BACKEND") == "1":
            try:
                from backend.app.main import app as live_app

                test_client = TestClient(live_app)
                try:
                    test_client.post("/api/v1/profiles/reset")
                except (httpx.HTTPError, RuntimeError):
                    pass
                yield test_client
                return
            except ImportError:
                pass

        # Standalone contract-compliant test client
        test_client = TestClient(_contract_app)
        test_client.post("/api/v1/profiles/reset")
        yield test_client
        # Cleanup / reset after test as well
        test_client.post("/api/v1/profiles/reset")
