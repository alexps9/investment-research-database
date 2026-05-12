"""
Health endpoint tests - TDD Red Phase
MUST run this test and see it FAIL before implementing
"""

import pytest
from fastapi.testclient import TestClient


def test_health_endpoint_returns_200():
    """Health endpoint must return 200 status"""
    from app.main import app

    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200


def test_health_endpoint_returns_correct_structure():
    """Health endpoint must return status and version"""
    from app.main import app

    client = TestClient(app)

    response = client.get("/api/health")
    data = response.json()

    assert "status" in data
    assert "version" in data
    assert data["status"] == "ok"
    assert isinstance(data["version"], str)


def test_health_endpoint_version_format():
    """Version must follow semantic versioning"""
    from app.main import app

    client = TestClient(app)

    response = client.get("/api/health")
    version = response.json()["version"]

    # Must be in format X.Y.Z
    parts = version.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
