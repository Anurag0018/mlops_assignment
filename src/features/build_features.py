"""
Feature Engineering & Preprocessing Module
------------------------------------------
Constructs leak-free feature pipelines, computes target labels,
fits transformers strictly on training splits, and exports reference
data for drift monitoring and inference consistency.
"""

import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import Tuple, Dict, Any, List
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.common.config import (
    STUDENT_ANALYTICS_CSV,
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    ALL_FEATURE_COLUMNS,
    TARGET_COLUMN,
    PREPROCESSOR_PATH,
    FEATURE_METADATA_PATH,
    REFERENCE_FEATURES_PATH,
    DATASET_FINGERPRINT_PATH,
    RANDOM_STATE,
    TRAIN_RATIO,
    VAL_RATIO,
    TEST_RATIO,
    MODELS_DIR,
    REFERENCE_DATA_DIR
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("features")


def compute_dataset_fingerprint(df: pd.DataFrame, file_path: Path) -> Dict[str, Any]:
    """Calculate SHA-256 fingerprint, row count, and class distribution metadata."""
    content_bytes = file_path.read_bytes()
    sha256_hash = hashlib.sha256(content_bytes).hexdigest()

    # Generate target for class distribution audit
    target_series = (df["final_grade"] < 10).astype(int)
    class_counts = target_series.value_counts().to_dict()
    total = len(target_series)

    fingerprint = {
        "dataset_name": file_path.name,
        "sha256_checksum": sha256_hash,
        "total_records": int(total),
        "total_columns": int(len(df.columns)),
        "target_definition": "failure_risk = 1 if final_grade (G3) < 10 else 0",
        "class_distribution": {
            "0_passing": int(class_counts.get(0, 0)),
            "1_at_risk": int(class_counts.get(1, 0)),
        },
        "class_proportions": {
            "0_passing_pct": round(float(class_counts.get(0, 0)) / total * 100, 2),
            "1_at_risk_pct": round(float(class_counts.get(1, 0)) / total * 100, 2),
        },
        "all_input_features": ALL_FEATURE_COLUMNS,
        "numerical_features": NUMERICAL_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
    }
    return fingerprint


def create_preprocessor() -> ColumnTransformer:
    """Build scikit-learn ColumnTransformer for numerical and categorical features."""
    num_pipeline = StandardScaler()
    cat_pipeline = OneHotEncoder(handle_unknown="ignore", sparse_output=False)

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", num_pipeline, NUMERICAL_FEATURES),
            ("cat", cat_pipeline, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )
    return preprocessor


def extract_feature_metadata(df: pd.DataFrame, preprocessor: ColumnTransformer) -> Dict[str, Any]:
    """Extract and document schema metadata for runtime validation."""
    num_meta = {}
    for col in NUMERICAL_FEATURES:
        num_meta[col] = {
            "type": "float",
            "min": float(df[col].min()),
            "max": float(df[col].max()),
            "mean": round(float(df[col].mean()), 2),
        }

    cat_meta = {}
    for col in CATEGORICAL_FEATURES:
        cat_meta[col] = {
            "type": "categorical",
            "allowed_categories": sorted(df[col].astype(str).unique().tolist()),
        }

    # Extract transformed feature names
    cat_encoder = preprocessor.named_transformers_["cat"]
    encoded_cat_names = cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES).tolist()
    transformed_feature_names = NUMERICAL_FEATURES + encoded_cat_names

    metadata = {
        "target": TARGET_COLUMN,
        "input_features": ALL_FEATURE_COLUMNS,
        "numerical_features": num_meta,
        "categorical_features": cat_meta,
        "transformed_feature_names": transformed_feature_names,
        "transformed_feature_count": len(transformed_feature_names),
    }
    return metadata


def prepare_data_and_features() -> Tuple[
    np.ndarray, np.ndarray, np.ndarray,
    np.ndarray, np.ndarray, np.ndarray,
    ColumnTransformer, Dict[str, Any]
]:
    """
    Complete feature engineering pipeline:
    1. Loads student_analytics.csv
    2. Constructs leak-free target variable (failure_risk)
    3. Generates dataset fingerprint
    4. Performs stratified Train/Val/Test split (70/15/15)
    5. Fits preprocessor on Train set only
    6. Saves preprocessor, metadata, and reference baseline
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    REFERENCE_DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not STUDENT_ANALYTICS_CSV.exists():
        raise FileNotFoundError(f"Source analytics mart missing at {STUDENT_ANALYTICS_CSV}")

    df = pd.read_csv(STUDENT_ANALYTICS_CSV)
    logger.info(f"Loaded {len(df)} records from {STUDENT_ANALYTICS_CSV.name}")

    # Generate dataset fingerprint
    fingerprint = compute_dataset_fingerprint(df, STUDENT_ANALYTICS_CSV)
    with open(DATASET_FINGERPRINT_PATH, "w", encoding="utf-8") as f:
        json.dump(fingerprint, f, indent=2)
    logger.info(f"Saved dataset fingerprint to {DATASET_FINGERPRINT_PATH}")

    # Define target variable (1 = At-Risk, 0 = Passing)
    y = (df["final_grade"] < 10).astype(int).values

    # Select only prediction-time features (NO target leakage)
    X_df = df[ALL_FEATURE_COLUMNS].copy()

    # Stratified Train/Val/Test split: 70% Train, 30% Temp -> 15% Val, 15% Test
    X_train_df, X_temp_df, y_train, y_temp = train_test_split(
        X_df, y,
        test_size=(VAL_RATIO + TEST_RATIO),
        stratify=y,
        random_state=RANDOM_STATE
    )

    X_val_df, X_test_df, y_val, y_test = train_test_split(
        X_temp_df, y_temp,
        test_size=0.5,
        stratify=y_temp,
        random_state=RANDOM_STATE
    )

    logger.info(
        f"Data Splits: Train={len(X_train_df)} ({y_train.sum()} at-risk), "
        f"Val={len(X_val_df)} ({y_val.sum()} at-risk), "
        f"Test={len(X_test_df)} ({y_test.sum()} at-risk)"
    )

    # Save reference baseline (training features before transformation) for drift detection
    X_train_df.to_parquet(REFERENCE_FEATURES_PATH, index=False)
    logger.info(f"Saved reference training features for drift monitoring to {REFERENCE_FEATURES_PATH}")

    # Fit preprocessor strictly on training features
    preprocessor = create_preprocessor()
    X_train_trans = preprocessor.fit_transform(X_train_df)
    X_val_trans = preprocessor.transform(X_val_df)
    X_test_trans = preprocessor.transform(X_test_df)

    # Save preprocessor artifact
    joblib.dump(preprocessor, PREPROCESSOR_PATH)
    logger.info(f"Saved fitted preprocessor artifact to {PREPROCESSOR_PATH}")

    # Save feature metadata
    metadata = extract_feature_metadata(X_train_df, preprocessor)
    with open(FEATURE_METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved feature metadata schema to {FEATURE_METADATA_PATH}")

    return (
        X_train_trans, X_val_trans, X_test_trans,
        y_train, y_val, y_test,
        preprocessor, metadata
    )


def transform_inference_input(input_df: pd.DataFrame) -> np.ndarray:
    """Transform inference dataframe into preprocessed feature array using saved preprocessor."""
    if not PREPROCESSOR_PATH.exists():
        raise FileNotFoundError(f"Fitted preprocessor not found at {PREPROCESSOR_PATH}. Run build_features first.")
    preprocessor = joblib.load(PREPROCESSOR_PATH)

    # Ensure all required columns are present
    missing = [c for c in ALL_FEATURE_COLUMNS if c not in input_df.columns]
    if missing:
        raise ValueError(f"Inference input missing required features: {missing}")

    return preprocessor.transform(input_df[ALL_FEATURE_COLUMNS])


if __name__ == "__main__":
    logger.info("Executing Feature Engineering Pipeline...")
    (
        X_train, X_val, X_test,
        y_train, y_val, y_test,
        preprocessor, meta
    ) = prepare_data_and_features()

    print("\n" + "=" * 60)
    print("FEATURE ENGINEERING COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print(f"• Transformed Feature Dimensions: {X_train.shape[1]}")
    print(f"• Training Set Samples: {X_train.shape[0]}")
    print(f"• Validation Set Samples: {X_val.shape[0]}")
    print(f"• Test Set Samples: {X_test.shape[0]}")
    print(f"• Saved Artifact: {PREPROCESSOR_PATH}")
    print(f"• Saved Metadata: {FEATURE_METADATA_PATH}")
    print("=" * 60 + "\n")
