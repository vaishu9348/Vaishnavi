"""
Baseline Analytics Pipeline (Non-Private Reference Benchmark)
Calculates ground truth stage completion and abandonment rates
directly from consented interaction events without differential privacy noise.
"""

import sys
import os
from typing import Dict, Any
import pandas as pd

# Ensure privacy package is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from privacy.consent import filter_consented_events
from privacy.aggregation import aggregate_stage_metrics, stage_aggregates_to_dataframe, AggregateJourneyStats


def compute_non_private_baseline(df_events: pd.DataFrame) -> Dict[str, Any]:
    """
    Runs the baseline non-private aggregation pipeline:
    1. Filter by explicit consent
    2. Aggregate counts per stage
    3. Calculate abandonment and completion rates
    4. Identify ground-truth top abandonment bottleneck
    """
    # Step 1: Consent filter
    df_consented, consent_stats = filter_consented_events(df_events)

    # Step 2 & 3: Aggregation and abandonment rates
    stats: AggregateJourneyStats = aggregate_stage_metrics(df_consented)
    df_summary = stage_aggregates_to_dataframe(stats)

    return {
        "summary_df": df_summary,
        "top_abandonment_stage": stats.top_abandonment_stage,
        "max_abandonment_rate": stats.max_abandonment_rate,
        "total_sessions_analyzed": stats.total_sessions_analyzed,
        "consent_stats": consent_stats,
    }
