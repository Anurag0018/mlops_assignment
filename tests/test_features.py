"""
Unit Tests for Feature Engineering & Preprocessing Pipeline
------------------------------------------------------------
Validates leak-free feature isolation, fingerprinting, and transformation pipelines.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from src.common.config import (
    ALL_FEATURE_COLUMNS,
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    TARGET_COLUMN,
    PREPROCESSOR_PATH,
    STUDENT_ANALYTICS_CSV,
)
from src.features.build_features import (
    compute_dataset_fingerprint,
    create_preprocessor,
    prepare_data_and_features,
)


def test_no_target_leakage_in_features():
    """Verify that outcome variables and future grades are strictly excluded."""
    leakage_columns = {
        "g2", "g3", "final_grade", "average_grade", "pass_fail",
        "performance_category", "grade_improvement", "risk_status", "student_id"
    }
    for col in ALL_FEATURE_COLUMNS:
        assert col not in leakage_columns, f"Target leakage detected! Feature '{col}' reveals future outcomes."


def test_dataset_fingerprinting():
    """Verify dataset fingerprint computes checksum, row count, and class proportions."""
    assert STUDENT_ANALYTICS_CSV.exists()
    df = pd.read_csv(STUDENT_ANALYTICS_CSV)
    fp = compute_dataset_fingerprint(df, STUDENT_ANALYTICS_CSV)

    assert fp["total_records"] == len(df)
    assert len(fp["sha256_checksum"]) == 64
    assert fp["class_distribution"]["0_passing"] + fp["class_distribution"]["1_at_risk"] == len(df)


def test_preprocessor_fitting_and_transformation():
    """Verify preprocessor transforms categorical and numerical features into consistent dimensions."""
    df = pd.read_csv(STUDENT_ANALYTICS_CSV)
    X = df[ALL_FEATURE_COLUMNS]

    preprocessor = create_preprocessor()
    X_trans = preprocessor.fit_transform(X)

    # 6 numerical features scaled + 31 one-hot encoded categories = 37 transformed features
    assert X_trans.shape[0] == len(df)
    assert X_trans.shape[1] == 37
    assert not np.isnan(X_trans).any()


def test_stratified_data_split_integrity():
    """Verify train/val/test splits maintain non-zero samples and consistent class ratios."""
    (
        X_train, X_val, X_test,
        y_train, y_val, y_test,
        preprocessor, metadata
    ) = prepare_data_and_features()

    total_samples = len(y_train) + len(y_val) + len(y_test)
    assert total_samples == 1028

    # Check class imbalance representation across all splits (~21.6% positive class)
    train_risk_rate = np.mean(y_train)
    val_risk_rate = np.mean(y_val)
    test_risk_rate = np.mean(y_test)

    assert 0.18 <= train_risk_rate <= 0.25
    assert 0.18 <= val_risk_rate <= 0.25
    assert 0.18 <= test_risk_rate <= 0.25
