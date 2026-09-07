# System Requirements Specification (SRS)

## 1. Functional Requirements

### FR-01: Simulated Legacy Insurance Workflow
* The platform must simulate an 8-stage insurance claims process: `Login`, `Start Claim`, `Claim Type`, `Claim Details`, `Document Upload`, `Review`, `Submit`, `Confirmation`.
* Each stage must support progression, simulated error generation, and customer abandonment.

### FR-02: Non-Blocking Telemetry Collection
* All stage transitions must generate an event with schema: `event_id`, `anonymous_session_id`, `workflow_stage`, `event_type`, `timestamp_bucket`, `consent_status`, `portal_version`, `event_source`.
* Telemetry collection must never block or crash core claim processing.

### FR-03: Explicit Consent Enforcement
* Events must be validated for explicit `CONSENTED` status.
* `NOT_CONSENTED` and `UNKNOWN` events must be dropped from analytics calculations.
* Secure defaults must reject unverified consent without assumptions.

### FR-04: Anonymisation & Data Minimisation
* Direct personal identifiable information (PII) including names, emails, phones, and policy numbers must be strictly forbidden from analytics storage.
* Session identifiers must use one-way salted hashes. Timestamps must be bucketized to 1-hour increments.

### FR-05: Macro-Level Aggregation
* The analytics service must produce aggregated stage totals (`entered_count`, `completed_count`, `abandoned_count`, `completion_rate`, `abandonment_rate`).
* Individual journey paths must never be exposed to product or business users.

### FR-06: Small-Group Suppression
* Aggregate counts below $k=10$ must be suppressed and marked as `[SUPPRESSED < 10]`.

### FR-07: Laplace Differential Privacy
* Count metrics must be perturbed with Laplace noise using sensitivity $\Delta f = 1$ and bounded budget $\epsilon \in [0.1, 1.0]$.
* Unsafe budgets ($\epsilon > 1.0$) must be rejected.

### FR-08: Privacy Budget Accounting
* A centralized ledger must track consumed $\epsilon$ and remaining budget. Queries exceeding the budget must be refused.

### FR-09: Bottleneck Identification & Baseline Comparison
* The engine must identify the workflow stage with the highest abandonment rate.
* A non-private baseline must be provided for comparative error benchmarking.

### FR-10: Coexistence & Rollback Controller
* The system must support `LEGACY`, `COEXISTENCE`, `MODERN`, and `LEGACY_FALLBACK` modes.
* Simulated analytics outages must trigger fallback while claims processing continues with 100% availability.

---

## 2. Non-Functional Requirements

### NFR-01: Privacy & Confidentiality
* Compliance with GDPR Article 5 (Data Minimisation) and Article 25 (Data Protection by Design and by Default).

### NFR-02: Availability & Fault Tolerance
* Legacy claims processing must maintain 100% operational availability during total analytics downtime.

### NFR-03: Performance & Latency
* Aggregate privacy queries across 50,000+ events must return within 2.0 seconds.
* Event adapter overhead must be $< 10\text{ms}$ per transition.

### NFR-04: Usability & Visual Distinction
* Modern analytics dashboard must provide responsive, dark-mode, glassmorphic UI.
* Legacy portal interface must visually convey classic utilitarian corporate styling.
