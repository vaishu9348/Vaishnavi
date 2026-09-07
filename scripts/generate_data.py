"""
Synthetic Data Generator
Generates realistic interaction journeys for an insurance claims workflow.
Supports configurable session volume, realistic stage transitions,
Document Upload bottleneck modeling, and consent distributions.
"""

import os
import uuid
import random
import argparse
from datetime import datetime, timedelta
import pandas as pd
import sqlite3

# Workflow sequence and realistic stage completion rates
WORKFLOW_STEPS = [
    ("Login", 1.00),
    ("Start Claim", 0.98),
    ("Claim Type", 0.95),
    ("Claim Details", 0.88),
    ("Document Upload", 0.70),  # Primary operational bottleneck
    ("Review", 0.92),
    ("Submit", 0.96),
    ("Confirmation", 1.00),
]

CLAIM_TYPES = ["Vehicle", "Health", "Property", "Travel"]
PORTAL_VERSIONS = ["v2.4-legacy-adapter", "v2.5-coexistence"]


def generate_synthetic_data(
    num_sessions: int = 10000,
    seed: int = 42,
    output_dir: str = "data",
    db_path: str = "data/synthetic/insurance_portal.db"
) -> pd.DataFrame:
    """
    Generates realistic synthetic insurance customer workflow events.
    """
    random.seed(seed)
    base_time = datetime(2026, 8, 1, 8, 0, 0)

    events = []
    claims_records = []
    
    print(f"[*] Generating {num_sessions} synthetic insurance customer sessions...")

    for i in range(num_sessions):
        # Generate anonymous session token
        session_hash = uuid.uuid4().hex[:8].upper()
        anon_session_id = f"ANON-{session_hash[:4]}-{session_hash[4:]}"
        
        # Stagger timestamps across a 30-day operational window
        session_start_offset = timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        current_time = base_time + session_start_offset
        
        # Determine customer consent for analytics
        # ~80% Consented, 15% Not Consented, 5% Unknown
        consent_rand = random.random()
        if consent_rand < 0.80:
            consent = "CONSENTED"
        elif consent_rand < 0.95:
            consent = "NOT_CONSENTED"
        else:
            consent = "UNKNOWN"

        portal_ver = random.choice(PORTAL_VERSIONS)
        claim_type = random.choice(CLAIM_TYPES)
        completed_all = True
        reached_stage = "Login"

        # Journey simulation through workflow
        for stage_idx, (stage_name, completion_prob) in enumerate(WORKFLOW_STEPS):
            reached_stage = stage_name
            # Bucketize timestamp to nearest hour (data minimisation)
            ts_bucket = current_time.replace(minute=0, second=0, microsecond=0).strftime("%Y-%m-%d %H:00:00")
            created_iso = current_time.isoformat()

            # 1. Stage ENTERED event
            events.append({
                "event_id": f"EVT-{uuid.uuid4().hex[:12].upper()}",
                "anonymous_session_id": anon_session_id,
                "workflow_stage": stage_name,
                "event_type": "ENTERED",
                "timestamp_bucket": ts_bucket,
                "consent_status": consent,
                "portal_version": portal_ver,
                "event_source": "web_claims_portal",
                "created_at": created_iso,
            })

            # Simulate Document Upload error journey archetype (Upload Error -> Retry)
            if stage_name == "Document Upload" and random.random() < 0.12:
                err_time = current_time + timedelta(seconds=random.randint(5, 20))
                events.append({
                    "event_id": f"EVT-{uuid.uuid4().hex[:12].upper()}",
                    "anonymous_session_id": anon_session_id,
                    "workflow_stage": stage_name,
                    "event_type": "ERROR",
                    "timestamp_bucket": ts_bucket,
                    "consent_status": consent,
                    "portal_version": portal_ver,
                    "event_source": "web_claims_portal",
                    "created_at": err_time.isoformat(),
                })
                # 50% recover after error, 50% abandon at error
                if random.random() < 0.50:
                    current_time += timedelta(seconds=random.randint(25, 45))
                    events.append({
                        "event_id": f"EVT-{uuid.uuid4().hex[:12].upper()}",
                        "anonymous_session_id": anon_session_id,
                        "workflow_stage": stage_name,
                        "event_type": "ABANDONED",
                        "timestamp_bucket": ts_bucket,
                        "consent_status": consent,
                        "portal_version": portal_ver,
                        "event_source": "web_claims_portal",
                        "created_at": current_time.isoformat(),
                    })
                    completed_all = False
                    break

            # Check if customer completes or abandons current stage
            if random.random() <= completion_prob:
                current_time += timedelta(seconds=random.randint(10, 60))
                events.append({
                    "event_id": f"EVT-{uuid.uuid4().hex[:12].upper()}",
                    "anonymous_session_id": anon_session_id,
                    "workflow_stage": stage_name,
                    "event_type": "COMPLETED",
                    "timestamp_bucket": ts_bucket,
                    "consent_status": consent,
                    "portal_version": portal_ver,
                    "event_source": "web_claims_portal",
                    "created_at": current_time.isoformat(),
                })
            else:
                # Customer abandons
                current_time += timedelta(seconds=random.randint(15, 90))
                events.append({
                    "event_id": f"EVT-{uuid.uuid4().hex[:12].upper()}",
                    "anonymous_session_id": anon_session_id,
                    "workflow_stage": stage_name,
                    "event_type": "ABANDONED",
                    "timestamp_bucket": ts_bucket,
                    "consent_status": consent,
                    "portal_version": portal_ver,
                    "event_source": "web_claims_portal",
                    "created_at": current_time.isoformat(),
                })
                completed_all = False
                break

        # If customer reached submit/confirmation, record in legacy claims table
        if completed_all or reached_stage in ("Submit", "Confirmation"):
            claims_records.append({
                "claim_id": f"CLM-2026-{i:05d}-{uuid.uuid4().hex[:4].upper()}",
                "customer_id": f"CUST-SYNTH-{random.randint(1000, 9999)}",
                "claim_type": claim_type,
                "claim_description": f"Synthetic {claim_type} incident reported via portal",
                "amount_estimated": round(random.uniform(250.0, 7500.0), 2),
                "status": "SUBMITTED" if completed_all else "DRAFT_ABANDONED",
                "created_at": current_time.isoformat(),
                "processed_mode": "COEXISTENCE",
            })

    df_events = pd.DataFrame(events)
    df_claims = pd.DataFrame(claims_records)

    print(f"[+] Total Events Generated: {len(df_events):,}")
    print(f"[+] Total Completed/Submitted Claims: {len(df_claims):,}")

    # Ensure output directories exist
    raw_dir = os.path.join(output_dir, "raw")
    proc_dir = os.path.join(output_dir, "processed")
    synth_dir = os.path.join(output_dir, "synthetic")
    for d in [raw_dir, proc_dir, synth_dir]:
        os.makedirs(d, exist_ok=True)

    # Save CSVs
    raw_csv = os.path.join(raw_dir, "interaction_events_raw.csv")
    synth_csv = os.path.join(synth_dir, "interaction_events.csv")
    df_events.to_csv(raw_csv, index=False)
    df_events.to_csv(synth_csv, index=False)

    consented_csv = os.path.join(proc_dir, "interaction_events_consented.csv")
    df_consented = df_events[df_events["consent_status"] == "CONSENTED"]
    df_consented.to_csv(consented_csv, index=False)

    # Populate SQLite database
    print(f"[*] Populating SQLite database at: {db_path}...")
    try:
        from scripts.initialize_db import create_schema
    except ImportError:
        from initialize_db import create_schema
    create_schema(db_path)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("DELETE FROM interaction_events")
    cur.execute("DELETE FROM claims")
    conn.commit()

    df_events.to_sql("interaction_events", conn, if_exists="append", index=False)
    df_claims.to_sql("claims", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()

    print(f"[SUCCESS] Synthetic data generation complete.")
    print(f"  - Raw Events: {raw_csv}")
    print(f"  - Consented Events: {consented_csv}")
    print(f"  - Database: {db_path}")

    return df_events


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic insurance journey events")
    parser.add_argument("--sessions", type=int, default=10000, help="Number of customer sessions")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output-dir", type=str, default="data", help="Output directory")
    parser.add_argument("--db-path", type=str, default="data/synthetic/insurance_portal.db", help="SQLite DB path")
    args = parser.parse_args()

    # Resolve relative paths from project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    out_dir = os.path.join(project_root, args.output_dir) if not os.path.isabs(args.output_dir) else args.output_dir
    db_p = os.path.join(project_root, args.db_path) if not os.path.isabs(args.db_path) else args.db_path

    generate_synthetic_data(
        num_sessions=args.sessions,
        seed=args.seed,
        output_dir=out_dir,
        db_path=db_p
    )
