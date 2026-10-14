"""
MLflow Tracking Utility
-----------------------
Configures local MLflow experiment tracking, runs, metrics,
and artifact logging for reproducible model governance.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import mlflow
import mlflow.sklearn
import mlflow.xgboost

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.common.config import (
    MLFLOW_TRACKING_URI,
    MLFLOW_EXPERIMENT_NAME,
    MODELS_DIR,
)

logger = logging.getLogger("mlflow_utils")


def setup_mlflow(
    experiment_name: str = MLFLOW_EXPERIMENT_NAME,
    tracking_uri: Optional[str] = None
) -> str:
    """Set tracking URI and experiment name in MLflow."""
    uri = tracking_uri or MLFLOW_TRACKING_URI
    mlflow.set_tracking_uri(uri)
    logger.info(f"MLflow Tracking URI set to: {uri}")

    # Ensure SQLite experiment artifact_location points to local filesystem if invalid
    if uri.startswith("sqlite:///"):
        try:
            db_path = uri.replace("sqlite:///", "")
            if os.path.exists(db_path):
                import sqlite3
                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                for row in c.execute("SELECT experiment_id, artifact_location FROM experiments").fetchall():
                    exp_id, art_loc = row[0], row[1]
                    if art_loc and art_loc.startswith("file:"):
                        raw_path = art_loc[5:]
                        drive = os.path.splitdrive(raw_path)[0]
                        if (drive and not os.path.exists(drive + "\\")) or not os.path.exists(os.path.dirname(raw_path)):
                            local_art = f"file:{(PROJECT_ROOT / 'mlruns' / str(exp_id)).as_posix()}"
                            c.execute("UPDATE experiments SET artifact_location = ? WHERE experiment_id = ?", (local_art, exp_id))
                conn.commit()
                conn.close()
        except Exception as e:
            logger.debug(f"MLflow artifact location check: {e}")

    mlflow.set_experiment(experiment_name)
    logger.info(f"MLflow Experiment set to: {experiment_name}")
    return uri


def log_model_run(
    model_name: str,
    model: Any,
    params: Dict[str, Any],
    train_metrics: Dict[str, float],
    val_metrics: Dict[str, float],
    test_metrics: Dict[str, float],
    artifact_paths: Optional[Dict[str, str]] = None,
    tags: Optional[Dict[str, str]] = None,
) -> str:
    """
    Log a complete model evaluation run to MLflow.
    Returns run_id.
    """
    with mlflow.start_run(run_name=model_name) as run:
        run_id = run.info.run_id
        logger.info(f"Starting MLflow Run [{model_name}] (run_id: {run_id})")

        # 1. Tags
        mlflow.set_tag("model_family", model.__class__.__name__)
        mlflow.set_tag("pipeline", "student_academic_risk")
        if tags:
            for k, v in tags.items():
                mlflow.set_tag(k, str(v))

        # 2. Parameters
        mlflow.log_params(params)

        # 3. Metrics (prefixing split to maintain clean separation)
        for k, v in train_metrics.items():
            mlflow.log_metric(f"train_{k}", float(v))

        for k, v in val_metrics.items():
            mlflow.log_metric(f"val_{k}", float(v))

        for k, v in test_metrics.items():
            mlflow.log_metric(f"test_{k}", float(v))

        # 4. Artifact plots (confusion matrix, ROC, PR curve)
        if artifact_paths:
            for artifact_name, file_path in artifact_paths.items():
                if file_path and Path(file_path).exists():
                    mlflow.log_artifact(file_path, artifact_path="evaluation_plots")
                    logger.info(f"Logged artifact {artifact_name}: {file_path}")

        # 5. Model artifact
        try:
            if "xgb" in model.__class__.__name__.lower():
                mlflow.xgboost.log_model(model, artifact_path="model")
            else:
                mlflow.sklearn.log_model(model, artifact_path="model")
            logger.info(f"Successfully logged model artifact for {model_name}")
        except Exception as e:
            logger.warning(f"Could not log native MLflow model format ({e}). Proceeding.")

        logger.info(f"MLflow Run {run_id} completed successfully.")
        return run_id
