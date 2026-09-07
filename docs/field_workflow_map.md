# Field Workflow Map: Legacy Insurance Claims & Privacy Analytics

This document illustrates the operational journey of insurance customers navigating the claims workflow and how anonymized telemetry coexists without interrupting claims operations.

## End-to-End Workflow Diagram

```mermaid
flowchart TD
    A[Customer (Policyholder)] --> B[Legacy Claims Portal]
    B --> C[Step 1: Login]
    C --> D[Step 2: Start Claim]
    D --> E[Step 3: Claim Type]
    E --> F[Step 4: Claim Details]
    F --> G[Step 5: Document Upload]
    G --> H[Step 6: Review]
    H --> I[Step 7: Submit]
    I --> J[Step 8: Confirmation]

    F -.-> X[Abandonment at Details]
    G -.-> Y[Primary Bottleneck: Abandonment at Documents]
    H -.-> Z[Abandonment at Review]

    B --> K[Non-Blocking Event Adapter]
    K --> L[Privacy Gateway]
    L --> M[Consent Verification Gateway]
    M --> N[Anonymisation & Timestamp Bucketizer]
    N --> O[Macro Aggregation Layer]
    O --> P[Small-Group Suppression (k >= 10)]
    P --> Q[Laplace Differential Privacy (ε <= 1.0)]
    Q --> R[Journey & Abandonment Analytics Engine]
    R --> S[Streamlit Product Intelligence Dashboard]
```

## Stage Descriptions

1. **Login**: Initial authentication using synthetic session tokens (`ANON-XXXX-XXXX`). No real credentials or policyholder identity are recorded.
2. **Start Claim**: Initiation of a new claim request.
3. **Claim Type**: Selection among Vehicle, Health, Property, or Travel categories.
4. **Claim Details**: Entering incident date, synthetic narrative, and estimated reimbursement amount.
5. **Document Upload (Operational Bottleneck)**: Uploading damage receipts, repair estimates, and medical summaries. Historically exhibits ~30% abandonment due to file preparation friction.
6. **Review**: Summary verification of entered claim data.
7. **Submit**: Final transaction write to legacy claims ledger.
8. **Confirmation**: Issuance of claim reference number (`CLM-2026-XXXX`).

## Non-Blocking Telemetry Ingestion

The event adapter taps each transition asynchronously:
* If the Privacy Gateway or Analytics service is degraded or offline, the adapter drops telemetry silently without raising an unhandled exception.
* Core claims submission to the legacy ledger continues with **100% availability**.
