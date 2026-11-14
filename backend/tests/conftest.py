"""Pytest configuration and test fixtures for CyberShield AI 2.0."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import get_settings


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Fixture providing a synchronous HTTP TestClient for the FastAPI app."""
    with TestClient(app=app, base_url="http://testserver") as test_client:
        yield test_client


@pytest.fixture(scope="session")
def settings():
    """Fixture providing the active settings instance."""
    return get_settings()
