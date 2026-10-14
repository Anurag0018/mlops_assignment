"""
Data Quality Validation Module for Inference Traffic
---------------------------------------------------
Validates incoming inference data against feature bounds,
detects missing fields, out-of-range numerical values,
and unseen categorical levels.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.common.config import FEATURE_METADATA_PATH, ALL_FEATURE_COLUMNS, NUMERICAL_FEATURES, CATEGORICAL_FEATURES

logger = logging.getLogger("monitoring.data_quality")


class DataQualityValidator:
    """Validates inference records against training metadata constraints."""

    def __init__(self, metadata_path: Path = FEATURE_METADATA_PATH):
        self.metadata_path = metadata_path
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Any]:
        if not self.metadata_path.exists():
            logger.warning(f"Feature metadata not found at {self.metadata_path}. Using fallback validation.")
            return {}
        with open(self.metadata_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def validate_record(self, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate a single record dictionary against schema rules."""
        issues = []

        # Check missing required columns
        for col in ALL_FEATURE_COLUMNS:
            if col not in record or record[col] is None:
                issues.append(f"Missing required feature: '{col}'")

        if issues:
            return False, issues

        # Numerical bounds
        num_rules = self.metadata.get("numerical_features", {})
        for col in NUMERICAL_FEATURES:
            val = record.get(col)
            if val is not None:
                try:
                    fval = float(val)
                    if col == "g1" and not (0.0 <= fval <= 20.0):
                        issues.append(f"Feature 'g1' out of bounds: {fval} (expected 0 to 20)")
                    elif col == "age" and not (14 <= fval <= 35):
                        issues.append(f"Feature 'age' out of bounds: {fval} (expected 14 to 35)")
                    elif col == "attendance_rate" and not (0.0 <= fval <= 100.0):
                        issues.append(f"Feature 'attendance_rate' out of bounds: {fval} (expected 0 to 100)")
                    elif col == "studytime" and not (1 <= fval <= 4):
                        issues.append(f"Feature 'studytime' out of bounds: {fval} (expected 1 to 4)")
                    elif col == "failures" and not (0 <= fval <= 5):
                        issues.append(f"Feature 'failures' out of bounds: {fval} (expected 0 to 5)")
                except (ValueError, TypeError):
                    issues.append(f"Numerical feature '{col}' is not a valid number: {val}")

        # Categorical allowed values
        cat_rules = self.metadata.get("categorical_features", {})
        for col in CATEGORICAL_FEATURES:
            val = str(record.get(col, ""))
            allowed = cat_rules.get(col, {}).get("allowed_categories", [])
            if allowed and val not in allowed:
                issues.append(f"Unseen category in '{col}': '{val}' (allowed: {allowed})")

        is_valid = len(issues) == 0
        return is_valid, issues

    def validate_batch(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate an entire DataFrame batch and calculate data quality health index."""
        total_rows = len(df)
        if total_rows == 0:
            return {"total_records": 0, "quality_score_pct": 100.0, "issues": []}

        invalid_rows = 0
        collected_issues = []

        for idx, row in df.iterrows():
            valid, issues = self.validate_record(row.to_dict())
            if not valid:
                invalid_rows += 1
                collected_issues.extend([f"Row {idx}: {iss}" for iss in issues])

        quality_score = round((1.0 - (invalid_rows / total_rows)) * 100.0, 2)

        return {
            "total_records": total_rows,
            "valid_records": total_rows - invalid_rows,
            "invalid_records": invalid_rows,
            "quality_score_pct": quality_score,
            "issue_count": len(collected_issues),
            "sample_issues": collected_issues[:10],
        }
