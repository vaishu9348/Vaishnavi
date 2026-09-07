"""
Aggregation Subsystem
Transforms individual interaction streams into macro stage-level counts.
Enforces that product teams receive zero row-level individual journeys.
"""

from typing import List, Dict, Any
import pandas as pd
from dataclasses import dataclass, asdict

# Canonical workflow sequence
ORDERED_WORKFLOW_STAGES = [
    "Login",
    "Start Claim",
    "Claim Type",
    "Claim Details",
    "Document Upload",
    "Review",
    "Submit",
    "Confirmation",
]


@dataclass
class StageAggregate:
    workflow_stage: str
    entered_count: int
    completed_count: int
    abandoned_count: int
    error_count: int
    completion_rate: float
    abandonment_rate: float


@dataclass
class AggregateJourneyStats:
    stages: List[StageAggregate]
    total_sessions_analyzed: int
    top_abandonment_stage: str
    max_abandonment_rate: float


def aggregate_stage_metrics(df: pd.DataFrame) -> AggregateJourneyStats:
    """
    Aggregates consented events across workflow stages.
    Guarantees no individual session identifiers or micro-traces are returned.
    """
    if df.empty:
        empty_stages = [
            StageAggregate(
                workflow_stage=stage,
                entered_count=0,
                completed_count=0,
                abandoned_count=0,
                error_count=0,
                completion_rate=0.0,
                abandonment_rate=0.0,
            )
            for stage in ORDERED_WORKFLOW_STAGES
        ]
        return AggregateJourneyStats(
            stages=empty_stages,
            total_sessions_analyzed=0,
            top_abandonment_stage="None",
            max_abandonment_rate=0.0,
        )

    # Clean stage column
    df_clean = df.copy()
    df_clean["workflow_stage"] = df_clean["workflow_stage"].astype(str)
    df_clean["event_type"] = df_clean["event_type"].astype(str).str.upper()

    unique_sessions = df_clean["anonymous_session_id"].nunique() if "anonymous_session_id" in df_clean.columns else len(df_clean)

    stage_records: List[StageAggregate] = []
    top_stage = "None"
    highest_abandonment_rate = -1.0

    for stage in ORDERED_WORKFLOW_STAGES:
        stage_df = df_clean[df_clean["workflow_stage"] == stage]
        
        entered = int((stage_df["event_type"] == "ENTERED").sum())
        completed = int((stage_df["event_type"] == "COMPLETED").sum())
        abandoned = int((stage_df["event_type"] == "ABANDONED").sum())
        error = int((stage_df["event_type"] == "ERROR").sum())

        # If entered wasn't explicitly logged or is smaller than completed+abandoned,
        # ensure conservative lower-bound consistency
        effective_entered = max(entered, completed + abandoned)

        comp_rate = round(completed / effective_entered, 4) if effective_entered > 0 else 0.0
        aband_rate = round(abandoned / effective_entered, 4) if effective_entered > 0 else 0.0

        if aband_rate > highest_abandonment_rate and effective_entered > 0:
            highest_abandonment_rate = aband_rate
            top_stage = stage

        stage_records.append(
            StageAggregate(
                workflow_stage=stage,
                entered_count=effective_entered,
                completed_count=completed,
                abandoned_count=abandoned,
                error_count=error,
                completion_rate=comp_rate,
                abandonment_rate=aband_rate,
            )
        )

    return AggregateJourneyStats(
        stages=stage_records,
        total_sessions_analyzed=unique_sessions,
        top_abandonment_stage=top_stage,
        max_abandonment_rate=max(highest_abandonment_rate, 0.0),
    )


def stage_aggregates_to_dataframe(stats: AggregateJourneyStats) -> pd.DataFrame:
    """Converts AggregateJourneyStats to standard pandas DataFrame for charts and display."""
    return pd.DataFrame([asdict(s) for s in stats.stages])
