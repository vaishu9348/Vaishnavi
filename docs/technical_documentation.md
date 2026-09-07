# Technical Documentation & Developer Guide

This document provides complete technical specifications for engineers maintaining or extending the Insurance Privacy Journey Analytics Platform.

## 1. Directory Structure

```text
insurance-privacy-analytics/
├── app/
│   ├── dashboard.py           # Streamlit Multi-Page Enterprise Analytics UI
│   ├── legacy_portal.py       # Simulated Legacy Claims Processing Portal
│   ├── analytics.py           # Core privacy analytics aggregation engine
│   ├── health.py              # Health check monitoring & endpoint
│   └── rollback.py            # Coexistence, fallback & rollback state machine
├── privacy/
│   ├── consent.py             # Strict consent enforcement
│   ├── anonymization.py       # PII stripping & session ID hashing
│   ├── aggregation.py         # Macro stage counts (zero individual traces)
│   ├── suppression.py         # Small-group suppression (k-anonymity, k=10)
│   └── differential_privacy.py# Laplace mechanism & Privacy Budget Manager
├── data/
│   ├── raw/                   # Raw generated telemetry CSVs
│   ├── processed/             # Consented events CSVs
│   └── synthetic/             # Synthetic events and SQLite database
├── scripts/
│   ├── generate_data.py       # Generates 10,000+ sessions / 50,000+ events
│   ├── initialize_db.py       # SQLite database initialization
│   ├── run_experiment.py      # Automated benchmark across epsilons
│   └── create_notebooks.py    # Generates the 7 Jupyter notebooks
├── experiments/
│   ├── baseline.py            # Non-private ground truth reference
│   ├── evaluation.py          # Multi-trial privacy-utility evaluation
│   └── metrics.py             # MAE, MAPE, Top-Stage Accuracy, Spearman Rank
├── notebooks/                 # 7 Comprehensive Jupyter notebooks
├── tests/                     # 11 Pytest unit & security test files
├── docs/                      # Complete technical & operational docs
├── reports/                   # CSV results & high-res PNG charts
├── requirements.txt           # Pip dependencies
├── .env.example               # Environment variables
└── README.md                  # Comprehensive project documentation
```

## 2. Database Schema (SQLite)

* `interaction_events`:
  - `event_id` (TEXT, PK): Unique event identifier.
  - `anonymous_session_id` (TEXT): Salted cryptographic hash token (`ANON-XXXX-XXXX`).
  - `workflow_stage` (TEXT): One of the 8 canonical stages.
  - `event_type` (TEXT): `ENTERED`, `COMPLETED`, `ABANDONED`, `ERROR`.
  - `timestamp_bucket` (TEXT): Bucketized to nearest hour (`YYYY-MM-DD HH:00:00`).
  - `consent_status` (TEXT): `CONSENTED`, `NOT_CONSENTED`, `UNKNOWN`.
  - `portal_version` (TEXT): Adapter release identifier.
  - `event_source` (TEXT): Generating client application.
  - `created_at` (TEXT): ISO timestamp.

* `claims`:
  - `claim_id` (TEXT, PK): Legacy claim reference number (`CLM-2026-XXXX`).
  - `customer_id` (TEXT): Anonymous customer identifier.
  - `claim_type` (TEXT): Claim category (Vehicle, Health, Property, Travel).
  - `claim_description` (TEXT): Synthetic incident description.
  - `amount_estimated` (REAL): Estimated claim loss amount.
  - `status` (TEXT): `SUBMITTED` or `DRAFT_ABANDONED`.
  - `created_at` (TEXT): ISO timestamp.
  - `processed_mode` (TEXT): Operational mode during processing.

* `privacy_budget`:
  - `budget_id` (INTEGER, PK): Primary key (Row 1).
  - `total_epsilon` (REAL): Maximum allowed privacy budget (default 1.0).
  - `consumed_epsilon` (REAL): Cumulative epsilon consumed.
  - `remaining_epsilon` (REAL): Remaining budget.
  - `query_count` (INTEGER): Number of executed analytics queries.
  - `updated_at` (TEXT): Timestamp of last ledger transaction.

---

## 3. Operational Telemetry & Fault Traps

The `RollbackController` implements a non-blocking fault barrier:
```python
def dispatch_event_adapter(self, event_data: Dict[str, Any]) -> bool:
    if self._current_mode == SystemMode.LEGACY or self._analytics_simulated_failed:
        return True  # Silently bypass analytics; customer claim succeeds
    try:
        # Ingestion logic...
        return True
    except Exception:
        # Failsafe: Never raise exceptions into customer claim thread
        return True
```
