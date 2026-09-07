"""
Experiments package for Insurance Privacy Journey Analytics Platform.
Provides baseline computation, comparative evaluation, and error metrics.
"""

from .baseline import compute_non_private_baseline
from .metrics import compute_mae, compute_mape, compute_top_stage_accuracy, compute_ranking_agreement
from .evaluation import run_evaluation_experiment

__all__ = [
    "compute_non_private_baseline",
    "compute_mae",
    "compute_mape",
    "compute_top_stage_accuracy",
    "compute_ranking_agreement",
    "run_evaluation_experiment",
]
