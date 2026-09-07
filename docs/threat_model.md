# Threat Model & Privacy Risk Assessment

This document formalizes the threat landscape for the Insurance Privacy Journey Analytics Platform using STRIDE-adapted privacy threat modeling.

## Threat Analysis Matrix

### 1. Threat: Individual Journey Re-identification
* **Risk**: High
* **Attack Scenario**: An internal analyst or external adversary attempts to link anonymous interaction sequences to a known policyholder by tracking specific transition timestamps or IP addresses.
* **Mitigation**:
  - Zero PII stored in analytics tables (no names, emails, phones, policy numbers, or IP addresses).
  - Session tokens generated with non-reversible cryptographic hash (`SHA-256(seed + salt)`).
  - Timestamp bucketization strips exact seconds and minutes, aggregating time into 1-hour intervals.
  - Reverse mapping tables between anonymous IDs and policyholders are completely prohibited and non-existent.
* **Residual Risk**: Negligible. Without timing precision or personal attributes, linkage attacks fail mathematically.

---

### 2. Threat: Small-Group Inference / Singling Out
* **Risk**: Medium-High
* **Attack Scenario**: An adversary queries a narrow demographic or unusual time bucket where only 1 or 2 users abandoned, deduce their behavior by elimination.
* **Mitigation**:
  - Enforced $k$-anonymity suppression threshold ($k=10$).
  - Any aggregate cell with $\text{count} < 10$ is suppressed and replaced with `[SUPPRESSED < 10]`.
* **Residual Risk**: Low. Micro-cohort inference is blocked.

---

### 3. Threat: Consent Bypass Injection
* **Risk**: Medium
* **Attack Scenario**: A corrupted client or rogue batch script submits telemetry tagged as `NOT_CONSENTED` or `UNKNOWN` hoping analytics engines will process it anyway.
* **Mitigation**:
  - Strict conservative consent filter (`privacy/consent.py`).
  - Only explicitly marked `CONSENTED` records pass into aggregation.
  - Zero-consent default: `None`, empty string, and `UNKNOWN` are dropped automatically.
* **Residual Risk**: None. Validated through automated unit tests.

---

### 4. Threat: Differential Privacy Budget Abuse (Excessive Epsilon)
* **Risk**: High
* **Attack Scenario**: A malicious data analyst requests queries with $\epsilon = 100$, effectively stripping Laplace noise and extracting true counts.
* **Mitigation**:
  - Hard parameter validation ceiling enforcing $\epsilon \le 1.0$.
  - Requests with $\epsilon > 1.0$ immediately raise `InvalidEpsilonError` and are dropped.
* **Residual Risk**: Zero. The privacy engine strictly refuses unsafe budgets.

---

### 5. Threat: Repeated-Query Reconstruction (Differencing Attack)
* **Risk**: Medium
* **Attack Scenario**: An attacker issues hundreds of slightly varied queries to average out the Laplace noise and reconstruct ground-truth values.
* **Mitigation**:
  - Global Privacy Budget Ledger (`PrivacyBudgetManager`).
  - Bounded global budget $\epsilon_{\text{total}} = 1.0$.
  - Each query deducts its $\epsilon$; when exhausted, queries are rejected with `BudgetExhaustedError`.
* **Residual Risk**: Minimal. Budget accounting prevents infinite averaging.

---

### 6. Threat: Analytics Denial of Service Blocking Claims Processing
* **Risk**: Critical (Operational Availability)
* **Attack Scenario**: The analytics engine or privacy gateway crashes, locking the database or raising exceptions that cause the customer's claim submission to fail.
* **Mitigation**:
  - Asynchronous, non-blocking Event Adapter.
  - Independent database connections and transaction threads.
  - Coexistence architecture guarantees that analytics failures fail silently to the customer while logging audit telemetry.
* **Residual Risk**: Zero. Core claim processing is 100% decoupled.
