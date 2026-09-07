"""
Tests for Common Privacy Misuse & Security Controls
Implements formal validation of the 5 security misuse scenarios:
1. Individual lookup attempt -> Blocked
2. Small-group inference attempt -> Suppressed
3. Consent bypass injection -> Excluded
4. Privacy budget abuse (epsilon > 1.0) -> Rejected
5. Excessive queries / budget exhaustion -> Rejected
"""

import sys
import os
import pytest
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from privacy.consent import validate_event_consent, filter_consented_events
from privacy.suppression import check_and_suppress_count
from privacy.differential_privacy import LaplaceMechanism, PrivacyBudgetManager, BudgetExhaustedError, InvalidEpsilonError
from app.analytics import run_privacy_preserving_analytics


def test_security_misuse_1_individual_lookup_blocked():
    """Attempting to query individual user journeys must return only macro aggregates."""
    df_raw = pd.DataFrame([
        {"anonymous_session_id": "ANON-TARGET-001", "workflow_stage": "Login", "event_type": "ENTERED", "consent_status": "CONSENTED"},
        {"anonymous_session_id": "ANON-TARGET-001", "workflow_stage": "Login", "event_type": "COMPLETED", "consent_status": "CONSENTED"},
        {"anonymous_session_id": "ANON-OTHER-002", "workflow_stage": "Login", "event_type": "ENTERED", "consent_status": "CONSENTED"},
    ])
    
    analytics_out = run_privacy_preserving_analytics(df_raw, epsilon=1.0)
    private_df = analytics_out["private_df"]
    
    # Guarantees that individual anonymous_session_id is NOT present in analytics results
    assert "anonymous_session_id" not in private_df.columns
    assert "user_id" not in private_df.columns


def test_security_misuse_2_small_group_inference():
    """Attempting to query a group with count = 2 must be suppressed."""
    result = check_and_suppress_count(2, min_group_size=10)
    assert result.is_suppressed is True
    assert "[SUPPRESSED" in str(result.display_value)
    assert result.min_threshold == 10


def test_security_misuse_3_consent_bypass():
    """Injecting consent = NOT_CONSENTED must be excluded from analytics."""
    df_injected = pd.DataFrame([
        {"event_id": "EVT-BYPASS", "workflow_stage": "Document Upload", "event_type": "ABANDONED", "consent_status": "NOT_CONSENTED"},
        {"event_id": "EVT-VALID", "workflow_stage": "Document Upload", "event_type": "ABANDONED", "consent_status": "CONSENTED"},
    ])
    df_filtered, stats = filter_consented_events(df_injected)

    assert len(df_filtered) == 1
    assert df_filtered.iloc[0]["event_id"] == "EVT-VALID"
    assert stats["not_consented_count"] == 1


def test_security_misuse_4_privacy_budget_abuse():
    """Requesting excessive epsilon (e.g. epsilon = 100) must be rejected."""
    with pytest.raises(InvalidEpsilonError):
        LaplaceMechanism.validate_epsilon(100.0)


def test_security_misuse_5_excessive_queries_budget_exhaustion():
    """Exceeding cumulative privacy budget must reject subsequent queries."""
    mgr = PrivacyBudgetManager(total_budget=1.0)
    
    # Query 1: Deducts 0.6
    mgr.request_budget(0.6)
    assert mgr.get_status()["remaining_budget"] == 0.4

    # Query 2: Requests 0.5 (Exceeds remaining 0.4) -> Must be rejected
    with pytest.raises(BudgetExhaustedError):
        mgr.request_budget(0.5)
