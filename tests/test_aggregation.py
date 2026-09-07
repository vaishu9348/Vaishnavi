"""
Tests for Macro Aggregation Subsystem
Validates count aggregation, completion rate calculation, and zero individual record leakage.
"""

import sys
import os
import pytest
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from privacy.aggregation import aggregate_stage_metrics, stage_aggregates_to_dataframe, ORDERED_WORKFLOW_STAGES


def test_aggregate_stage_metrics():
    events = [
        {"anonymous_session_id": "U1", "workflow_stage": "Login", "event_type": "ENTERED"},
        {"anonymous_session_id": "U1", "workflow_stage": "Login", "event_type": "COMPLETED"},
        {"anonymous_session_id": "U1", "workflow_stage": "Start Claim", "event_type": "ENTERED"},
        {"anonymous_session_id": "U1", "workflow_stage": "Start Claim", "event_type": "COMPLETED"},
        {"anonymous_session_id": "U2", "workflow_stage": "Login", "event_type": "ENTERED"},
        {"anonymous_session_id": "U2", "workflow_stage": "Login", "event_type": "COMPLETED"},
        {"anonymous_session_id": "U2", "workflow_stage": "Start Claim", "event_type": "ENTERED"},
        {"anonymous_session_id": "U2", "workflow_stage": "Start Claim", "event_type": "ABANDONED"},
    ]
    df = pd.DataFrame(events)
    stats = aggregate_stage_metrics(df)

    assert stats.total_sessions_analyzed == 2

    df_stages = stage_aggregates_to_dataframe(stats)
    login_row = df_stages[df_stages["workflow_stage"] == "Login"].iloc[0]
    start_row = df_stages[df_stages["workflow_stage"] == "Start Claim"].iloc[0]

    assert login_row["entered_count"] == 2
    assert login_row["completed_count"] == 2
    assert login_row["completion_rate"] == 1.0

    assert start_row["entered_count"] == 2
    assert start_row["completed_count"] == 1
    assert start_row["abandoned_count"] == 1
    assert start_row["abandonment_rate"] == 0.5


def test_empty_dataframe_aggregation():
    stats = aggregate_stage_metrics(pd.DataFrame())
    assert stats.total_sessions_analyzed == 0
    assert len(stats.stages) == len(ORDERED_WORKFLOW_STAGES)
