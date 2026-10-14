"""
Unit Tests for Retraining Governance and Promotion Criteria
-----------------------------------------------------------
Validates champion vs challenger promotion logic and recall safety floors.
"""

import pytest
from src.training.retrain import evaluate_promotion_criteria


def test_promotion_when_challenger_improves_f1():
    """Challenger with superior F1 and adequate recall must be promoted."""
    champion = {
        "validation_metrics": {"f1": 0.7200, "recall": 0.8000, "precision": 0.6500}
    }
    challenger = {
        "validation_metrics": {"f1": 0.7500, "recall": 0.8200, "precision": 0.6900}
    }
    should_promote, rationale = evaluate_promotion_criteria(champion, challenger)
    assert should_promote is True
    assert "Challenger promoted" in rationale


def test_rejection_when_challenger_recall_violates_safety_floor():
    """Challenger with recall < 0.70 must be rejected despite high accuracy/precision."""
    champion = {
        "validation_metrics": {"f1": 0.7200, "recall": 0.8000, "precision": 0.6500}
    }
    challenger = {
        "validation_metrics": {"f1": 0.7800, "recall": 0.6200, "precision": 0.9000}
    }
    should_promote, rationale = evaluate_promotion_criteria(champion, challenger)
    assert should_promote is False
    assert "safety threshold" in rationale


def test_rejection_when_challenger_has_inferior_f1():
    """Challenger with lower F1 must be rejected and champion retained."""
    champion = {
        "validation_metrics": {"f1": 0.7600, "recall": 0.8400, "precision": 0.6900}
    }
    challenger = {
        "validation_metrics": {"f1": 0.7100, "recall": 0.7500, "precision": 0.6700}
    }
    should_promote, rationale = evaluate_promotion_criteria(champion, challenger)
    assert should_promote is False
    assert "Active champion retained" in rationale
