"""
Tests for Abandonment Analytics Engine
Validates completion rates, abandonment rates, and bottleneck identification.
"""

import sys
import os
import pytest
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from app.analytics import run_privacy_preserving_analytics
from experiments.baseline import compute_non_private_baseline


def test_abandonment_analytics_identification():
    # Build synthetic event set where Document Upload has 50% abandonment, others < 10%
    events = []
    # 100 sessions reaching Login
    for i in range(100):
        uid = f"ANON-{i}"
        events.append({"anonymous_session_id": uid, "workflow_stage": "Login", "event_type": "ENTERED", "consent_status": "CONSENTED"})
        events.append({"anonymous_session_id": uid, "workflow_stage": "Login", "event_type": "COMPLETED", "consent_status": "CONSENTED"})
        events.append({"anonymous_session_id": uid, "workflow_stage": "Document Upload", "event_type": "ENTERED", "consent_status": "CONSENTED"})
        if i < 50:
            events.append({"anonymous_session_id": uid, "workflow_stage": "Document Upload", "event_type": "COMPLETED", "consent_status": "CONSENTED"})
        else:
            events.append({"anonymous_session_id": uid, "workflow_stage": "Document Upload", "event_type": "ABANDONED", "consent_status": "CONSENTED"})

    df = pd.DataFrame(events)

    # 1. Baseline
    base_res = compute_non_private_baseline(df)
    assert base_res["top_abandonment_stage"] == "Document Upload"
    assert base_res["max_abandonment_rate"] == 0.5

    # 2. Differential privacy
    dp_res = run_privacy_preserving_analytics(df, epsilon=1.0, seed=42)
    assert dp_res["top_abandonment_stage"] == "Document Upload"
    assert abs(dp_res["max_abandonment_rate"] - 0.5) < 0.15
