"""
Feature Drift Detection Module using Population Stability Index (PSI)
---------------------------------------------------------------------
Compares incoming inference features against reference baseline features
(captured during training) to detect statistical distribution shift.

Thresholds:
- PSI < 0.1: No significant drift (Stable distribution)
- 0.1 <= PSI < 0.2: Moderate drift (Warning / Early shift)
- PSI >= 0.2: Significant drift (Action Required: Triggers Retraining Alert)
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.common.config import (
    REFERENCE_FEATURES_PATH,
    NUMERICAL_FEATURES,
    CATEGORICAL_FEATURES,
    ALL_FEATURE_COLUMNS,
    DRIFT_PSI_THRESHOLD_WARNING,
    DRIFT_PSI_THRESHOLD_CRITICAL,
)

logger = logging.getLogger("monitoring.drift")


def calculate_numerical_psi(
    reference: np.ndarray,
    current: np.ndarray,
    num_bins: int = 10,
    epsilon: float = 1e-4
) -> float:
    """Calculate Population Stability Index (PSI) for continuous numerical features."""
    if len(reference) == 0 or len(current) == 0:
        return 0.0

    # Determine quantiles from reference baseline
    quantiles = np.linspace(0, 100, num_bins + 1)
    bins = np.percentile(reference, quantiles)
    bins = np.unique(bins)

    if len(bins) < 2:
        return 0.0

    # Bin frequencies
    ref_counts, _ = np.histogram(reference, bins=bins)
    curr_counts, _ = np.histogram(current, bins=bins)

    # Convert to proportions with smoothing epsilon
    ref_props = ref_counts / len(reference) + epsilon
    curr_props = curr_counts / len(current) + epsilon

    # Normalize back to 1
    ref_props /= ref_props.sum()
    curr_props /= curr_props.sum()

    # PSI Formula: sum((Actual - Expected) * ln(Actual / Expected))
    psi_val = np.sum((curr_props - ref_props) * np.log(curr_props / ref_props))
    return float(round(max(0.0, psi_val), 4))


def calculate_categorical_psi(
    reference: pd.Series,
    current: pd.Series,
    epsilon: float = 1e-4
) -> float:
    """Calculate PSI for discrete categorical feature levels."""
    all_categories = sorted(list(set(reference.dropna().unique()).union(set(current.dropna().unique()))))
    if not all_categories:
        return 0.0

    ref_counts = reference.value_counts(normalize=True).to_dict()
    curr_counts = current.value_counts(normalize=True).to_dict()

    ref_props = np.array([ref_counts.get(cat, 0.0) + epsilon for cat in all_categories])
    curr_props = np.array([curr_counts.get(cat, 0.0) + epsilon for cat in all_categories])

    ref_props /= ref_props.sum()
    curr_props /= curr_props.sum()

    psi_val = np.sum((curr_props - ref_props) * np.log(curr_props / ref_props))
    return float(round(max(0.0, psi_val), 4))


class DriftDetector:
    """Detects feature distribution shift against the baseline training distribution."""

    def __init__(self, reference_path: Optional[Path] = None):
        self.ref_path = reference_path or REFERENCE_FEATURES_PATH
        self.reference_df: Optional[pd.DataFrame] = None
        self._load_reference_data()

    def _load_reference_data(self) -> None:
        if not self.ref_path.exists():
            logger.warning(f"Reference features not found at {self.ref_path}. Drift detection disabled.")
            return

        try:
            self.reference_df = pd.read_parquet(self.ref_path)
            logger.info(f"Loaded reference feature baseline ({len(self.reference_df)} rows).")
        except Exception as e:
            logger.error(f"Failed to load reference features: {e}")

    def evaluate_drift(self, current_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Evaluate drift across all features.
        Returns PSI report per feature and overall system drift assessment.
        """
        if self.reference_df is None or len(current_df) == 0:
            return {
                "status": "baseline_unavailable",
                "overall_drift_detected": False,
                "overall_drift_level": "Unknown",
                "feature_psi": {},
            }

        feature_psi: Dict[str, Dict[str, Any]] = {}
        drifted_features = []
        warning_features = []

        # Numerical features
        for col in NUMERICAL_FEATURES:
            if col in current_df.columns and col in self.reference_df.columns:
                ref_vals = self.reference_df[col].dropna().values
                curr_vals = current_df[col].dropna().values
                psi = calculate_numerical_psi(ref_vals, curr_vals)

                if psi >= DRIFT_PSI_THRESHOLD_CRITICAL:
                    level = "Critical Drift"
                    drifted_features.append(col)
                elif psi >= DRIFT_PSI_THRESHOLD_WARNING:
                    level = "Moderate Drift"
                    warning_features.append(col)
                else:
                    level = "Stable"

                feature_psi[col] = {
                    "type": "numerical",
                    "psi": psi,
                    "status": level,
                    "ref_mean": round(float(np.mean(ref_vals)), 2) if len(ref_vals) else 0.0,
                    "curr_mean": round(float(np.mean(curr_vals)), 2) if len(curr_vals) else 0.0,
                }

        # Categorical features
        for col in CATEGORICAL_FEATURES:
            if col in current_df.columns and col in self.reference_df.columns:
                ref_series = self.reference_df[col].astype(str)
                curr_series = current_df[col].astype(str)
                psi = calculate_categorical_psi(ref_series, curr_series)

                if psi >= DRIFT_PSI_THRESHOLD_CRITICAL:
                    level = "Critical Drift"
                    drifted_features.append(col)
                elif psi >= DRIFT_PSI_THRESHOLD_WARNING:
                    level = "Moderate Drift"
                    warning_features.append(col)
                else:
                    level = "Stable"

                feature_psi[col] = {
                    "type": "categorical",
                    "psi": psi,
                    "status": level,
                }

        # Overall summary
        psi_scores = [f["psi"] for f in feature_psi.values()]
        avg_psi = round(float(np.mean(psi_scores)), 4) if psi_scores else 0.0
        max_psi = round(float(np.max(psi_scores)), 4) if psi_scores else 0.0

        if len(drifted_features) > 0 or max_psi >= DRIFT_PSI_THRESHOLD_CRITICAL:
            overall_status = "Critical Shift (Retraining Alert)"
            drift_detected = True
        elif len(warning_features) > 0 or max_psi >= DRIFT_PSI_THRESHOLD_WARNING:
            overall_status = "Moderate Shift (Monitor)"
            drift_detected = False
        else:
            overall_status = "Stable (No Drift)"
            drift_detected = False

        return {
            "status": "evaluated",
            "reference_sample_size": len(self.reference_df),
            "current_sample_size": len(current_df),
            "average_psi": avg_psi,
            "max_psi": max_psi,
            "overall_drift_status": overall_status,
            "overall_drift_detected": drift_detected,
            "critical_features": drifted_features,
            "warning_features": warning_features,
            "feature_psi": feature_psi,
        }
