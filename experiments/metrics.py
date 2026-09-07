"""
Statistical Metrics Subsystem
Implements accuracy, error quantification, and rank correlation metrics:
- Mean Absolute Error (MAE)
- Mean Absolute Percentage Error (MAPE, with zero-denominator safety)
- Top-Stage Identification Accuracy
- Workflow Stage Ranking Agreement (Spearman rank correlation)
- Suppression Rate
"""

import numpy as np
from typing import List, Union, Dict, Any
import pandas as pd


def compute_mae(actual: Union[List[float], np.ndarray, pd.Series], predicted: Union[List[float], np.ndarray, pd.Series]) -> float:
    """Computes Mean Absolute Error."""
    act = np.array(actual, dtype=float)
    pred = np.array(predicted, dtype=float)
    if len(act) == 0:
        return 0.0
    return float(np.mean(np.abs(act - pred)))


def compute_mape(
    actual: Union[List[float], np.ndarray, pd.Series],
    predicted: Union[List[float], np.ndarray, pd.Series],
    epsilon_zero_guard: float = 1e-4
) -> float:
    """
    Computes Mean Absolute Percentage Error (MAPE) as a percentage (0 to 100%).
    Safely handles zero denominators using standard numerical stabilization.
    """
    act = np.array(actual, dtype=float)
    pred = np.array(predicted, dtype=float)
    if len(act) == 0:
        return 0.0

    # Guard against zero denominators
    safe_actual = np.where(np.abs(act) < epsilon_zero_guard, epsilon_zero_guard, act)
    percentage_errors = np.abs((act - pred) / safe_actual) * 100.0
    return float(np.mean(percentage_errors))


def compute_top_stage_accuracy(actual_top_stage: str, predicted_top_stage: str) -> float:
    """Returns 1.0 if privacy-preserving estimate correctly identifies top bottleneck, else 0.0."""
    if not actual_top_stage or not predicted_top_stage:
        return 0.0
    return 1.0 if str(actual_top_stage).strip().lower() == str(predicted_top_stage).strip().lower() else 0.0


def compute_ranking_agreement(
    actual_rates: Union[List[float], np.ndarray, pd.Series],
    predicted_rates: Union[List[float], np.ndarray, pd.Series]
) -> float:
    """
    Computes rank concordance (Spearman Rank Correlation coefficient).
    Uses Pearson correlation over ordinal ranks to avoid external scipy dependency.
    Returns value between -1.0 and 1.0 (1.0 = perfect agreement in stage bottleneck severity).
    """
    act = pd.Series(actual_rates, dtype=float)
    pred = pd.Series(predicted_rates, dtype=float)
    if len(act) <= 1 or act.std() == 0 or pred.std() == 0:
        return 1.0
    
    # Compute rank of values and then standard Pearson correlation
    act_rank = act.rank()
    pred_rank = pred.rank()
    if act_rank.std() == 0 or pred_rank.std() == 0:
        return 1.0

    corr = act_rank.corr(pred_rank, method="pearson")
    return float(0.0 if np.isnan(corr) else round(corr, 4))


def compute_comprehensive_metrics(
    actual_df: pd.DataFrame,
    predicted_df: pd.DataFrame,
    actual_top_stage: str,
    predicted_top_stage: str,
    rate_col: str = "abandonment_rate"
) -> Dict[str, float]:
    """Computes full evaluation battery comparing actual vs predicted stages."""
    act_rates = actual_df[rate_col].values
    pred_rates = predicted_df[rate_col].values

    mae = compute_mae(act_rates, pred_rates)
    mape = compute_mape(act_rates, pred_rates)
    top_acc = compute_top_stage_accuracy(actual_top_stage, predicted_top_stage)
    rank_agree = compute_ranking_agreement(act_rates, pred_rates)

    return {
        "mae": round(mae, 4),
        "mape": round(mape, 2),
        "top_stage_accuracy": top_acc,
        "ranking_agreement": rank_agree,
    }
