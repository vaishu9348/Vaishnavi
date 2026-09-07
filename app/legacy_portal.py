"""
Simulated Legacy Insurance Claims Portal
Provides a functional, interactive simulation of the legacy insurance customer workflow:
1. Login -> 2. Start Claim -> 3. Claim Type -> 4. Claim Details -> 5. Document Upload
-> 6. Review -> 7. Submit -> 8. Confirmation.

Emits anonymized interaction events via the non-blocking event adapter.
Operates seamlessly even if analytics fails or is offline (coexistence guarantee).
"""

import streamlit as st
import uuid
import os
import sqlite3
from datetime import datetime
from app.rollback import global_rollback_controller
from privacy.anonymization import generate_anonymous_session_id, bucketize_timestamp

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "synthetic", "insurance_portal.db")


def init_portal_session_state():
    """Initializes customer workflow state in Streamlit session."""
    if "portal_stage_idx" not in st.session_state:
        st.session_state.portal_stage_idx = 0
    if "portal_anon_id" not in st.session_state:
        st.session_state.portal_anon_id = generate_anonymous_session_id()
    if "portal_claim_type" not in st.session_state:
        st.session_state.portal_claim_type = "Vehicle"
    if "portal_claim_desc" not in st.session_state:
        st.session_state.portal_claim_desc = "Minor fender bender in parking bay."
    if "portal_amount" not in st.session_state:
        st.session_state.portal_amount = 1250.0
    if "portal_consent" not in st.session_state:
        st.session_state.portal_consent = "CONSENTED"
    if "portal_completed_claim_id" not in st.session_state:
        st.session_state.portal_completed_claim_id = None
    if "portal_event_log" not in st.session_state:
        st.session_state.portal_event_log = []


def emit_portal_event(stage_name: str, event_type: str):
    """Emits an anonymized interaction event through the non-blocking adapter."""
    ts_now = datetime.utcnow()
    evt = {
        "event_id": f"EVT-{uuid.uuid4().hex[:8].upper()}",
        "anonymous_session_id": st.session_state.portal_anon_id,
        "workflow_stage": stage_name,
        "event_type": event_type,
        "timestamp_bucket": bucketize_timestamp(ts_now),
        "consent_status": st.session_state.portal_consent,
        "portal_version": "v2.5-coexistence",
        "event_source": "web_claims_portal",
        "created_at": ts_now.isoformat(),
    }
    st.session_state.portal_event_log.append(f"[{ts_now.strftime('%H:%M:%S')}] {stage_name} -> {event_type}")
    # Non-blocking dispatch
    global_rollback_controller.dispatch_event_adapter(evt)


def render_legacy_portal():
    """Renders the simulated legacy portal UI."""
    init_portal_session_state()

    stages = [
        "Login",
        "Start Claim",
        "Claim Type",
        "Claim Details",
        "Document Upload",
        "Review",
        "Submit",
        "Confirmation"
    ]

    current_idx = st.session_state.portal_stage_idx
    current_stage = stages[current_idx]

    # Legacy styling container
    st.markdown("""
        <style>
            .legacy-box {
                background-color: #f8f9fa;
                border: 2px solid #ced4da;
                border-radius: 6px;
                padding: 18px;
                color: #212529;
                font-family: Arial, sans-serif;
            }
            .legacy-banner {
                background-color: #1a365d;
                color: #ffffff;
                padding: 12px 20px;
                border-radius: 6px 6px 0 0;
                font-weight: bold;
                font-size: 1.15rem;
            }
            .legacy-step-badge {
                display: inline-block;
                padding: 4px 10px;
                background-color: #e2e8f0;
                color: #2d3748;
                border-radius: 4px;
                font-size: 0.85rem;
                font-weight: 600;
                margin-right: 6px;
            }
            .legacy-step-active {
                background-color: #2b6cb0;
                color: white;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="legacy-banner">
            🏛️ Legacy Insurance Claims Processing Portal (Simulated Production Environment)
        </div>
    """, unsafe_allow_html=True)

    # Coexistence banner indicator
    is_failed = global_rollback_controller.is_analytics_failed
    mode_val = global_rollback_controller.current_mode.value

    if is_failed:
        st.warning(f"⚠️ **Analytics Service Unavailable** | System Operating in **{mode_val}**. Claims processing is 100% operational.")
    else:
        st.info(f"ℹ️ System Mode: **{mode_val}** | Claims Pipeline: **HEALTHY** | Analytics Telemetry: **CONNECTED**")

    # Breadcrumb workflow tracker
    cols = st.columns(len(stages))
    for i, s in enumerate(stages):
        with cols[i]:
            if i == current_idx:
                st.markdown(f"**Step {i+1}**<br><span style='color:#2b6cb0;font-weight:bold;'>{s}</span>", unsafe_allow_html=True)
            elif i < current_idx:
                st.markdown(f"<span style='color:green;'>✓ Step {i+1}</span><br><span style='color:gray;'>{s}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color:gray;'>Step {i+1}</span><br><span style='color:lightgray;'>{s}</span>", unsafe_allow_html=True)

    st.divider()

    # Stage 1: Login
    if current_stage == "Login":
        st.subheader("Step 1: Customer Authentication")
        st.markdown("Enter synthetic credentials to begin. *Notice: No real personal information is collected.*")
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Anonymous Session Token", value=st.session_state.portal_anon_id, disabled=True)
            st.text_input("Policy Account ID", value="POL-SYNTH-882194", disabled=True)
        with c2:
            st.selectbox(
                "Consent for Journey Analytics",
                ["CONSENTED", "NOT_CONSENTED", "UNKNOWN"],
                key="portal_consent",
                help="Only CONSENTED events will contribute to privacy analytics. Secure-by-default."
            )
            st.caption("We value privacy: Journey analytics uses differential privacy without capturing names, emails, or personal claim specifics.")

        if st.button("Continue to Portal ➡️", key="btn_login"):
            emit_portal_event("Login", "COMPLETED")
            st.session_state.portal_stage_idx = 1
            emit_portal_event("Start Claim", "ENTERED")
            st.rerun()

    # Stage 2: Start Claim
    elif current_stage == "Start Claim":
        st.subheader("Step 2: Start New Insurance Claim")
        st.write("Welcome back. Would you like to initiate a new claim for incident loss or damage reimbursement?")
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            if st.button("🚀 Start New Claim", key="btn_start"):
                emit_portal_event("Start Claim", "COMPLETED")
                st.session_state.portal_stage_idx = 2
                emit_portal_event("Claim Type", "ENTERED")
                st.rerun()
        with c2:
            if st.button("❌ Abandon Journey", key="btn_aban_start"):
                emit_portal_event("Start Claim", "ABANDONED")
                st.session_state.portal_stage_idx = 0
                st.warning("Customer abandoned at Start Claim.")
                st.rerun()

    # Stage 3: Claim Type
    elif current_stage == "Claim Type":
        st.subheader("Step 3: Select Claim Category")
        claim_type = st.radio("Choose claim category:", ["Vehicle", "Health", "Property", "Travel"], horizontal=True)
        st.session_state.portal_claim_type = claim_type
        
        c1, c2, _ = st.columns([2, 1, 1])
        with c1:
            if st.button("Next: Enter Claim Details ➡️", key="btn_type"):
                emit_portal_event("Claim Type", "COMPLETED")
                st.session_state.portal_stage_idx = 3
                emit_portal_event("Claim Details", "ENTERED")
                st.rerun()
        with c2:
            if st.button("❌ Abandon Journey", key="btn_aban_type"):
                emit_portal_event("Claim Type", "ABANDONED")
                st.session_state.portal_stage_idx = 0
                st.warning("Customer abandoned at Claim Type.")
                st.rerun()

    # Stage 4: Claim Details
    elif current_stage == "Claim Details":
        st.subheader("Step 4: Claim Incident Details")
        st.text_area("Incident Description (Synthetic)", value=st.session_state.portal_claim_desc, key="portal_claim_desc")
        st.number_input("Estimated Claim Amount ($)", min_value=50.0, max_value=50000.0, value=st.session_state.portal_amount, step=100.0, key="portal_amount")

        c1, c2, _ = st.columns([2, 1, 1])
        with c1:
            if st.button("Next: Document Upload ➡️", key="btn_details"):
                emit_portal_event("Claim Details", "COMPLETED")
                st.session_state.portal_stage_idx = 4
                emit_portal_event("Document Upload", "ENTERED")
                st.rerun()
        with c2:
            if st.button("❌ Abandon Journey", key="btn_aban_details"):
                emit_portal_event("Claim Details", "ABANDONED")
                st.session_state.portal_stage_idx = 0
                st.warning("Customer abandoned at Claim Details.")
                st.rerun()

    # Stage 5: Document Upload (Primary Operational Bottleneck)
    elif current_stage == "Document Upload":
        st.subheader("Step 5: Document Upload (Known Industry Bottleneck)")
        st.markdown("""
            > ⚠️ **Friction Point**: In legacy insurance portals, customers frequently abandon here due to missing receipts, file format rejections, or slow upload progress.
        """)
        st.file_uploader("Upload Supporting Invoices / Proof of Damage", type=["pdf", "png", "jpg"], accept_multiple_files=False)

        c1, c2, c3 = st.columns([2, 1.5, 1])
        with c1:
            if st.button("Complete Upload & Review ➡️", key="btn_docs"):
                emit_portal_event("Document Upload", "COMPLETED")
                st.session_state.portal_stage_idx = 5
                emit_portal_event("Review", "ENTERED")
                st.rerun()
        with c2:
            if st.button("⚠️ Simulate Upload Error", key="btn_err_docs"):
                emit_portal_event("Document Upload", "ERROR")
                st.error("Simulated Error: File verification timeout. Customer can retry or abandon.")
        with c3:
            if st.button("❌ Abandon Journey", key="btn_aban_docs"):
                emit_portal_event("Document Upload", "ABANDONED")
                st.session_state.portal_stage_idx = 0
                st.warning("Customer abandoned at Document Upload stage.")
                st.rerun()

    # Stage 6: Review
    elif current_stage == "Review":
        st.subheader("Step 6: Review Claim Information")
        st.info(f"**Category**: {st.session_state.portal_claim_type} | **Amount**: ${st.session_state.portal_amount:,.2f} | **Incident**: {st.session_state.portal_claim_desc}")
        st.caption("Please confirm that all details are accurate before final submission.")

        c1, c2, _ = st.columns([2, 1, 1])
        with c1:
            if st.button("Submit Claim for Processing 🚀", key="btn_review"):
                emit_portal_event("Review", "COMPLETED")
                st.session_state.portal_stage_idx = 6
                emit_portal_event("Submit", "ENTERED")
                st.rerun()
        with c2:
            if st.button("❌ Abandon Journey", key="btn_aban_review"):
                emit_portal_event("Review", "ABANDONED")
                st.session_state.portal_stage_idx = 0
                st.warning("Customer abandoned at Review.")
                st.rerun()

    # Stage 7: Submit
    elif current_stage == "Submit":
        st.subheader("Step 7: Final Processing Submission")
        st.write("Submitting claim transaction to core ledger...")

        # Store in legacy SQLite claims table
        new_claim_id = f"CLM-2026-{uuid.uuid4().hex[:6].upper()}"
        st.session_state.portal_completed_claim_id = new_claim_id
        
        try:
            db_p = DEFAULT_DB_PATH
            if os.path.exists(db_p):
                conn = sqlite3.connect(db_p, timeout=2.0)
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO claims (claim_id, customer_id, claim_type, claim_description, amount_estimated, status, created_at, processed_mode)
                    VALUES (?, ?, ?, ?, ?, 'SUBMITTED', ?, ?)
                """, (
                    new_claim_id,
                    st.session_state.portal_anon_id,
                    st.session_state.portal_claim_type,
                    st.session_state.portal_claim_desc,
                    st.session_state.portal_amount,
                    datetime.utcnow().isoformat(),
                    global_rollback_controller.current_mode.value
                ))
                conn.commit()
                conn.close()
        except Exception:
            pass

        global_rollback_controller.record_claim_processed()
        emit_portal_event("Submit", "COMPLETED")
        st.session_state.portal_stage_idx = 7
        emit_portal_event("Confirmation", "ENTERED")
        emit_portal_event("Confirmation", "COMPLETED")
        st.rerun()

    # Stage 8: Confirmation
    elif current_stage == "Confirmation":
        st.success(f"🎉 **Claim Successfully Submitted!** Reference ID: `{st.session_state.portal_completed_claim_id}`")
        st.write("Thank you. Your claim has been queued for claims adjudicator evaluation.")
        st.info("Notice: Your claim submission was completed successfully regardless of analytics system availability.")

        if st.button("Start Another Claim 🔄", key="btn_reset"):
            st.session_state.portal_stage_idx = 0
            st.session_state.portal_anon_id = generate_anonymous_session_id()
            st.session_state.portal_completed_claim_id = None
            st.rerun()

    # Telemetry monitor expander
    with st.expander("📡 Live Event Adapter Telemetry (Non-blocking)", expanded=False):
        st.write(f"**Customer Token**: `{st.session_state.portal_anon_id}` | **Consent**: `{st.session_state.portal_consent}`")
        if st.session_state.portal_event_log:
            for log_entry in st.session_state.portal_event_log[-8:]:
                st.code(log_entry)
        else:
            st.caption("No events generated in this session yet.")
