# System Architecture & Coexistence Blueprint

This document details the multi-tiered architecture of the Insurance Privacy Journey Analytics Platform.

## Architectural Diagram

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

## Architectural Decoupling & Isolation

1. **Transaction Isolation**:
   - The claims processing pipeline writes directly to the SQLite `claims` table.
   - The event adapter wraps analytics ingestion in a try/except fault barrier. Any connection timeout, database lock, or gateway failure is trapped silently, returning success to the frontend customer interface.

2. **Zero-PII Gateway Boundary**:
   - The `interaction_events` stream receives sanitized events where personal attributes are removed before reaching persistent storage or memory aggregation caches.

3. **Stateless Privacy Transform**:
   - Aggregation and Laplace perturbation occur dynamically per query, with ledger deductions handled by the thread-safe `PrivacyBudgetManager`.
