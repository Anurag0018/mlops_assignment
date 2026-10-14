"""
Unit Tests for Model Evaluation & Champion Governance
----------------------------------------------------
Validates metric computation accuracy, champion artifact integrity, and registry metadata.
"""

import json
import pytest
import numpy as np
import pandas as pd
import joblib

from src.common.config import (
    BEST_MODEL_PATH,
    MODEL_REGISTRY_PATH,
    PREPROCESSOR_PATH,
    ALL_FEATURE_COLUMNS,
)
from src.training.evaluate import calculate_metrics


def test_metric_calculation_correctness():
    """Verify precision, recall, f1, and confusion matrix math on known labels."""
    y_true = np.array([1, 1, 0, 0, 1, 0])
    y_pred = np.array([1, 0, 0, 0, 1, 1])
    # TP: 2, FN: 1, FP: 1, TN: 2
    # Precision: 2 / (2 + 1) = 0.6667
    # Recall: 2 / (2 + 1) = 0.6667
    # Accuracy: 4 / 6 = 0.6667
    metrics = calculate_metrics(y_true, y_pred)

    assert metrics["true_positives"] == 2
    assert metrics["false_negatives"] == 1
    assert metrics["false_positives"] == 1
    assert metrics["true_negatives"] == 2
    assert pytest.approx(metrics["precision"], 0.001) == 0.6667
    assert pytest.approx(metrics["recall"], 0.001) == 0.6667
    assert pytest.approx(metrics["accuracy"], 0.001) == 0.6667


def test_champion_model_artifacts_exist():
    """Verify champion model, preprocessor, and registry files exist on disk."""
    assert BEST_MODEL_PATH.exists(), f"Missing champion artifact at {BEST_MODEL_PATH}"
    assert PREPROCESSOR_PATH.exists(), f"Missing preprocessor artifact at {PREPROCESSOR_PATH}"
    assert MODEL_REGISTRY_PATH.exists(), f"Missing model registry at {MODEL_REGISTRY_PATH}"


def test_champion_model_inference():
    """Verify champion model loads cleanly and predicts valid probability distributions."""
    model = joblib.load(BEST_MODEL_PATH)
    preprocessor = joblib.load(PREPROCESSOR_PATH)

    assert hasattr(model, "predict")
    assert hasattr(model, "predict_proba")

    # Mock single-row features
    mock_df = pd.DataFrame([{
        "g1": 12.0, "age": 17, "absences": 4, "attendance_rate": 95.7,
        "studytime": 2, "failures": 0, "school": "GP", "sex": "F",
        "address": "U", "famsize": "GT3", "pstatus": "T", "mjob": "other",
        "fjob": "other", "parent_education": "Secondary Education",
        "study_time_category": "2 to 5 hours", "subject": "Mathematics"
    }])[ALL_FEATURE_COLUMNS]

    X_trans = preprocessor.transform(mock_df)
    preds = model.predict(X_trans)
    probs = model.predict_proba(X_trans)

    assert preds[0] in [0, 1]
    assert 0.0 <= probs[0, 1] <= 1.0
    assert pytest.approx(probs[0, 0] + probs[0, 1], 0.001) == 1.0


def test_model_registry_governance_schema():
    """Verify registry metadata contains complete audit trail and candidate benchmarks."""
    with open(MODEL_REGISTRY_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert "champion_model_name" in meta
    assert "model_version" in meta
    assert "validation_metrics" in meta
    assert "test_metrics" in meta
    assert "candidate_comparisons" in meta

    assert len(meta["candidate_comparisons"]) >= 3
    # Verify primary metric F1 is non-zero
    assert meta["validation_metrics"]["f1"] > 0.50
    assert meta["validation_metrics"]["recall"] > 0.60
