"""
Inference and Model Service Layer
---------------------------------
Manages preprocessor and model lifecycle, executes leak-free inference,
generates academic risk tiers and recommendations, and monitors request latency.
"""

import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
import joblib

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.common.config import (
    BEST_MODEL_PATH,
    PREPROCESSOR_PATH,
    MODEL_REGISTRY_PATH,
    FEATURE_METADATA_PATH,
    ALL_FEATURE_COLUMNS,
)
from api.schemas import (
    StudentFeatures,
    PredictionResponse,
    BatchPredictionResponse,
)

logger = logging.getLogger("api.services")


class ModelService:
    """Encapsulates model artifact loading, transformation, and prediction inference."""

    _instance: Optional["ModelService"] = None

    def __init__(self):
        self.model = None
        self.preprocessor = None
        self.registry_info = {}
        self.feature_metadata = {}
        self.is_loaded = False

        # In-memory monitoring metrics
        self.total_predictions = 0
        self.at_risk_count = 0
        self.passing_count = 0
        self.total_latency_ms = 0.0

        self.load_artifacts()

    @classmethod
    def get_instance(cls) -> "ModelService":
        if cls._instance is None:
            cls._instance = ModelService()
        return cls._instance

    def load_artifacts(self) -> None:
        """Load trained preprocessor, model artifact, and governance metadata."""
        try:
            if not PREPROCESSOR_PATH.exists():
                raise FileNotFoundError(f"Missing preprocessor at {PREPROCESSOR_PATH}")
            if not BEST_MODEL_PATH.exists():
                raise FileNotFoundError(f"Missing best model at {BEST_MODEL_PATH}")

            self.preprocessor = joblib.load(PREPROCESSOR_PATH)
            self.model = joblib.load(BEST_MODEL_PATH)

            if MODEL_REGISTRY_PATH.exists():
                with open(MODEL_REGISTRY_PATH, "r", encoding="utf-8") as f:
                    self.registry_info = json.load(f)

            if FEATURE_METADATA_PATH.exists():
                with open(FEATURE_METADATA_PATH, "r", encoding="utf-8") as f:
                    self.feature_metadata = json.load(f)

            self.is_loaded = True
            logger.info("Successfully loaded champion model and preprocessor artifacts.")
        except Exception as e:
            logger.error(f"Failed to load model artifacts: {e}")
            self.is_loaded = False

    def _determine_risk_tier(self, risk_score: float) -> Tuple[str, str]:
        """Categorize failure risk into actionable advisory tiers."""
        if risk_score >= 0.65:
            return (
                "High Risk",
                "High academic failure risk detected. Immediate advisor counseling and mandatory tutoring required."
            )
        elif risk_score >= 0.35:
            return (
                "Medium Risk",
                "Moderate academic failure risk. Recommend bi-weekly progress review and homework check-in."
            )
        else:
            return (
                "Low Risk",
                "Student is on track to pass. Continue standard curriculum pacing and positive reinforcement."
            )

    def predict_single(self, features: StudentFeatures) -> PredictionResponse:
        """Execute single-record prediction with latency and metric tracking."""
        if not self.is_loaded:
            raise RuntimeError("Model service is not loaded.")

        start_time = time.perf_counter()

        # Convert to DataFrame ensuring strictly identical feature ordering
        feature_dict = features.model_dump()
        df = pd.DataFrame([feature_dict])[ALL_FEATURE_COLUMNS]

        # Transform using training preprocessor
        X_trans = self.preprocessor.transform(df)

        # Infer class & risk probability
        pred_class = int(self.model.predict(X_trans)[0])
        if hasattr(self.model, "predict_proba"):
            risk_prob = float(self.model.predict_proba(X_trans)[0, 1])
        else:
            risk_prob = float(pred_class)

        risk_tier, recommendation = self._determine_risk_tier(risk_prob)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Update in-memory service metrics
        self.total_predictions += 1
        if pred_class == 1:
            self.at_risk_count += 1
        else:
            self.passing_count += 1
        self.total_latency_ms += elapsed_ms

        model_name = self.registry_info.get("champion_model_name", "AcademicRiskClassifier")
        model_ver = self.registry_info.get("model_version", "v1.0.0")

        return PredictionResponse(
            prediction=pred_class,
            risk_status="At-Risk" if pred_class == 1 else "Passing",
            risk_score=round(risk_prob, 4),
            risk_level=risk_tier,
            recommendation=recommendation,
            model_name=model_name,
            model_version=model_ver,
        )

    def predict_batch(self, students: List[StudentFeatures]) -> BatchPredictionResponse:
        """Vectorized batch prediction for multi-student rosters."""
        if not self.is_loaded:
            raise RuntimeError("Model service is not loaded.")

        start_time = time.perf_counter()

        # Convert records to DataFrame
        records = [s.model_dump() for s in students]
        df = pd.DataFrame(records)[ALL_FEATURE_COLUMNS]

        # Transform all rows at once
        X_trans = self.preprocessor.transform(df)

        preds = self.model.predict(X_trans)
        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(X_trans)[:, 1]
        else:
            probs = preds.astype(float)

        responses: List[PredictionResponse] = []
        model_name = self.registry_info.get("champion_model_name", "AcademicRiskClassifier")
        model_ver = self.registry_info.get("model_version", "v1.0.0")

        at_risk = 0
        passing = 0

        for pred, prob in zip(preds, probs):
            p_class = int(pred)
            p_score = float(prob)
            if p_class == 1:
                at_risk += 1
            else:
                passing += 1

            tier, rec = self._determine_risk_tier(p_score)
            responses.append(
                PredictionResponse(
                    prediction=p_class,
                    risk_status="At-Risk" if p_class == 1 else "Passing",
                    risk_score=round(p_score, 4),
                    risk_level=tier,
                    recommendation=rec,
                    model_name=model_name,
                    model_version=model_ver,
                )
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Update service metrics
        self.total_predictions += len(students)
        self.at_risk_count += at_risk
        self.passing_count += passing
        self.total_latency_ms += elapsed_ms

        mean_risk = float(np.mean(probs)) if len(probs) > 0 else 0.0

        return BatchPredictionResponse(
            total_students=len(students),
            at_risk_count=at_risk,
            passing_count=passing,
            average_risk_score=round(mean_risk, 4),
            predictions=responses,
            model_version=model_ver,
        )

    def get_operational_metrics(self) -> Dict[str, Any]:
        """Return live inference metrics for monitoring."""
        avg_lat = (
            self.total_latency_ms / self.total_predictions
            if self.total_predictions > 0
            else 0.0
        )
        return {
            "model_loaded": self.is_loaded,
            "total_predictions": self.total_predictions,
            "at_risk_predictions": self.at_risk_count,
            "passing_predictions": self.passing_count,
            "average_latency_ms": round(avg_lat, 2),
        }
