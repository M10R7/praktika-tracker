"""
Tests for healthcheck and root endpoints.
"""

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Praktika-Tracker API"
    assert data["status"] == "operational"
    assert data["version"] == "0.1.0"


def test_healthcheck_endpoint():
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "praktika-tracker"
    assert "environment" in data
