"""
Tests for Data Validation Layer
Validates schema conformity, PII detection, stage boundaries, and event integrity.
"""

import sys
import os
import pytest
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from scripts.validate_data import validate_telemetry_data, REQUIRED_COLUMNS, PROHIBITED_PII_FIELDS


def test_telemetry_validation_on_synthetic_dataset():
    """Verify that generated synthetic interaction events pass all validation checks."""
    csv_path = os.path.join(PROJECT_ROOT, "data", "synthetic", "interaction_events.csv")
    if not os.path.exists(csv_path):
        pytest.skip("Synthetic dataset not generated yet")

    result = validate_telemetry_data(csv_path)
    assert result['status'] == 'PASS'
    assert result['checks_passed'] == result['total_checks']
    assert result['total_sessions'] >= 10000
    assert result['total_records'] >= 50000


def test_pii_detection_fails_on_injected_pii(tmp_path):
    """Ensure validator catches any disallowed PII fields."""
    bad_data = pd.DataFrame({
        'event_id': ['EVT-001'],
        'session_id': ['ANON-1234-5678'],
        'stage_name': ['Login'],
        'event_type': ['ENTERED'],
        'timestamp_bucket': ['2026-09-07T12:00:00Z'],
        'consent_state': ['CONSENTED'],
        'portal_version': ['v2.1'],
        'email': ['user@example.com'],  # Injected PII
        'policy_number': ['POL-999']      # Injected PII
    })
    temp_csv = str(tmp_path / "bad_telemetry.csv")
    bad_data.to_csv(temp_csv, index=False)

    res = validate_telemetry_data(temp_csv)
    assert res['status'] == 'FAIL'
