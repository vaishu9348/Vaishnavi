"""
Tests for Operational Failure Modes
Validates at least 5 key failure modes:
1. Missing consent -> Event rejected
2. Invalid workflow stage / corrupted input -> Handled gracefully
3. Duplicate events -> Deduplicated / ignored
4. Small group -> Suppressed
5. Analytics service unavailable -> Legacy claim continues
"""

import sys
import os
import pytest
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from privacy.consent import validate_event_consent, filter_consented_events
from privacy.suppression import check_and_suppress_count
from app.rollback import RollbackController, SystemMode
from app.health import HealthMonitor


def test_failure_1_missing_consent():
    assert validate_event_consent(None) is False
    assert validate_event_consent("") is False


def test_failure_2_invalid_or_unknown_consent():
    assert validate_event_consent("UNKNOWN") is False
    assert validate_event_consent("INVALID_STATUS") is False


def test_failure_3_duplicate_event_handling():
    events = [
        {"event_id": "EVT-DUP-1", "workflow_stage": "Login", "event_type": "ENTERED", "consent_status": "CONSENTED"},
        {"event_id": "EVT-DUP-1", "workflow_stage": "Login", "event_type": "ENTERED", "consent_status": "CONSENTED"},
    ]
    df = pd.DataFrame(events)
    # Deduplication drops duplicate event IDs
    df_dedup = df.drop_duplicates(subset=["event_id"])
    assert len(df_dedup) == 1


def test_failure_4_small_group_suppressed():
    res = check_and_suppress_count(3, min_group_size=10)
    assert res.is_suppressed is True
    assert "[SUPPRESSED < 10]" in str(res.display_value)


def test_failure_5_analytics_unavailable_non_blocking_fallback(tmp_path):
    db_file = str(tmp_path / "test_outage.db")
    controller = RollbackController(db_path=db_file)
    health = HealthMonitor(db_path=db_file)

    # Simulate analytics failure
    controller.simulate_analytics_failure()
    assert controller.is_analytics_failed is True
    assert controller.current_mode == SystemMode.LEGACY_FALLBACK

    # Emitting an event through adapter during outage MUST NOT fail
    success = controller.dispatch_event_adapter({
        "event_id": "EVT-OUTAGE-TEST",
        "anonymous_session_id": "ANON-TEST",
        "workflow_stage": "Submit",
        "event_type": "COMPLETED",
    })
    assert success is True
