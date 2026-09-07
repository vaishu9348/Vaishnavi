"""
Tests for Consent Management Subsystem
Validates conservative defaults, consent filtering, and secure-by-default behavior.
"""

import sys
import os
import pytest
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from privacy.consent import validate_event_consent, filter_consented_events, ConsentStatus, is_event_allowed


def test_validate_event_consent_consented():
    assert validate_event_consent("CONSENTED") is True
    assert validate_event_consent("consented") is True


def test_validate_event_consent_non_consented():
    assert validate_event_consent("NOT_CONSENTED") is False
    assert validate_event_consent("UNKNOWN") is False
    assert validate_event_consent("") is False
    assert validate_event_consent(None) is False
    assert validate_event_consent("anything_else") is False


def test_filter_consented_events():
    data = [
        {"event_id": "1", "consent_status": "CONSENTED", "value": 10},
        {"event_id": "2", "consent_status": "NOT_CONSENTED", "value": 20},
        {"event_id": "3", "consent_status": "UNKNOWN", "value": 30},
        {"event_id": "4", "consent_status": None, "value": 40},
        {"event_id": "5", "consent_status": "CONSENTED", "value": 50},
    ]
    df = pd.DataFrame(data)
    df_filtered, stats = filter_consented_events(df)

    assert len(df_filtered) == 2
    assert set(df_filtered["event_id"]) == {"1", "5"}
    assert stats["total_received"] == 5
    assert stats["consented_count"] == 2
    assert stats["not_consented_count"] == 1
    assert stats["unknown_count"] == 2
    assert stats["rejection_rate"] == 0.6


def test_is_event_allowed():
    assert is_event_allowed({"consent_status": "CONSENTED"}) is True
    assert is_event_allowed({"consent_status": "NOT_CONSENTED"}) is False
    assert is_event_allowed({"consent_status": "UNKNOWN"}) is False
    assert is_event_allowed({}) is False
