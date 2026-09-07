"""
End-to-End Acceptance Test
Verifies the complete end-to-end pipeline:
Synthetic Data Generation -> Consent Filtering -> Anonymisation -> Aggregation ->
Small Group Suppression -> Differential Privacy -> Journey Abandonment Analytics ->
Baseline Comparison -> Analytics Failure Isolation -> Rollback & Restoration.
"""

import sys
import os
import pytest
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from scripts.generate_data import generate_synthetic_data
from privacy.consent import filter_consented_events, validate_event_consent
from privacy.anonymization import sanitize_event, generate_anonymous_session_id
from privacy.aggregation import aggregate_stage_metrics
from privacy.suppression import apply_small_group_suppression, check_and_suppress_count
from privacy.differential_privacy import LaplaceMechanism, PrivacyBudgetManager, BudgetExhaustedError
from experiments.baseline import compute_non_private_baseline
from experiments.metrics import compute_mae, compute_top_stage_accuracy
from app.analytics import run_privacy_preserving_analytics
from app.rollback import RollbackController, SystemMode


def test_complete_end_to_end_pipeline(tmp_path):
    """
    Executes and validates the entire lifecycle from generation to DP analytics,
    baseline benchmarking, and zero-downtime coexistence rollback.
    """
    # 1. Synthetic Data Generation
    db_file = str(tmp_path / "e2e_portal.db")
    df_events = generate_synthetic_data(
        num_sessions=1000,  # fast test volume
        seed=123,
        output_dir=str(tmp_path),
        db_path=db_file
    )
    assert len(df_events) > 3000
    assert df_events['anonymous_session_id'].nunique() == 1000
    assert "Document Upload" in df_events['workflow_stage'].values

    # 2. Consent Filtering
    df_consented, consent_stats = filter_consented_events(df_events)
    assert len(df_consented) < len(df_events)
    assert (df_consented['consent_status'] == "CONSENTED").all()
    assert consent_stats['consented_count'] == len(df_consented)

    # 3. Anonymisation & PII Stripping
    raw_event = {
        "event_id": "EVT-TEST-999",
        "name": "Jane Doe",
        "email": "jane@example.com",
        "policy_number": "POL-12345",
        "session_id": "RAW-SESSION-123",
        "workflow_stage": "Document Upload",
        "event_type": "ENTERED",
        "created_at": "2026-09-07T14:30:15Z"
    }
    sanitized = sanitize_event(raw_event)
    assert "name" not in sanitized
    assert "email" not in sanitized
    assert "policy_number" not in sanitized
    assert sanitized["anonymous_session_id"].startswith("ANON-")
    assert sanitized["timestamp_bucket"] == "2026-09-07 14:00:00"

    # 4. Non-Private Baseline Computation
    baseline_res = compute_non_private_baseline(df_events)
    assert baseline_res["top_abandonment_stage"] == "Document Upload"
    assert baseline_res["max_abandonment_rate"] > 0.15

    # 5. Privacy-Preserving Analytics Pipeline (DP + Suppression)
    budget_mgr = PrivacyBudgetManager(total_budget=1.0, db_path=db_file)
    analytics_out = run_privacy_preserving_analytics(
        df_events=df_events,
        epsilon=0.5,
        min_group_size=10,
        budget_manager=budget_mgr,
        seed=42
    )
    assert analytics_out["success"] is True
    assert analytics_out["top_abandonment_stage"] == "Document Upload"
    assert budget_mgr.get_remaining_budget() == pytest.approx(0.5, abs=1e-4)

    # 6. Accuracy Metrics Verification
    df_base = baseline_res["summary_df"]
    df_dp = analytics_out["private_df"]
    mae = compute_mae(df_base["abandonment_rate"], df_dp["abandonment_rate"])
    top_acc = compute_top_stage_accuracy(baseline_res["top_abandonment_stage"], analytics_out["top_abandonment_stage"])
    assert mae < 0.05
    assert top_acc == 1.0

    # 7. Privacy Budget Enforcement
    analytics_out2 = run_privacy_preserving_analytics(
        df_events=df_events,
        epsilon=0.5,
        min_group_size=10,
        budget_manager=budget_mgr,
        seed=43
    )
    assert analytics_out2["success"] is True
    assert budget_mgr.get_remaining_budget() == pytest.approx(0.0, abs=1e-4)

    # Budget exhaustion must reject subsequent query
    with pytest.raises(BudgetExhaustedError):
        run_privacy_preserving_analytics(
            df_events=df_events,
            epsilon=0.1,
            budget_manager=budget_mgr
        )

    # 8. Legacy Coexistence & Non-Blocking Rollback
    controller = RollbackController(db_path=db_file)
    assert controller.current_mode == SystemMode.COEXISTENCE

    # Simulate catastrophic analytics service crash
    controller.simulate_analytics_failure()
    assert controller.current_mode == SystemMode.LEGACY_FALLBACK

    # Legacy claim creation and submission MUST succeed without exception
    claim_emitted = controller.dispatch_event_adapter({
        "event_id": "EVT-EMERGENCY-01",
        "anonymous_session_id": "ANON-9999",
        "workflow_stage": "Submit",
        "event_type": "COMPLETED"
    })
    assert claim_emitted is True

    # Restore analytics back to COEXISTENCE
    controller.restore_analytics_service()
    assert controller.current_mode == SystemMode.COEXISTENCE
    assert controller.is_analytics_failed is False
