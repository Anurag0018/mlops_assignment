"""
Model Training and MLflow Experiment Tracking Pipeline
------------------------------------------------------
Trains, compares, and evaluates multiple candidate models:
1. Logistic Regression (Baseline with balanced weights)
2. Random Forest Classifier (Ensemble tree-based)
3. XGBoost Classifier (Gradient boosted trees)

Selects the Champion model based on validation F1-score & Recall,
logs all runs and artifacts to MLflow, and saves the registered
champion model to models/best_model.joblib.
"""

import sys
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Tuple, List
import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.common.config import (
    BEST_MODEL_PATH,
    MODEL_REGISTRY_PATH,
    RANDOM_STATE,
    MODELS_DIR,
    REPORTS_DIR,
)
from src.features.build_features import prepare_data_and_features
from src.training.evaluate import (
    calculate_metrics,
    plot_confusion_matrix_artifact,
    plot_roc_curve_artifact,
    plot_pr_curve_artifact,
)
from src.tracking.mlflow_utils import setup_mlflow, log_model_run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("train")


def train_and_evaluate_model(
    name: str,
    model: Any,
    params: Dict[str, Any],
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
) -> Dict[str, Any]:
    """Train single model, compute metrics across splits, generate evaluation plots."""
    logger.info(f"--- Training {name} ---")
    model.fit(X_train, y_train)

    # Predictions & probabilities for Train
    train_pred = model.predict(X_train)
    train_prob = model.predict_proba(X_train)[:, 1] if hasattr(model, "predict_proba") else None
    train_metrics = calculate_metrics(y_train, train_pred, train_prob)

    # Predictions & probabilities for Validation
    val_pred = model.predict(X_val)
    val_prob = model.predict_proba(X_val)[:, 1] if hasattr(model, "predict_proba") else None
    val_metrics = calculate_metrics(y_val, val_pred, val_prob)

    # Predictions & probabilities for Test (strictly for unbiased final check)
    test_pred = model.predict(X_test)
    test_prob = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else None
    test_metrics = calculate_metrics(y_test, test_pred, test_prob)

    logger.info(
        f"[{name}] Val Metrics -> Acc: {val_metrics['accuracy']:.4f}, "
        f"Precision: {val_metrics['precision']:.4f}, Recall: {val_metrics['recall']:.4f}, "
        f"F1: {val_metrics['f1']:.4f}, ROC-AUC: {val_metrics.get('roc_auc', 0):.4f}"
    )

    # Generate evaluation plots using test split for final audit
    cm_path = plot_confusion_matrix_artifact(y_test, test_pred, name)
    roc_path = plot_roc_curve_artifact(y_test, test_prob, name) if test_prob is not None else None
    pr_path = plot_pr_curve_artifact(y_test, test_prob, name) if test_prob is not None else None

    artifact_paths = {"confusion_matrix": str(cm_path)}
    if roc_path:
        artifact_paths["roc_curve"] = str(roc_path)
    if pr_path:
        artifact_paths["pr_curve"] = str(pr_path)

    # Log to MLflow
    run_id = log_model_run(
        model_name=name,
        model=model,
        params=params,
        train_metrics=train_metrics,
        val_metrics=val_metrics,
        test_metrics=test_metrics,
        artifact_paths=artifact_paths,
    )

    return {
        "name": name,
        "model": model,
        "params": params,
        "run_id": run_id,
        "train_metrics": train_metrics,
        "val_metrics": val_metrics,
        "test_metrics": test_metrics,
        "artifact_paths": artifact_paths,
    }


def run_training_pipeline() -> Dict[str, Any]:
    """Execute complete multi-model training, MLflow tracking, and champion registration."""
    logger.info("Initializing MLflow Tracking...")
    setup_mlflow()

    logger.info("Preparing data splits and features...")
    (
        X_train, X_val, X_test,
        y_train, y_val, y_test,
        preprocessor, metadata
    ) = prepare_data_and_features()

    # Calculate class imbalance ratio for XGBoost scale_pos_weight
    neg_count = int(np.sum(y_train == 0))
    pos_count = int(np.sum(y_train == 1))
    scale_pos = round(float(neg_count) / max(1, pos_count), 2)

    # Define candidate models
    candidates = [
        (
            "Logistic Regression (Baseline)",
            LogisticRegression(
                C=1.0,
                solver="lbfgs",
                max_iter=1000,
                class_weight="balanced",
                random_state=RANDOM_STATE,
            ),
            {
                "model_type": "LogisticRegression",
                "C": 1.0,
                "solver": "lbfgs",
                "class_weight": "balanced",
                "random_state": RANDOM_STATE,
            }
        ),
        (
            "Random Forest Classifier",
            RandomForestClassifier(
                n_estimators=150,
                max_depth=8,
                min_samples_split=4,
                class_weight="balanced",
                random_state=RANDOM_STATE,
                n_jobs=-1,
            ),
            {
                "model_type": "RandomForestClassifier",
                "n_estimators": 150,
                "max_depth": 8,
                "min_samples_split": 4,
                "class_weight": "balanced",
                "random_state": RANDOM_STATE,
            }
        ),
        (
            "XGBoost Classifier",
            xgb.XGBClassifier(
                n_estimators=120,
                max_depth=4,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                scale_pos_weight=scale_pos,
                eval_metric="logloss",
                random_state=RANDOM_STATE,
                n_jobs=-1,
            ),
            {
                "model_type": "XGBClassifier",
                "n_estimators": 120,
                "max_depth": 4,
                "learning_rate": 0.05,
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "scale_pos_weight": scale_pos,
                "random_state": RANDOM_STATE,
            }
        ),
    ]

    results: List[Dict[str, Any]] = []
    for name, model_inst, params in candidates:
        res = train_and_evaluate_model(
            name=name,
            model=model_inst,
            params=params,
            X_train=X_train,
            y_train=y_train,
            X_val=X_val,
            y_val=y_val,
            X_test=X_test,
            y_test=y_test,
        )
        results.append(res)

    # Champion selection:
    # Academic risk detection requires high Recall (don't miss failing students)
    # while maintaining high Precision (don't overburden advisors with false alerts).
    # Thus, validation F1-score is our primary ranking metric, with ROC-AUC as tie-breaker.
    best_candidate = max(
        results,
        key=lambda r: (r["val_metrics"]["f1"], r["val_metrics"].get("roc_auc", 0))
    )

    logger.info("=" * 60)
    logger.info(f"CHAMPION MODEL SELECTED: {best_candidate['name']}")
    logger.info(
        f"Validation F1: {best_candidate['val_metrics']['f1']:.4f} | "
        f"Validation Recall: {best_candidate['val_metrics']['recall']:.4f} | "
        f"Validation ROC-AUC: {best_candidate['val_metrics'].get('roc_auc', 0):.4f}"
    )
    logger.info(
        f"Test F1: {best_candidate['test_metrics']['f1']:.4f} | "
        f"Test Recall: {best_candidate['test_metrics']['recall']:.4f} | "
        f"Test ROC-AUC: {best_candidate['test_metrics'].get('roc_auc', 0):.4f}"
    )
    logger.info("=" * 60)

    # Save Champion Model Artifact
    joblib.dump(best_candidate["model"], BEST_MODEL_PATH)
    logger.info(f"Saved Champion model artifact to {BEST_MODEL_PATH}")

    # Build comparison summary for registry metadata
    comparison_summary = []
    for r in results:
        comparison_summary.append({
            "model_name": r["name"],
            "run_id": r["run_id"],
            "val_f1": r["val_metrics"]["f1"],
            "val_recall": r["val_metrics"]["recall"],
            "val_precision": r["val_metrics"]["precision"],
            "val_roc_auc": r["val_metrics"].get("roc_auc", 0),
            "test_f1": r["test_metrics"]["f1"],
            "test_recall": r["test_metrics"]["recall"],
            "test_precision": r["test_metrics"]["precision"],
            "test_roc_auc": r["test_metrics"].get("roc_auc", 0),
        })

    registry_metadata = {
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "champion_model_name": best_candidate["name"],
        "champion_run_id": best_candidate["run_id"],
        "algorithm": best_candidate["model"].__class__.__name__,
        "model_version": "v1.0.0",
        "primary_metric": "f1_score",
        "selection_rationale": (
            "Selected based on highest validation F1-score to maximize coverage of at-risk students "
            "without generating excessive false intervention alerts."
        ),
        "validation_metrics": best_candidate["val_metrics"],
        "test_metrics": best_candidate["test_metrics"],
        "hyperparameters": best_candidate["params"],
        "candidate_comparisons": comparison_summary,
        "artifact_path": str(BEST_MODEL_PATH),
    }

    with open(MODEL_REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry_metadata, f, indent=2)
    logger.info(f"Saved Model Registry metadata to {MODEL_REGISTRY_PATH}")

    return registry_metadata


if __name__ == "__main__":
    run_training_pipeline()
