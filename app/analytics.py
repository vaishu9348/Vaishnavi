"""
Privacy-Preserving Journey Analytics Engine
Combines Consent Filtering, Anonymisation, Aggregation,
Small-Group Suppression, and Laplace Differential Privacy.
"""

import sys
import os
from typing import Dict, Any, Optional
import pandas as pd
import time

# Resolve import paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from privacy.consent import filter_consented_events
from privacy.aggregation import aggregate_stage_metrics, stage_aggregates_to_dataframe, AggregateJourneyStats
from privacy.suppression import apply_small_group_suppression, DEFAULT_MIN_GROUP_SIZE
from privacy.differential_privacy import LaplaceMechanism, PrivacyBudgetManager, BudgetExhaustedError, InvalidEpsilonError


def run_privacy_preserving_analytics(
    df_events: pd.DataFrame,
    epsilon: float = 1.0,
    min_group_size: int = DEFAULT_MIN_GROUP_SIZE,
    budget_manager: Optional[PrivacyBudgetManager] = None,
    seed: Optional[int] = None,
    allow_experiment_epsilon: bool = False
) -> Dict[str, Any]:
    """
    Executes the proposed privacy-preserving journey analytics pipeline:
    1. Consent Filter (Consent status must be CONSENTED)
    2. Aggregation (Macro stage counts; no individual rows exposed)
    3. Small-Group Suppression (Minimum group size enforcement)
    4. Differential Privacy (Laplace noise on counts)
    5. Abandonment Analytics (Private rates & bottleneck identification)
    """
    start_time = time.perf_counter()

    # Deduct from privacy budget if manager provided
    budget_consumed = 0.0
    if budget_manager is not None:
        budget_consumed = budget_manager.request_budget(epsilon, allow_experiment=allow_experiment_epsilon)

    # 1. Filter consented events
    df_consented, consent_stats = filter_consented_events(df_events)

    # 2. Macro aggregation
    raw_stats: AggregateJourneyStats = aggregate_stage_metrics(df_consented)
    df_baseline = stage_aggregates_to_dataframe(raw_stats)

    # 3 & 4. Differential Privacy Perturbation
    dp = LaplaceMechanism(epsilon=epsilon, sensitivity=1.0, seed=seed, allow_experiment=allow_experiment_epsilon)

    df_private = df_baseline.copy()
    for idx in df_private.index:
        true_entered = df_private.at[idx, "entered_count"]
        true_completed = df_private.at[idx, "completed_count"]
        true_abandoned = df_private.at[idx, "abandoned_count"]
        true_error = df_private.at[idx, "error_count"]

        if true_entered == 0:
            df_private.at[idx, "entered_count"] = 0
            df_private.at[idx, "completed_count"] = 0
            df_private.at[idx, "abandoned_count"] = 0
            df_private.at[idx, "error_count"] = 0
            df_private.at[idx, "completion_rate"] = 0.0
            df_private.at[idx, "abandonment_rate"] = 0.0
            continue

        # Perturb counts with Laplace noise
        p_entered = dp.perturb_count(true_entered)
        p_completed = dp.perturb_count(true_completed)
        p_abandoned = dp.perturb_count(true_abandoned)
        p_error = dp.perturb_count(true_error)

        # Consistent lower bounds
        p_entered = max(p_entered, p_completed + p_abandoned)

        df_private.at[idx, "entered_count"] = p_entered
        df_private.at[idx, "completed_count"] = p_completed
        df_private.at[idx, "abandoned_count"] = p_abandoned
        df_private.at[idx, "error_count"] = p_error

        # Recompute private rates
        c_rate = round(p_completed / p_entered, 4) if p_entered > 0 else 0.0
        a_rate = round(p_abandoned / p_entered, 4) if p_entered > 0 else 0.0

        df_private.at[idx, "completion_rate"] = c_rate
        df_private.at[idx, "abandonment_rate"] = a_rate

    # Identify top abandonment stage from private estimates
    top_private_stage = "None"
    max_aband_rate = -1.0
    for idx, row in df_private.iterrows():
        if row["abandonment_rate"] > max_aband_rate and row["entered_count"] > 0:
            max_aband_rate = row["abandonment_rate"]
            top_private_stage = row["workflow_stage"]

    # 5. Small-Group Suppression
    suppression_output = apply_small_group_suppression(
        df_private,
        count_columns=["entered_count", "completed_count", "abandoned_count", "error_count"],
        min_group_size=min_group_size
    )

    runtime = round(time.perf_counter() - start_time, 4)

    return {
        "private_df": df_private,
        "suppressed_display_df": suppression_output["suppressed_df"],
        "baseline_df": df_baseline,
        "top_abandonment_stage": top_private_stage,
        "max_abandonment_rate": max_aband_rate,
        "epsilon_used": epsilon,
        "suppression_info": suppression_output,
        "consent_stats": consent_stats,
        "budget_consumed": budget_consumed,
        "runtime_seconds": runtime,
    }
