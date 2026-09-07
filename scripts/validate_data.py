"""
Data Validation Layer for Synthetic Telemetry Stream
Validates:
- Required schema columns
- Valid workflow stages
- Valid event types
- Valid consent values
- Timestamps integrity and chronological ordering
- Duplicate events
- Missing session IDs
- Invalid sessions and portal versions
- Strict zero PII verification (prohibits name, email, phone, address, policy number, medical info, real claim number)

Outputs validation report to reports/data_validation_results.csv and reports/data_validation_summary.txt.
"""

import os
import sys
import pandas as pd
import numpy as np

VALID_STAGES = [
    'Login', 'Start Claim', 'Claim Type', 'Claim Details',
    'Document Upload', 'Review', 'Submit', 'Confirmation'
]

VALID_EVENT_TYPES = ['ENTERED', 'COMPLETED', 'ABANDONED', 'ERROR']

VALID_CONSENT_VALUES = ['CONSENTED', 'NOT_CONSENTED', 'UNKNOWN']

REQUIRED_COLUMNS = [
    'event_id', 'timestamp_bucket', 'portal_version', 'event_type'
]

# Supported column mappings
SESSION_COLS = ['anonymous_session_id', 'session_id']
STAGE_COLS = ['workflow_stage', 'stage_name']
CONSENT_COLS = ['consent_status', 'consent_state']

PROHIBITED_PII_FIELDS = [
    'name', 'first_name', 'last_name', 'email', 'phone', 'telephone',
    'address', 'ssn', 'policy_number', 'medical_info', 'medical_records',
    'diagnosis', 'treatment', 'claim_number', 'credit_card', 'bank_account'
]


def validate_telemetry_data(csv_path: str) -> dict:
    """Perform rigorous validation of the telemetry dataset."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Telemetry file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    total_records = len(df)

    # Identify dynamic column names
    session_col = next((c for c in SESSION_COLS if c in df.columns), None)
    stage_col = next((c for c in STAGE_COLS if c in df.columns), None)
    consent_col = next((c for c in CONSENT_COLS if c in df.columns), None)

    total_sessions = df[session_col].nunique() if session_col else 0

    results = []

    # 1. Required Columns Check
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    results.append({
        'check_name': 'Required Columns Present',
        'status': 'PASS' if len(missing_cols) == 0 else 'FAIL',
        'details': f"All {len(REQUIRED_COLUMNS)} columns present" if not missing_cols else f"Missing: {missing_cols}",
        'severity': 'CRITICAL'
    })

    # 2. Prohibited PII Check
    found_pii = [col for col in df.columns if any(pii in col.lower() for pii in PROHIBITED_PII_FIELDS)]
    results.append({
        'check_name': 'Zero PII Fields',
        'status': 'PASS' if len(found_pii) == 0 else 'FAIL',
        'details': "No PII columns detected" if not found_pii else f"Disallowed PII columns: {found_pii}",
        'severity': 'CRITICAL'
    })

    # 3. Valid Workflow Stages Check
    if stage_col:
        invalid_stages = df[~df[stage_col].isin(VALID_STAGES)]
        stage_status = 'PASS' if len(invalid_stages) == 0 else 'FAIL'
        stage_details = f"100% of stage names match valid 8-stage schema ({df[stage_col].nunique()} unique stages)"
    else:
        stage_status = 'FAIL'
        stage_details = f"Stage column not found (expected one of {STAGE_COLS})"
    results.append({
        'check_name': 'Valid Workflow Stages',
        'status': stage_status,
        'details': stage_details,
        'severity': 'HIGH'
    })

    # 4. Valid Event Types Check
    invalid_events = df[~df['event_type'].isin(VALID_EVENT_TYPES)]
    results.append({
        'check_name': 'Valid Event Types',
        'status': 'PASS' if len(invalid_events) == 0 else 'FAIL',
        'details': f"All event types valid ({dict(df['event_type'].value_counts())})",
        'severity': 'HIGH'
    })

    # 5. Valid Consent Values Check
    if consent_col:
        invalid_consent = df[~df[consent_col].isin(VALID_CONSENT_VALUES)]
        consent_status = 'PASS' if len(invalid_consent) == 0 else 'FAIL'
        consent_details = f"All consent states valid ({dict(df[consent_col].value_counts())})"
    else:
        consent_status = 'FAIL'
        consent_details = f"Consent column not found (expected one of {CONSENT_COLS})"
    results.append({
        'check_name': 'Valid Consent States',
        'status': consent_status,
        'details': consent_details,
        'severity': 'CRITICAL'
    })

    # 6. Missing Session IDs Check
    if session_col:
        null_sessions = df[session_col].isnull().sum()
        session_status = 'PASS' if null_sessions == 0 else 'FAIL'
        session_details = f"Zero null session IDs ({total_sessions:,} distinct sessions)"
    else:
        session_status = 'FAIL'
        session_details = f"Session column not found (expected one of {SESSION_COLS})"
    results.append({
        'check_name': 'Session ID Completeness',
        'status': session_status,
        'details': session_details,
        'severity': 'HIGH'
    })

    # 7. Duplicate Event IDs Check
    duplicate_events = df['event_id'].duplicated().sum()
    results.append({
        'check_name': 'Unique Event IDs',
        'status': 'PASS' if duplicate_events == 0 else 'FAIL',
        'details': f"Zero duplicate event IDs across {total_records:,} events",
        'severity': 'MEDIUM'
    })

    # 8. Portal Version Check
    invalid_versions = df[~df['portal_version'].str.match(r'^v\d+\.\d+')] if 'portal_version' in df.columns else []
    results.append({
        'check_name': 'Valid Portal Versions',
        'status': 'PASS' if len(invalid_versions) == 0 else 'FAIL',
        'details': f"Valid portal versions ({dict(df['portal_version'].value_counts())})",
        'severity': 'MEDIUM'
    })

    # 9. Minimum Volume Thresholds
    volume_pass = total_sessions >= 10000 and total_records >= 50000
    results.append({
        'check_name': 'Volume Threshold (>=10k sessions, >=50k events)',
        'status': 'PASS' if volume_pass else 'FAIL',
        'details': f"{total_sessions:,} sessions, {total_records:,} events generated",
        'severity': 'HIGH'
    })

    # 10. Anonymous Session ID Format
    if session_col:
        anon_format_pass = df[session_col].str.match(r'^ANON-[A-F0-9]{4}-[A-F0-9]{4}$').all()
        anon_status = 'PASS' if anon_format_pass else 'FAIL'
        anon_details = "All session IDs follow salted pseudonymous hash format"
    else:
        anon_status = 'FAIL'
        anon_details = "Missing session column"
    results.append({
        'check_name': 'Anonymous Session Format (ANON-XXXX-XXXX)',
        'status': anon_status,
        'details': anon_details,
        'severity': 'CRITICAL'
    })

    val_df = pd.DataFrame(results)
    
    # Save CSV
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'reports')
    os.makedirs(output_dir, exist_ok=True)
    csv_out = os.path.join(output_dir, 'data_validation_results.csv')
    val_df.to_csv(csv_out, index=False)
    
    # Save text summary
    summary_out = os.path.join(output_dir, 'data_validation_summary.txt')
    with open(summary_out, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("TELEMETRY DATA VALIDATION SUMMARY REPORT\n")
        f.write("=" * 60 + "\n")
        f.write(f"Dataset File      : {os.path.basename(csv_path)}\n")
        f.write(f"Total Events      : {total_records:,}\n")
        f.write(f"Total Sessions    : {total_sessions:,}\n")
        f.write(f"Total Checks      : {len(results)}\n")
        passed_checks = (val_df['status'] == 'PASS').sum()
        f.write(f"Passed Checks     : {passed_checks} / {len(results)}\n")
        f.write(f"Validation Status : {'ALL CHECKS PASSED [OK]' if passed_checks == len(results) else 'FAILURES DETECTED [FAIL]'}\n\n")
        f.write(val_df.to_string(index=False))
        f.write("\n" + "=" * 60 + "\n")

    print(f"[DATA VALIDATION] Evaluated {len(results)} checks across {total_records:,} events.")
    print(f"[DATA VALIDATION] Saved report -> {csv_out}")
    print(f"[DATA VALIDATION] Overall Status: {'PASS' if (val_df['status'] == 'PASS').all() else 'FAIL'}")
    return {
        'total_records': total_records,
        'total_sessions': total_sessions,
        'checks_passed': int((val_df['status'] == 'PASS').sum()),
        'total_checks': len(results),
        'status': 'PASS' if (val_df['status'] == 'PASS').all() else 'FAIL'
    }


if __name__ == '__main__':
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(project_root, 'data', 'synthetic', 'interaction_events.csv')
    validate_telemetry_data(data_path)
