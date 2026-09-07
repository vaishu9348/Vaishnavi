# Failure Mode and Effects Analysis (FMEA)

This document formalizes system resilience across key operational failure scenarios and unexpected data inputs.

## Failure Matrix

| Failure Mode | Detection Mechanism | System Response | Customer Impact | Recovery Protocol |
| :--- | :--- | :--- | :--- | :--- |
| **Missing Consent** | Consent Gateway Validator | Event dropped immediately; logged to audit ledger. | None. Secure defaults protect user. | Continue ingestion stream. |
| **Unknown Consent Status** | Conservative filter check (`CONSENTED` required) | Treated identically to `NOT_CONSENTED`; excluded from counts. | None. Conservative zero-consent default. | Continue ingestion stream. |
| **Invalid Workflow Stage** | Schema validation against canonical stage list | Event rejected at Gateway boundary. | None. Legacy claim unaffected. | Drop corrupted event; log audit warning. |
| **Duplicate Event Stream** | Primary key uniqueness constraint on `event_id` | Duplicate record silently ignored or discarded. | None. | Automatic deduplication. |
| **Small Group Inference (Count < 10)** | Suppression filter (`k = 10`) | Display count replaced with `[SUPPRESSED < 10]`; notice shown. | None. Protects outlier privacy. | Automatic masking. |
| **Privacy Budget Exhaustion** | Budget manager transaction check | Query rejected with `BudgetExhaustedError`. | None to claim processing; dashboard analytics halted. | Admin reset after operational cycle review. |
| **Excessive Epsilon Request (ε > 1.0)** | Security input sanitizer | Rejected with `InvalidEpsilonError`. | None. Prevents privacy stripping attack. | Request valid bounded epsilon ($0.1 \le \epsilon \le 1.0$). |
| **Analytics Service Outage / Crash** | Health check monitor & adapter error trap | Adapter bypasses analytics; mode shifts to `LEGACY_FALLBACK`. | **ZERO Impact**. Claim processing continues 100%. | Automatic non-blocking fallback; resume via Coexistence mode. |
| **Database Lock / Unavailability** | Timeout guard (1.0s timeout) | Fallback to non-blocking memory queue; claim write prioritized. | None. Customer receives claim confirmation. | DB connection retry with backoff. |

## Decoupled Architecture Guarantee

Critical claim transaction execution and privacy analytics share zero blocking dependencies. In every tested failure mode, the policyholder's ability to initiate, edit, review, and submit an insurance claim remains fully operational.
