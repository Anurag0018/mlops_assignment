"""
Unit Tests for Data Quality Validation and Feature Drift Detection
------------------------------------------------------------------
Validates schema validation rules, boundary checks, and Population Stability Index (PSI).
"""

import pytest
import numpy as np
import pandas as pd

from src.monitoring.data_quality import DataQualityValidator
from src.monitoring.drift import (
    calculate_numerical_psi,
    calculate_categorical_psi,
    DriftDetector,
)


def test_data_quality_validator_valid_record():
    """Verify validator approves a fully compliant record."""
    validator = DataQualityValidator()
    valid_record = {
        "g1": 12.0, "age": 17, "absences": 4, "attendance_rate": 95.7,
        "studytime": 2, "failures": 0, "school": "GP", "sex": "F",
        "address": "U", "famsize": "GT3", "pstatus": "T", "mjob": "services",
        "fjob": "services", "parent_education": "Secondary Education",
        "study_time_category": "2 to 5 hours", "subject": "Mathematics"
    }
    is_valid, issues = validator.validate_record(valid_record)
    assert is_valid is True
    assert len(issues) == 0


def test_data_quality_validator_out_of_bounds():
    """Verify validator flags invalid grade bounds and missing features."""
    validator = DataQualityValidator()
    invalid_record = {
        "g1": 25.0,  # Exceeds max 20
        "age": 17,
        "absences": 4,
        "attendance_rate": 95.7,
        "studytime": 2,
        "failures": 0,
        # Missing remaining features
    }
    is_valid, issues = validator.validate_record(invalid_record)
    assert is_valid is False
    assert any("Missing required feature" in iss for iss in issues)


def test_numerical_psi_identical_distribution():
    """Verify PSI is approximately zero when actual matches reference."""
    np.random.seed(42)
    ref = np.random.normal(loc=11.0, scale=3.0, size=1000)
    curr = ref.copy()

    psi = calculate_numerical_psi(ref, curr)
    assert psi < 0.05, f"Expected near-zero PSI for identical distribution, got {psi}"


def test_numerical_psi_shifted_distribution():
    """Verify PSI detects significant shift when distribution mean moves."""
    np.random.seed(42)
    ref = np.random.normal(loc=12.0, scale=2.5, size=1000)
    curr = np.random.normal(loc=6.0, scale=2.5, size=1000)  # Severe degradation in marks

    psi = calculate_numerical_psi(ref, curr)
    assert psi > 0.20, f"Expected critical drift (PSI >= 0.20) for shifted mean, got {psi}"


def test_categorical_psi_frequency_shift():
    """Verify categorical PSI catches shifts in category frequency."""
    ref = pd.Series(["Mathematics"] * 800 + ["Portuguese"] * 200)
    curr = pd.Series(["Mathematics"] * 100 + ["Portuguese"] * 900)  # Inverted subject cohort

    psi = calculate_categorical_psi(ref, curr)
    assert psi > 0.20


def test_drift_detector_end_to_end():
    """Verify DriftDetector produces structured report with overall drift status."""
    detector = DriftDetector()
    if detector.reference_df is not None:
        report = detector.evaluate_drift(detector.reference_df)
        assert report["status"] == "evaluated"
        assert report["overall_drift_status"] == "Stable (No Drift)"
        assert report["overall_drift_detected"] is False
        assert "feature_psi" in report
