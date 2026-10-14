"""
Model Evaluation and Metric Computation Module
---------------------------------------------
Computes comprehensive classification metrics with focus on academic risk detection:
- Recall: Minimizes missed at-risk students (False Negatives).
- Precision: Minimizes false alerts for interventions (False Positives).
- F1-score: Harmonic balance for alert quality.
- ROC-AUC and PR-AUC: Discrimination ability across probability thresholds.
- Confusion Matrix and ROC plots.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    classification_report,
    roc_curve,
    precision_recall_curve,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.common.config import REPORTS_DIR

logger = logging.getLogger("evaluate")


def calculate_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: Optional[np.ndarray] = None
) -> Dict[str, float]:
    """Calculate standard and risk-sensitive classification metrics."""
    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    metrics = {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
    }

    # Confusion matrix elements
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    metrics["true_negatives"] = int(tn)
    metrics["false_positives"] = int(fp)
    metrics["false_negatives"] = int(fn)
    metrics["true_positives"] = int(tp)

    # Probabilistic metrics if probabilities are supplied
    if y_prob is not None:
        try:
            auc = float(roc_auc_score(y_true, y_prob))
            metrics["roc_auc"] = round(auc, 4)
        except Exception:
            metrics["roc_auc"] = 0.0

        try:
            pr_auc = float(average_precision_score(y_true, y_prob))
            metrics["pr_auc"] = round(pr_auc, 4)
        except Exception:
            metrics["pr_auc"] = 0.0

    return metrics


def plot_confusion_matrix_artifact(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    model_name: str,
    output_path: Optional[Path] = None
) -> Path:
    """Generate and save confusion matrix figure."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = output_path or (REPORTS_DIR / f"cm_{model_name.lower().replace(' ', '_')}.png")

    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(6, 5))
    cax = ax.matshow(cm, cmap=plt.cm.Blues, alpha=0.8)

    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(
                x=j, y=i,
                s=str(cm[i, j]),
                va="center", ha="center",
                size="large", weight="bold",
                color="white" if cm[i, j] > cm.max() / 2 else "black"
            )

    fig.colorbar(cax)
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["Passing (0)", "At-Risk (1)"])
    ax.set_yticklabels(["Passing (0)", "At-Risk (1)"])
    plt.xlabel("Predicted Label", fontweight="bold")
    plt.ylabel("True Label", fontweight="bold")
    plt.title(f"Confusion Matrix: {model_name}", pad=20, fontweight="bold")
    plt.tight_layout()
    plt.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_roc_curve_artifact(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    model_name: str,
    output_path: Optional[Path] = None
) -> Path:
    """Generate and save ROC curve plot."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = output_path or (REPORTS_DIR / f"roc_{model_name.lower().replace(' ', '_')}.png")

    fpr, tpr, _ = roc_curve(y_true, y_prob)
    auc_val = roc_auc_score(y_true, y_prob)

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr, color="#2563eb", lw=2, label=f"ROC (AUC = {auc_val:.3f})")
    ax.plot([0, 1], [0, 1], color="#9ca3af", lw=1.5, linestyle="--", label="Random Classifier")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("False Positive Rate (1 - Specificity)", fontweight="bold")
    ax.set_ylabel("True Positive Rate (Recall)", fontweight="bold")
    ax.set_title(f"ROC Curve: {model_name}", pad=15, fontweight="bold")
    ax.legend(loc="lower right")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_pr_curve_artifact(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    model_name: str,
    output_path: Optional[Path] = None
) -> Path:
    """Generate and save Precision-Recall curve plot."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = output_path or (REPORTS_DIR / f"pr_{model_name.lower().replace(' ', '_')}.png")

    precision, recall, _ = precision_recall_curve(y_true, y_prob)
    pr_auc = average_precision_score(y_true, y_prob)

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(recall, precision, color="#10b981", lw=2, label=f"PR Curve (AP = {pr_auc:.3f})")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("Recall (Coverage of At-Risk Students)", fontweight="bold")
    ax.set_ylabel("Precision (Intervention Accuracy)", fontweight="bold")
    ax.set_title(f"Precision-Recall Curve: {model_name}", pad=15, fontweight="bold")
    ax.legend(loc="lower left")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out, dpi=150)
    plt.close(fig)
    return out
