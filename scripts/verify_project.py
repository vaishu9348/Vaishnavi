"""
Final Automated Project Verification Script
Performs a comprehensive automated health, functionality, privacy, and evidence check
across the entire Insurance Privacy Journey Analytics Platform repository.
"""

import os
import sys
import pandas as pd
import sqlite3

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

def verify_all():
    print("=" * 45)
    print("PROJECT VERIFICATION")
    print("=" * 45)

    failures = []

    # 1. Data generation check
    data_csv = os.path.join(PROJECT_ROOT, "data", "synthetic", "interaction_events.csv")
    if os.path.exists(data_csv):
        df_events = pd.read_csv(data_csv)
        sessions = df_events['anonymous_session_id'].nunique() if 'anonymous_session_id' in df_events.columns else 0
        events = len(df_events)
        if sessions >= 10000 and events >= 50000:
            print(f"Data generation PASS ({sessions:,} sessions, {events:,} events)")
        else:
            print(f"Data generation FAIL (Expected >=10k sessions, got {sessions})")
            failures.append(("Data generation", f"Insufficient volume: {sessions} sessions, {events} events", "Run scripts/generate_data.py --sessions 10000"))
    else:
        print("Data generation FAIL (File missing)")
        failures.append(("Data generation", "interaction_events.csv missing", "Run scripts/generate_data.py"))

    # 2. Consent check
    try:
        from privacy.consent import validate_event_consent, filter_consented_events
        c_true = validate_event_consent("CONSENTED")
        c_false = validate_event_consent("UNKNOWN")
        c_none = validate_event_consent(None)
        if c_true and not c_false and not c_none:
            print("Consent PASS")
        else:
            print("Consent FAIL")
            failures.append(("Consent", "Consent validation logic returned unexpected values", "Check privacy/consent.py"))
    except Exception as e:
        print(f"Consent FAIL ({e})")
        failures.append(("Consent", str(e), "Fix privacy/consent.py"))

    # 3. Anonymisation check
    try:
        from privacy.anonymization import generate_anonymous_session_id, bucketize_timestamp, sanitize_event
        anon_id = generate_anonymous_session_id("test_user_123")
        ts = bucketize_timestamp("2026-09-07T14:32:15Z")
        cleaned = sanitize_event({"name": "Alice", "email": "alice@test.com", "session_id": "test_raw"})
        if anon_id.startswith("ANON-") and "name" not in cleaned and "email" not in cleaned:
            print("Anonymisation PASS")
        else:
            print("Anonymisation FAIL")
            failures.append(("Anonymisation", "PII not stripped or anonymous format invalid", "Check privacy/anonymization.py"))
    except Exception as e:
        print(f"Anonymisation FAIL ({e})")
        failures.append(("Anonymisation", str(e), "Fix privacy/anonymization.py"))

    # 4. Aggregation check
    try:
        from privacy.aggregation import aggregate_stage_metrics
        agg_res = aggregate_stage_metrics(df_events[df_events['consent_status'] == 'CONSENTED'])
        if len(agg_res.stages) == 8 and agg_res.top_abandonment_stage == "Document Upload":
            print("Aggregation PASS")
        else:
            print(f"Aggregation FAIL (Stages: {len(agg_res.stages)}, Top: {agg_res.top_abandonment_stage})")
            failures.append(("Aggregation", "Aggregation output stages invalid", "Check privacy/aggregation.py"))
    except Exception as e:
        print(f"Aggregation FAIL ({e})")
        failures.append(("Aggregation", str(e), "Fix privacy/aggregation.py"))

    # 5. Suppression check
    try:
        from privacy.suppression import check_and_suppress_count
        supp_low = check_and_suppress_count(3, min_group_size=10)
        supp_high = check_and_suppress_count(15, min_group_size=10)
        if supp_low.is_suppressed and not supp_high.is_suppressed:
            print("Suppression PASS")
        else:
            print("Suppression FAIL")
            failures.append(("Suppression", "k=10 suppression logic failed boundary check", "Check privacy/suppression.py"))
    except Exception as e:
        print(f"Suppression FAIL ({e})")
        failures.append(("Suppression", str(e), "Fix privacy/suppression.py"))

    # 6. Differential Privacy check
    try:
        from privacy.differential_privacy import LaplaceMechanism, InvalidEpsilonError
        dp = LaplaceMechanism(epsilon=1.0)
        noise = dp.draw_noise()
        noisy_count = dp.perturb_count(100)
        bounds_ok = False
        try:
            LaplaceMechanism.validate_epsilon(2.0)
        except InvalidEpsilonError:
            bounds_ok = True
        if bounds_ok and dp.epsilon <= 1.0 and noisy_count >= 0:
            print("Differential Privacy PASS")
        else:
            print("Differential Privacy FAIL")
            failures.append(("Differential Privacy", "Epsilon bound validation failed", "Check privacy/differential_privacy.py"))
    except Exception as e:
        print(f"Differential Privacy FAIL ({e})")
        failures.append(("Differential Privacy", str(e), "Fix privacy/differential_privacy.py"))

    # 7. Privacy Budget check
    try:
        from privacy.differential_privacy import PrivacyBudgetManager, BudgetExhaustedError
        mgr = PrivacyBudgetManager(total_budget=1.0)
        mgr.request_budget(0.5)
        rem = mgr.get_remaining_budget()
        if abs(rem - 0.5) < 1e-4:
            print("Privacy Budget PASS")
        else:
            print(f"Privacy Budget FAIL (Remaining: {rem})")
            failures.append(("Privacy Budget", f"Budget balance incorrect: {rem}", "Check privacy/differential_privacy.py"))
    except Exception as e:
        print(f"Privacy Budget FAIL ({e})")
        failures.append(("Privacy Budget", str(e), "Fix privacy/differential_privacy.py"))

    # 8. Baseline check
    try:
        from experiments.baseline import compute_non_private_baseline
        b_res = compute_non_private_baseline(df_events)
        if b_res["top_abandonment_stage"] == "Document Upload":
            print("Baseline PASS")
        else:
            print(f"Baseline FAIL (Top stage: {b_res['top_abandonment_stage']})")
            failures.append(("Baseline", f"Expected Document Upload, got {b_res['top_abandonment_stage']}", "Check data generator"))
    except Exception as e:
        print(f"Baseline FAIL ({e})")
        failures.append(("Baseline", str(e), "Fix experiments/baseline.py"))

    # 9. Experiments check
    exp_csv = os.path.join(PROJECT_ROOT, "reports", "experiment_summary.csv")
    if os.path.exists(exp_csv):
        exp_df = pd.read_csv(exp_csv)
        if len(exp_df) >= 5 and (exp_df['top_stage_correct'] == 1.0).all():
            print("Experiments PASS")
        else:
            print("Experiments FAIL (Insufficient rows or incorrect top stage)")
            failures.append(("Experiments", "Experiment summary invalid", "Run scripts/run_experiment.py"))
    else:
        print("Experiments FAIL (Missing experiment_summary.csv)")
        failures.append(("Experiments", "experiment_summary.csv missing", "Run scripts/run_experiment.py"))

    # 10. Failure Testing check
    fail_csv = os.path.join(PROJECT_ROOT, "reports", "failure_results.csv")
    if os.path.exists(fail_csv):
        fail_df = pd.read_csv(fail_csv)
        if len(fail_df) >= 8 and (fail_df['passed'] == True).all():
            print("Failure Testing PASS")
        else:
            print("Failure Testing FAIL")
            failures.append(("Failure Testing", "Not all 8 failure tests passed", "Run scripts/run_experiment.py"))
    else:
        print("Failure Testing FAIL (Missing failure_results.csv)")
        failures.append(("Failure Testing", "failure_results.csv missing", "Run scripts/run_experiment.py"))

    # 11. Legacy Coexistence check
    try:
        from app.rollback import RollbackController, SystemMode
        controller = RollbackController()
        if controller.current_mode == SystemMode.COEXISTENCE:
            print("Legacy Coexistence PASS")
        else:
            print(f"Legacy Coexistence FAIL (Mode: {controller.current_mode})")
            failures.append(("Legacy Coexistence", f"Initial mode not COEXISTENCE: {controller.current_mode}", "Check app/rollback.py"))
    except Exception as e:
        print(f"Legacy Coexistence FAIL ({e})")
        failures.append(("Legacy Coexistence", str(e), "Fix app/rollback.py"))

    # 12. Rollback check
    try:
        controller.simulate_analytics_failure()
        f_mode = controller.current_mode == SystemMode.LEGACY_FALLBACK
        dispatched = controller.dispatch_event_adapter({"event_id": "EVT-TEST", "workflow_stage": "Login"})
        controller.restore_services()
        r_mode = controller.current_mode == SystemMode.COEXISTENCE
        if f_mode and dispatched and r_mode:
            print("Rollback PASS")
        else:
            print("Rollback FAIL")
            failures.append(("Rollback", "Rollback transition or dispatch failed", "Check app/rollback.py"))
    except Exception as e:
        print(f"Rollback FAIL ({e})")
        failures.append(("Rollback", str(e), "Fix app/rollback.py"))

    # 13. Security Tests check
    try:
        import pytest
        ret_code = pytest.main(["-q", os.path.join(PROJECT_ROOT, "tests", "test_security.py")])
        if ret_code == 0:
            print("Security Tests PASS")
        else:
            print("Security Tests FAIL")
            failures.append(("Security Tests", "Security test module failed", "Run pytest tests/test_security.py"))
    except Exception as e:
        print(f"Security Tests FAIL ({e})")
        failures.append(("Security Tests", str(e), "Check tests/test_security.py"))

    # 14. Documentation check
    required_docs = [
        "architecture.md", "requirements.md", "field_workflow_map.md",
        "privacy_model.md", "threat_model.md", "failure_mode_analysis.md",
        "rollback_plan.md", "experiment_methodology.md", "technical_documentation.md",
        "user_feedback.md", "requirement_traceability.md"
    ]
    missing_docs = [d for d in required_docs if not os.path.exists(os.path.join(PROJECT_ROOT, "docs", d))]
    if not missing_docs:
        print("Documentation PASS")
    else:
        print(f"Documentation FAIL (Missing: {missing_docs})")
        failures.append(("Documentation", f"Missing doc files: {missing_docs}", "Create missing docs"))

    # 15. Presentation check
    pptx_path = os.path.join(PROJECT_ROOT, "docs", "Insurance_Privacy_Journey_Analytics_Presentation.pptx")
    if os.path.exists(pptx_path):
        print("Presentation PASS")
    else:
        print("Presentation FAIL (Missing PPTX)")
        failures.append(("Presentation", "Presentation PPTX missing", "Run scripts/generate_presentation.py"))

    print("=" * 45)
    if not failures:
        print("FINAL STATUS: PASS")
        print("=" * 45)
        return True
    else:
        print("FINAL STATUS: FAIL")
        print("=" * 45)
        print("\nFAILED COMPONENTS:")
        for comp, reason, fix in failures:
            print(f"  • {comp}: {reason} -> Fix: {fix}")
        return False

if __name__ == '__main__':
    success = verify_all()
    sys.exit(0 if success else 1)
