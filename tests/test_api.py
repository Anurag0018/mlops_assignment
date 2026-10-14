"""
Unit and Integration Tests for FastAPI Prediction Service
---------------------------------------------------------
Validates health, model metadata, single prediction, batch prediction,
schema validation errors, and operational metrics.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify health endpoint returns status ok and model loaded."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["model_loaded"] is True
    assert "model_name" in data


def test_model_info_endpoint():
    """Verify model-info endpoint returns champion details and metrics."""
    response = client.get("/model-info")
    assert response.status_code == 200
    data = response.json()
    assert "champion_model_name" in data
    assert "algorithm" in data
    assert "validation_metrics" in data
    assert "test_metrics" in data
    assert data["total_features"] == 16


def test_predict_single_passing_student():
    """High G1, zero failures, high attendance should predict Passing with Low Risk."""
    payload = {
        "g1": 16.0,
        "age": 16,
        "absences": 2,
        "attendance_rate": 97.8,
        "studytime": 3,
        "failures": 0,
        "school": "GP",
        "sex": "F",
        "address": "U",
        "famsize": "GT3",
        "pstatus": "T",
        "mjob": "teacher",
        "fjob": "services",
        "parent_education": "Higher Education",
        "study_time_category": "5 to 10 hours",
        "subject": "Mathematics",
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["prediction"] == 0
    assert data["risk_status"] == "Passing"
    assert data["risk_score"] < 0.35
    assert data["risk_level"] == "Low Risk"
    assert "recommendation" in data


def test_predict_single_at_risk_student():
    """Low G1, multiple past failures, low attendance should predict At-Risk."""
    payload = {
        "g1": 5.0,
        "age": 18,
        "absences": 24,
        "attendance_rate": 74.2,
        "studytime": 1,
        "failures": 3,
        "school": "MS",
        "sex": "M",
        "address": "R",
        "famsize": "LE3",
        "pstatus": "A",
        "mjob": "at_home",
        "fjob": "other",
        "parent_education": "5th to 9th grade",
        "study_time_category": "<2 hours",
        "subject": "Mathematics",
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["prediction"] == 1
    assert data["risk_status"] == "At-Risk"
    assert data["risk_score"] >= 0.50
    assert data["risk_level"] in ["Medium Risk", "High Risk"]


def test_predict_validation_error():
    """Input exceeding grade bound (e.g., G1 = 25 or -5) should return 422 Unprocessable Entity."""
    invalid_payload = {
        "g1": 25.0,  # Max is 20
        "age": 17,
        "absences": 4,
        "attendance_rate": 95.0,
        "studytime": 2,
        "failures": 0,
    }
    response = client.post("/predict", json=invalid_payload)
    assert response.status_code == 422


def test_predict_batch():
    """Verify batch prediction endpoint aggregates roster correctly."""
    batch_payload = {
        "students": [
            {
                "g1": 15.0,
                "age": 17,
                "absences": 2,
                "attendance_rate": 98.0,
                "studytime": 3,
                "failures": 0,
                "school": "GP",
                "sex": "F",
                "address": "U",
                "famsize": "GT3",
                "pstatus": "T",
                "mjob": "services",
                "fjob": "services",
                "parent_education": "Secondary Education",
                "study_time_category": "5 to 10 hours",
                "subject": "Mathematics",
            },
            {
                "g1": 4.0,
                "age": 18,
                "absences": 20,
                "attendance_rate": 78.0,
                "studytime": 1,
                "failures": 2,
                "school": "MS",
                "sex": "M",
                "address": "R",
                "famsize": "LE3",
                "pstatus": "A",
                "mjob": "other",
                "fjob": "other",
                "parent_education": "Primary (4th grade)",
                "study_time_category": "<2 hours",
                "subject": "Portuguese",
            }
        ]
    }
    response = client.post("/predict/batch", json=batch_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_students"] == 2
    assert len(data["predictions"]) == 2
    assert data["at_risk_count"] + data["passing_count"] == 2


def test_metrics_endpoint():
    """Operational metrics endpoint returns non-zero predictions after queries."""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["model_loaded"] is True
    assert data["total_predictions"] > 0
    assert "average_latency_ms" in data
