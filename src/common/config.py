"""
Central Configuration Module for MLOps Pipeline
------------------------------------------------
Provides unified access to paths, target variables, model parameters,
and environment settings across the feature, training, API, and monitoring modules.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Base project paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
STAGING_DATA_DIR = DATA_DIR / "staging"
CLEANED_DATA_DIR = DATA_DIR / "cleaned"
REFERENCE_DATA_DIR = DATA_DIR / "reference"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"

# Dataset paths
STUDENT_ANALYTICS_CSV = CLEANED_DATA_DIR / "student_analytics.csv"
DATASET_FINGERPRINT_PATH = REFERENCE_DATA_DIR / "dataset_fingerprint.json"
REFERENCE_FEATURES_PATH = REFERENCE_DATA_DIR / "reference_features.parquet"

# Target variable definition
# 1 = At-Risk / Failing (G3 < 10)
# 0 = Passing (G3 >= 10)
TARGET_COLUMN = "failure_risk"

# Features available at prediction time (NO target leakage: excluding G3, G2, averages, post-eval outcomes)
NUMERICAL_FEATURES = [
    "g1",
    "age",
    "absences",
    "attendance_rate",
    "studytime",
    "failures",
]

CATEGORICAL_FEATURES = [
    "school",
    "sex",
    "address",
    "famsize",
    "pstatus",
    "mjob",
    "fjob",
    "parent_education",
    "study_time_category",
    "subject",
]

ALL_FEATURE_COLUMNS = NUMERICAL_FEATURES + CATEGORICAL_FEATURES

# Model Artifact Paths
PREPROCESSOR_PATH = MODELS_DIR / "preprocessor.joblib"
BEST_MODEL_PATH = MODELS_DIR / "best_model.joblib"
MODEL_REGISTRY_PATH = MODELS_DIR / "model_registry.json"
FEATURE_METADATA_PATH = MODELS_DIR / "feature_metadata.json"

# MLflow Settings
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", f"sqlite:///{BASE_DIR / 'mlruns.db'}")
MLFLOW_EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "student_performance_mlops")

# API Settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Training hyperparameters & settings
RANDOM_STATE = 42
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

# Drift Monitoring Thresholds (Population Stability Index - PSI)
DRIFT_PSI_THRESHOLD_WARNING = 0.10
DRIFT_PSI_THRESHOLD_CRITICAL = 0.20
PSI_THRESHOLD_STABLE = 0.10
PSI_THRESHOLD_MODERATE = 0.20

# Retraining Promotion Criteria
MIN_F1_SCORE_THRESHOLD = 0.65
MIN_RECALL_THRESHOLD = 0.70
