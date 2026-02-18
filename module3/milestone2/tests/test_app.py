"""
Unit tests for ML inference service (Milestone 2).
Run from repo root or module3/milestone2: pytest module3/milestone2/tests/ -v
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure app package is on path when running from module3/milestone2 or repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import after path fix; model must exist for lifespan to succeed
@pytest.fixture(scope="module")
def client():
    from app.app import app
    return TestClient(app)


def test_health(client: TestClient):
    """Health endpoint returns 200 and status ok."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_root_redirects_to_docs(client: TestClient):
    """Root redirects to /docs."""
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (307, 308)
    assert "docs" in (r.headers.get("location") or "")


def test_predict_input_output_format(client: TestClient):
    """Predict accepts valid JSON and returns predicted_class and label."""
    payload = {
        "sepal_length": 5.1,
        "sepal_width": 3.5,
        "petal_length": 1.4,
        "petal_width": 0.2,
    }
    r = client.post("/predict", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "predicted_class" in data
    assert "label" in data
    assert data["predicted_class"] in (0, 1, 2)
    assert data["label"] in ("setosa", "versicolor", "virginica")


def test_predict_validation_error(client: TestClient):
    """Invalid input (out of range) returns 422."""
    payload = {
        "sepal_length": -1,
        "sepal_width": 3.5,
        "petal_length": 1.4,
        "petal_width": 0.2,
    }
    r = client.post("/predict", json=payload)
    assert r.status_code == 422


def test_predict_missing_field(client: TestClient):
    """Missing required field returns 422."""
    r = client.post("/predict", json={"sepal_length": 5.0})
    assert r.status_code == 422
