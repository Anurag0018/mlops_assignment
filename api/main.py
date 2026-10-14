"""
FastAPI Academic Risk Inference Microservice
--------------------------------------------
Exposes REST endpoints for model health, metadata, single/batch prediction,
and operational metrics for the student performance early-warning system.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.common.config import ALL_FEATURE_COLUMNS, TARGET_COLUMN
from api.schemas import (
    StudentFeatures,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
    HealthResponse,
    ModelInfoResponse,
)
from api.services import ModelService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("api.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Eagerly load model and preprocessor artifacts during startup."""
    logger.info("Initializing Model Service on FastAPI startup...")
    service = ModelService.get_instance()
    if not service.is_loaded:
        logger.warning("Warning: Model artifacts could not be loaded at startup.")
    else:
        logger.info("FastAPI ready to receive prediction traffic.")
    yield
    logger.info("Shutting down Model Service...")


app = FastAPI(
    title="Student Performance & Academic Risk Prediction API",
    description=(
        "Production-grade MLOps inference microservice predicting student academic failure "
        "risk (G3 < 10) using leak-free baseline features and an MLflow-tracked XGBoost champion model."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for Streamlit dashboard and cross-origin clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["General"])
def root():
    """Welcome and quick API navigation."""
    return {
        "service": "Student Performance & Academic Risk Prediction API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_url": "/health",
        "model_info_url": "/model-info",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health & Governance"])
def health():
    """Verify service readiness and model loading status."""
    service = ModelService.get_instance()
    model_name = service.registry_info.get("champion_model_name", "AcademicRiskClassifier") if service.is_loaded else None
    model_ver = service.registry_info.get("model_version", "v1.0.0") if service.is_loaded else None

    return HealthResponse(
        status="ok" if service.is_loaded else "degraded",
        model_loaded=service.is_loaded,
        model_name=model_name,
        model_version=model_ver,
    )


@app.get("/model-info", response_model=ModelInfoResponse, tags=["Health & Governance"])
def model_info():
    """Retrieve champion model lineage, hyperparameters, and evaluation metrics."""
    service = ModelService.get_instance()
    if not service.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded or registry metadata is unavailable."
        )

    info = service.registry_info
    return ModelInfoResponse(
        champion_model_name=info.get("champion_model_name", "XGBoost Classifier"),
        algorithm=info.get("algorithm", "XGBClassifier"),
        model_version=info.get("model_version", "v1.0.0"),
        target_definition="1 = Academic Failure Risk (G3 < 10), 0 = Passing (G3 >= 10)",
        selection_rationale=info.get("selection_rationale", "Optimized for validation F1 and Recall."),
        validation_metrics=info.get("validation_metrics", {}),
        test_metrics=info.get("test_metrics", {}),
        feature_columns=ALL_FEATURE_COLUMNS,
        total_features=len(ALL_FEATURE_COLUMNS),
        timestamp=info.get("registered_at", ""),
    )


@app.post("/predict", response_model=PredictionResponse, tags=["Inference"])
def predict(features: StudentFeatures):
    """
    Predict academic risk for a single student profile.
    Returns predicted class, risk probability score, risk tier, and intervention guidance.
    """
    service = ModelService.get_instance()
    if not service.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model service is currently unavailable. Ensure artifacts are generated."
        )

    try:
        response = service.predict_single(features)
        return response
    except Exception as e:
        logger.error(f"Inference error during /predict: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference failed: {str(e)}"
        )


@app.post("/predict/batch", response_model=BatchPredictionResponse, tags=["Inference"])
def predict_batch(payload: BatchPredictionRequest):
    """
    Predict academic risk for a roster of student records in a single vectorized batch.
    """
    service = ModelService.get_instance()
    if not service.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model service is currently unavailable."
        )

    if not payload.students:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student roster cannot be empty."
        )

    try:
        response = service.predict_batch(payload.students)
        return response
    except Exception as e:
        logger.error(f"Batch inference error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch inference failed: {str(e)}"
        )


@app.get("/metrics", tags=["Monitoring & Diagnostics"])
def operational_metrics():
    """Retrieve operational request counts, latency averages, and prediction distributions."""
    service = ModelService.get_instance()
    return service.get_operational_metrics()
