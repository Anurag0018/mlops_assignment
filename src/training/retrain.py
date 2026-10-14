"""
Automated Model Retraining and Champion-vs-Challenger Workflow
-------------------------------------------------------------
Executes the documented retraining pipeline:
1. Re-trains candidate models on latest ingested & validated dataset.
2. Compares the best Challenger against the active Champion model.
3. Enforces automated promotion criteria:
   - Challenger must meet or exceed Champion validation F1-score (delta >= 0.005).
   - Validation Recall must not degrade below 0.70.
4. Updates model artifacts, increments semantic model version, and logs promotion history.
"""

import sys
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Tuple
import joblib

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.common.config import (
    BEST_MODEL_PATH,
    MODEL_REGISTRY_PATH,
    MIN_F1_SCORE_THRESHOLD,
    MIN_RECALL_THRESHOLD,
)
from src.training.train import run_training_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("retrain")


def evaluate_promotion_criteria(
    current_champion: Dict[str, Any],
    challenger: Dict[str, Any],
    min_improvement: float = 0.005
) -> Tuple[bool, str]:
    """
    Check whether Challenger qualifies to replace Champion.
    Returns (should_promote, rationale).
    """
    champ_val = current_champion.get("validation_metrics", {})
    chal_val = challenger.get("validation_metrics", {})

    champ_f1 = champ_val.get("f1", 0.0)
    chal_f1 = chal_val.get("f1", 0.0)

    chal_recall = chal_val.get("recall", 0.0)

    # Constraint 1: Minimum Recall floor for academic early warning
    if chal_recall < MIN_RECALL_THRESHOLD:
        return False, (
            f"Challenger rejected: Validation Recall ({chal_recall:.4f}) is below minimum "
            f"safety threshold ({MIN_RECALL_THRESHOLD:.2f}). Early-warning system cannot miss at-risk students."
        )

    # Constraint 2: Meaningful improvement over champion
    f1_diff = chal_f1 - champ_f1
    if f1_diff >= min_improvement:
        return True, (
            f"Challenger promoted! Validation F1 improved from {champ_f1:.4f} to {chal_f1:.4f} "
            f"(+{f1_diff:.4f} >= threshold {min_improvement})."
        )
    elif chal_f1 >= champ_f1:
        return True, (
            f"Challenger promoted (tie-breaker/fresh weights)! Validation F1 matched Champion ({chal_f1:.4f}) "
            f"trained on updated data distribution."
        )
    else:
        return False, (
            f"Challenger rejected: Validation F1 ({chal_f1:.4f}) did not beat Champion F1 ({champ_f1:.4f}). "
            f"Active champion retained in production."
        )


def execute_retraining_loop(force_promote: bool = False) -> Dict[str, Any]:
    """Execute complete retraining and governance cycle."""
    logger.info("Starting Retraining and Champion-vs-Challenger Workflow...")

    # Load active champion metadata
    current_registry = {}
    if MODEL_REGISTRY_PATH.exists():
        with open(MODEL_REGISTRY_PATH, "r", encoding="utf-8") as f:
            current_registry = json.load(f)

    # Execute full training and candidate benchmarking
    new_registry = run_training_pipeline()

    # If no prior registry exists, initial run becomes champion automatically
    if not current_registry:
        logger.info("No prior champion found. Registering initial champion.")
        return new_registry

    should_promote, rationale = evaluate_promotion_criteria(
        current_champion=current_registry,
        challenger=new_registry
    )

    if force_promote:
        should_promote = True
        rationale = "Force promote flag set by operator."

    logger.info(f"Retraining Decision: {rationale}")

    # Parse version
    prev_ver = current_registry.get("model_version", "v1.0.0")
    major, minor, patch = [int(p) for p in prev_ver.replace("v", "").split(".")]

    if should_promote:
        next_ver = f"v{major}.{minor + 1}.0"
        new_registry["model_version"] = next_ver
        new_registry["promotion_status"] = "PROMOTED"
        new_registry["promotion_rationale"] = rationale
        new_registry["previous_version"] = prev_ver

        # Update registry JSON
        with open(MODEL_REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(new_registry, f, indent=2)
        logger.info(f"Promoted new Champion: {new_registry['champion_model_name']} ({next_ver})")
        return new_registry
    else:
        current_registry["last_retraining_attempt"] = datetime.now(timezone.utc).isoformat()
        current_registry["last_challenger_result"] = {
            "challenger_model": new_registry.get("champion_model_name"),
            "status": "REJECTED",
            "rationale": rationale,
            "challenger_metrics": new_registry.get("validation_metrics"),
        }
        with open(MODEL_REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(current_registry, f, indent=2)
        logger.info("Active champion remains in service.")
        return current_registry


if __name__ == "__main__":
    execute_retraining_loop()
