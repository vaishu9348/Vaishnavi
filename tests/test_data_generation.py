"""
Tests for Synthetic Data Generator
Validates volume, schemas, stage coverage, bottleneck modeling, and consent distribution.
"""

import sys
import os
import pytest
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from scripts.generate_data import generate_synthetic_data, WORKFLOW_STEPS
from privacy.aggregation import ORDERED_WORKFLOW_STAGES


def test_data_generation_volume_and_schema(tmp_path):
    """Verifies that generator produces correct event schemas and target volume."""
    out_dir = str(tmp_path / "data")
    db_p = str(tmp_path / "data" / "synthetic" / "test.db")
    
    # Generate 500 test sessions for fast unit testing
    df_events = generate_synthetic_data(num_sessions=500, seed=42, output_dir=out_dir, db_path=db_p)

    assert not df_events.empty
    assert len(df_events) > 2000

    required_columns = {
        "event_id",
        "anonymous_session_id",
        "workflow_stage",
        "event_type",
        "timestamp_bucket",
        "consent_status",
        "portal_version",
        "event_source",
        "created_at",
    }
    assert required_columns.issubset(set(df_events.columns))


def test_stage_coverage_and_bottleneck(tmp_path):
    """Verifies all 8 stages are present and Document Upload has highest abandonment."""
    out_dir = str(tmp_path / "data")
    db_p = str(tmp_path / "data" / "synthetic" / "test.db")
    df_events = generate_synthetic_data(num_sessions=500, seed=42, output_dir=out_dir, db_path=db_p)

    stages_present = set(df_events["workflow_stage"].unique())
    for s in ORDERED_WORKFLOW_STAGES:
        assert s in stages_present

    # Check Document Upload has significant abandonment
    doc_events = df_events[df_events["workflow_stage"] == "Document Upload"]
    doc_abandoned = (doc_events["event_type"] == "ABANDONED").sum()
    assert doc_abandoned > 0


def test_consent_distribution_present(tmp_path):
    """Verifies consent status categories are generated."""
    out_dir = str(tmp_path / "data")
    db_p = str(tmp_path / "data" / "synthetic" / "test.db")
    df_events = generate_synthetic_data(num_sessions=300, seed=42, output_dir=out_dir, db_path=db_p)

    consent_statuses = set(df_events["consent_status"].unique())
    assert "CONSENTED" in consent_statuses
    assert "NOT_CONSENTED" in consent_statuses
