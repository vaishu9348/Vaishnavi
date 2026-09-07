"""
Tests for Anonymisation & Data Minimisation
Validates PII stripping, session ID hashing, and timestamp bucketization.
"""

import sys
import os
import pytest
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from privacy.anonymization import sanitize_event, generate_anonymous_session_id, bucketize_timestamp, PROHIBITED_PII_FIELDS


def test_generate_anonymous_session_id():
    token1 = generate_anonymous_session_id("seed_user_1")
    token2 = generate_anonymous_session_id("seed_user_2")

    assert token1.startswith("ANON-")
    assert token2.startswith("ANON-")
    assert token1 != token2
    # Deterministic with same seed
    token1_dup = generate_anonymous_session_id("seed_user_1")
    assert token1 == token1_dup


def test_bucketize_timestamp():
    dt = datetime(2026, 9, 7, 14, 38, 22)
    bucketed = bucketize_timestamp(dt, bucket_hours=1)
    assert bucketed == "2026-09-07 14:00:00"


def test_sanitize_event_strips_pii():
    raw_event = {
        "event_id": "EVT-100",
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "+1-555-0199",
        "policy_number": "POL-9999",
        "medical_info": "Sprained ankle",
        "workflow_stage": "Document Upload",
        "event_type": "ENTERED",
        "timestamp_bucket": "2026-09-07 14:00:00",
        "consent_status": "CONSENTED",
        "portal_version": "v2.5-coexistence",
        "event_source": "web_claims_portal",
    }

    sanitized = sanitize_event(raw_event)

    # All prohibited PII fields must be absent
    for pii in PROHIBITED_PII_FIELDS:
        assert pii not in sanitized

    # Allowed fields must remain
    assert sanitized["event_id"] == "EVT-100"
    assert sanitized["workflow_stage"] == "Document Upload"
    assert sanitized["event_type"] == "ENTERED"
    assert sanitized["anonymous_session_id"].startswith("ANON-")
