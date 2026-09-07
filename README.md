# Insurance Privacy Journey Analytics Platform
### From Operational Pain to Working Product: Legacy Insurance Claims Portal Modernised Without Stopping

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests: Pytest](https://img.shields.io/badge/tests-pytest-green.svg)](tests/)
[![Framework: Streamlit](https://img.shields.io/badge/UI-Streamlit-red.svg)](https://streamlit.io/)

---

## 1. Project Overview

The **Insurance Privacy Journey Analytics Platform** is a working, enterprise-grade proof-of-concept demonstrating how a mission-critical legacy insurance claims portal can be modernised to uncover customer drop-off bottlenecks **without collecting invasive personal data** and **without interrupting daily claim processing operations**.

Modern insurance customers abandon multi-step claim submissions, yet product teams cannot identify friction points without violating privacy principles. This platform introduces a **privacy-preserving journey analytics pipeline** employing strict consent enforcement, one-way session anonymisation, macro aggregation, small-group suppression ($k=10$), and Laplace Differential Privacy ($\epsilon \le 1.0$) operating in non-blocking coexistence alongside the legacy claims system.

---

## 2. Problem Statement

* **The Operational Pain**: Insurance policyholders navigate an 8-stage claims process (`Login` → `Start Claim` → `Claim Type` → `Claim Details` → `Document Upload` → `Review` → `Submit` → `Confirmation`). Many abandon the journey, but product managers cannot determine where or why.
* **The Privacy Imperative**: The organisation refuses to deploy invasive tracking (e.g. session replays, keystroke loggers, device fingerprints, or reverse identity mappings) merely to understand workflow behavior.
* **The Business Risk**: Any modernisation that risks disrupting claim submissions is unacceptable. Legacy claim processing must continue operating with 100% availability even if the analytics subsystem fails.

---

## 3. Primary Objectives

1. **Identify the Bottleneck**: Answer with quantitative statistical confidence: *"Which workflow stage has the highest abandonment rate?"* (Identified: **Document Upload** at ~30% drop-off).
2. **Quantify Accuracy Under Privacy**: Measure how accurately journey abandonment rates can be estimated while operating strictly under a bounded differential privacy budget ($\epsilon \le 1.0$).
3. **Guarantee Legacy Coexistence**: Prove that total failure of the analytics service never interrupts core insurance claims processing.
4. **Prevent Privacy Misuse**: Provide active defenses against individual journey lookups, small-group inference, consent bypass, and privacy budget exhaustion.

---

## 4. System Architecture

```text
                                  CUSTOMER (POLICYHOLDER)
                                             |
                                             v
                             +-------------------------------+
                             |     LEGACY CLAIMS PORTAL      |
                             +---------------+---------------+
                                             |
                   +-------------------------+-------------------------+
                   | (Synchronous Critical)                            | (Asynchronous Telemetry)
                   v                                                   v
        +---------------------+                             +---------------------+
        |  CLAIM PROCESSING   |                             |    EVENT ADAPTER    |
        +----------+----------+                             +----------+----------+
                   |                                                   |
                   v                                                   v
        +---------------------+                             +---------------------+
        |   LEGACY DATABASE   |                             |   PRIVACY GATEWAY   |
        |  (Claims & Policy)  |                             +----------+----------+
        +---------------------+                                        |
                                                                       v
                                                  +--------------------+--------------------+
                                                  |                                         |
                                                  v                                         v
                                       +---------------------+                   +---------------------+
                                       |   CONSENT FILTER    |                   |    ANONYMISATION    |
                                       |  (CONSENTED only)   |                   |  (Zero PII / Salt)  |
                                       +----------+----------+                   +----------+----------+
                                                  |                                         |
                                                  +--------------------+--------------------+
                                                                       |
                                                                       v
                                                            +---------------------+
                                                            |  AGGREGATION LAYER  |
                                                            |  (Stage Counts)     |
                                                            +----------+----------+
                                                                       |
                                                                       v
                                                            +---------------------+
                                                            |   SUPPRESSION (k)   |
                                                            |  (k >= 10 mask)     |
                                                            +----------+----------+
                                                                       |
                                                                       v
                                                            +---------------------+
                                                            | DIFFERENTIAL PRIVACY|
                                                            | (Laplace, eps<=1.0) |
                                                            +----------+----------+
                                                                       |
                                                                       v
                                                            +---------------------+
                                                            |  JOURNEY ANALYTICS  |
                                                            |  (Rates & Bottleneck|
                                                            +----------+----------+
                                                                       |
                                                                       v
                                                            +---------------------+
                                                            | ANALYTICS DASHBOARD |
                                                            | (Streamlit Enterprise)
                                                            +----------+----------+
                                                                       |
                                                                       v
                                                            +---------------------+
                                                            |  PRODUCT / PM TEAM  |
                                                            +---------------------+
```

---

## 5. Technology Stack

* **Frontend UI**: Streamlit 1.63 (Dual Visual Identities: Modern Dark Glassmorphic Dashboard & Retro Utilitarian Legacy Portal)
* **Backend & Analytics**: Python 3.11, Pandas, NumPy, SQLite
* **Visualization**: Plotly 7.0 (Interactive funnels, trade-off curves, grouped error breakdowns) & Matplotlib
* **Privacy Engine**: Laplace Differential Privacy Mechanism, Privacy Budget Manager, k-Anonymity Suppression
* **Test Suite**: Pytest (11 test modules covering failure modes, security misuse, and statistical bounds)

---

## 6. Privacy Approach & Defense-in-Depth

The platform enforces five layers of privacy protection:
1. **Data Minimisation**: Prohibited fields (`name`, `email`, `phone`, `policy_number`, `medical_info`, `claim_number`) are stripped at ingestion.
2. **Explicit Consent Gateway**: Default is conservative zero-consent. Only records explicitly tagged `CONSENTED` enter aggregation; `NOT_CONSENTED` and `UNKNOWN` are dropped.
3. **One-Way Session Hashing & Bucketization**: Anonymous session tokens (`ANON-XXXX-XXXX`) use salted SHA-256 hashes without reversible mappings. Timestamps are coarsened to 1-hour windows.
4. **Small-Group Suppression ($k=10$)**: Aggregate cohort counts $< 10$ are masked with `[SUPPRESSED < 10]`.
5. **Laplace Differential Privacy ($\epsilon \le 1.0$)**: Count queries receive calibrated Laplace noise ($b = 1/\epsilon$) bounded by a persistent privacy budget ledger.

---

## 7. Dataset Generation

The project includes a realistic synthetic telemetry generator (`scripts/generate_data.py`):
```bash
python scripts/generate_data.py --sessions 10000
```
* **Sessions**: 10,000+ customer sessions
* **Events**: 50,000+ interaction events (`ENTERED`, `COMPLETED`, `ABANDONED`, `ERROR`)
* **Realistic Stage Probabilities**:
  - `Login`: 100%
  - `Start Claim`: 98%
  - `Claim Type`: 95%
  - `Claim Details`: 88%
  - **`Document Upload`**: **70%** (Primary realistic bottleneck)
  - `Review`: 92%
  - `Submit`: 96%
  - `Confirmation`: 100%
* **Multi-Journey Patterns**: Successful completions, detail dropouts, document upload abandonments, review exits, and error-recovery retries.
* **Consent Distribution**: ~80% `CONSENTED`, ~15% `NOT_CONSENTED`, ~5% `UNKNOWN`.

---

## 8. Installation

Clone repository and activate a Python virtual environment:
```bash
cd insurance-privacy-analytics
python -m venv .venv

# On Windows:
.\.venv\Scripts\activate

# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

---

## 9. Running Instructions

### Step 1: Initialize Database & Generate Synthetic Telemetry
```bash
python scripts/generate_data.py --sessions 10000
```

### Step 2: Run Automated Benchmarks & Generate Charts
```bash
python scripts/run_experiment.py
```

### Step 3: Launch Enterprise Analytics Dashboard
```bash
streamlit run app/dashboard.py
```
The dashboard will open automatically in your browser at `http://localhost:8501`.

---

## 10. Dashboard Structure & Navigation

The dashboard provides 10 integrated pages:
1. **Overview**: High-level KPIs, executive summary, architecture blueprint, system status.
2. **Journey Analytics**: Interactive Plotly funnel chart, stage volume drop-offs.
3. **Abandonment Analysis**: Stage abandonment comparison, Document Upload friction diagnostics, operational recommendations.
4. **Privacy & Consent**: Ingestion gate breakdown, data minimisation architecture, live privacy budget ledger.
5. **Baseline Comparison**: Side-by-side ground truth vs differentially private estimates, MAE/MAPE error metrics.
6. **Experiment Results**: Interactive $\epsilon$ slider, error vs accuracy trade-off curves, benchmark summary table.
7. **Failure Testing**: Interactive execution of 5 failure modes and 5 privacy misuse tests.
8. **System Health**: Telemetry status of Legacy Portal, Analytics Service, Gateway, and SQLite Database.
9. **Rollback Demo**: Live coexistence demonstration, analytics failure simulation, and legacy fallback verification.
10. **Legacy Claims Portal**: Functional simulation of the utilitarian insurance claims submission flow.

---

## 11. Experiment Methodology & Setup

The experimental evaluation runs controlled trials across privacy budgets $\epsilon \in \{0.1, 0.25, 0.5, 0.75, 1.0\}$ over 20 independent randomized trials on 126,204 interaction events:
* **Sensitivity**: $\Delta f = 1$ (1 customer session = 1 journey contribution)
* **Metrics**: Mean Absolute Error (MAE), Mean Absolute Percentage Error (MAPE), Top-Stage Identification Accuracy, Spearman Rank Correlation ($\rho$), Suppression Rate, Query Runtime.
* **Execution Command**:
  ```bash
  python scripts/run_experiment.py --trials 20
  ```

---

## 12. Baseline vs. Differentially Private Comparison

Empirical comparison derived directly from actual execution (`reports/experiment_summary.csv`):

| Method | Epsilon $\epsilon$ | Top Stage | Top-Stage Accuracy | Ground Truth Rate | Estimated Rate | Absolute Error | Ranking Agreement ($\rho$) | Runtime |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Non-Private Baseline** | 0.0 | **Document Upload** | 100.0% | 34.10% | 34.10% | 0.0000 | 1.0000 | 0.0150s |
| **DP (Laplace, $\epsilon=0.10$)** | 0.10 | **Document Upload** | 100.0% | 34.10% | 34.05% | 0.0005 | 0.9958 | 0.0677s |
| **DP (Laplace, $\epsilon=0.25$)** | 0.25 | **Document Upload** | 100.0% | 34.10% | 34.07% | 0.0003 | 0.9964 | 0.0679s |
| **DP (Laplace, $\epsilon=0.50$)** | 0.50 | **Document Upload** | 100.0% | 34.10% | 34.07% | 0.0003 | 0.9967 | 0.0674s |
| **DP (Laplace, $\epsilon=0.75$)** | 0.75 | **Document Upload** | 100.0% | 34.10% | 34.09% | 0.0001 | 0.9970 | 0.0647s |
| **DP (Laplace, $\epsilon=1.00$)** | 1.00 | **Document Upload** | 100.0% | 34.10% | 34.10% | 0.0000 | 0.9967 | 0.0666s |

---

## 13. Pre-Defined Targets vs. Measured Experimental Results

| Evaluation Metric | Target | Measured Result (ε = 1.0) | Status |
| :--- | :--- | :--- | :--- |
| **Privacy Budget** | $\epsilon \le 1.0$ | **$\epsilon = 1.0$** (bounded) | **TARGET MET ✅** |
| **Top-Stage Accuracy** | $\ge 90\%$ | **100.0%** (Document Upload correctly identified) | **TARGET MET ✅** |
| **Bottleneck Absolute Error** | $\le 1.0\%$ | **0.0000** (Exact 34.10% estimated) | **TARGET MET ✅** |
| **Ranking Agreement (Spearman $\rho$)** | $\ge 0.90$ | **0.9967** (near-perfect stage ordering) | **TARGET MET ✅** |
| **Legacy Availability During Outage** | $100\%$ | **100.0%** (zero claim loss) | **TARGET MET ✅** |
| **Small-Group Suppression ($k=10$)** | $100\%$ suppressed | **100.0%** ($27.96\%$ of fine-grained cohorts masked) | **TARGET MET ✅** |
| **Query Runtime** | $< 2.0\text{s}$ | **0.0666s** | **TARGET MET ✅** |

---

## 14. 8 Operational Failure Modes Tested & Validated

All 8 failure scenarios verified automatically via `reports/failure_results.csv`:
1. **Failure 1 (Missing Consent)**: `consent_status = None` $\rightarrow$ Event rejected; 0% personal data leakage.
2. **Failure 2 (Invalid Stage)**: `stage = 'InvalidStage_999'` $\rightarrow$ Validation failure; dropped at Gateway.
3. **Failure 3 (Duplicate Event)**: Duplicate `event_id` $\rightarrow$ Deduplicated idempotently without double-counting.
4. **Failure 4 (Small Group Cohort $< 10$)**: Count $= 2 \rightarrow$ Masked with `[SUPPRESSED < 10]` badge.
5. **Failure 5 (Analytics Service Crash)**: Analytics service offline $\rightarrow$ Non-blocking fallback; Claims succeed 100%.
6. **Failure 6 (Budget Exhausted)**: Cumulative queries exceed $\epsilon=1.0 \rightarrow$ Rejected with `BudgetExhaustedError`.
7. **Failure 7 (Invalid Epsilon)**: Requests with $\epsilon > 1.0$ or $\epsilon \le 0 \rightarrow$ Rejected with `InvalidEpsilonError`.
8. **Failure 8 (DB / Network Failure)**: Telemetry database unreachable $\rightarrow$ Core claims continue uninterrupted.

---

## 15. Quick Start & Execution Guide

```bash
# 1. Activate Environment
.\.venv\Scripts\activate

# 2. Reassemble SQLite Database (if cloned from GitHub)
python scripts/reassemble_db.py

# 3. Generate Synthetic Telemetry (10,000 sessions / 126k+ events)
python scripts/generate_data.py --sessions 10000 --seed 42

# 4. Validate Dataset Schema, Consent & Zero PII
python scripts/validate_data.py

# 5. Run Complete 20-Trial Benchmark Suite & Generate Charts
python scripts/run_experiment.py --trials 20

# 6. Run 40 Automated Pytest Unit, Security & E2E Tests
pytest tests/ -v

# 7. Generate 24-Slide Presentation PPTX
python scripts/generate_presentation.py

# 8. Run Automated Project-Wide Verification Script
python scripts/verify_project.py

# 9. Launch Streamlit Analytics Dashboard
streamlit run app/dashboard.py
```

---

## 16. Security & Misuse Controls

1. **Individual Lookup Blocked**: Individual session query attempts return an explicit security rejection.
2. **Small-Group Suppression**: Prevents inference attacks against rare customer cohorts.
3. **Consent Enforcement**: Rejects unauthorized telemetry.
4. **Privacy Budget Ceiling**: Epsilon $> 1.0$ requests are refused.
5. **Ledger Depletion Refusal**: Queries beyond total $\epsilon = 1.0$ are rejected with `BudgetExhaustedError`.

---

## 17. Limitations

1. **Sample Size Sensitivity**: At very low sample sizes ($N < 50$), Laplace noise can introduce larger percentage distortions in abandonment estimates.
2. **Single-Organization Scope**: Tested for single-tenant SQLite storage; multi-tenant deployments require distributed event streaming (e.g. Kafka).
3. **Longitudinal Shift**: The synthetic generator assumes stationary transition probabilities over the 30-day window.

---

## 18. Future Improvements

1. **Local Differential Privacy (LDP)**: Implement randomized response on the customer client side before telemetry leaves the browser.
2. **Differential Privacy with Rènyi Accounting**: Upgrade budget manager to support Rènyi Differential Privacy (RDP) for tighter composition bounds across thousands of queries.
3. **Automated Dynamic Deferral**: Automatically adjust workflow stages in the legacy portal (e.g. allowing document deferral) when abandonment thresholds exceed 25%.

---

## 19. License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
