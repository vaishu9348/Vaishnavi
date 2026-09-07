"""
Database Initialization Script
Sets up SQLite schema for:
- interaction_events (anonymised analytics stream)
- claims (legacy claims processing records)
- privacy_budget (privacy accounting ledger)
- system_status (health and coexistence state)
- audit_log (security, rollback, and administrative trace)
"""

import sqlite3
import os
import argparse
from datetime import datetime

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "synthetic", "insurance_portal.db")


def create_schema(db_path: str = DEFAULT_DB_PATH):
    """Creates database directories and initializes table schemas."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 1. interaction_events (Data-minimised analytics stream)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS interaction_events (
            event_id TEXT PRIMARY KEY,
            anonymous_session_id TEXT NOT NULL,
            workflow_stage TEXT NOT NULL,
            event_type TEXT NOT NULL,
            timestamp_bucket TEXT NOT NULL,
            consent_status TEXT NOT NULL,
            portal_version TEXT NOT NULL,
            event_source TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_events_consent ON interaction_events(consent_status)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_events_stage ON interaction_events(workflow_stage)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON interaction_events(event_type)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_events_session ON interaction_events(anonymous_session_id)")

    # 2. claims (Legacy insurance claims system table - independent from analytics)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS claims (
            claim_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            claim_type TEXT NOT NULL,
            claim_description TEXT,
            amount_estimated REAL DEFAULT 0.0,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            processed_mode TEXT NOT NULL
        )
    """)

    # 3. privacy_budget (Differential privacy ledger)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS privacy_budget (
            budget_id INTEGER PRIMARY KEY,
            total_epsilon REAL NOT NULL,
            consumed_epsilon REAL NOT NULL,
            remaining_epsilon REAL NOT NULL,
            query_count INTEGER NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        INSERT OR IGNORE INTO privacy_budget (budget_id, total_epsilon, consumed_epsilon, remaining_epsilon, query_count, updated_at)
        VALUES (1, 1.0, 0.0, 1.0, 0, ?)
    """, (datetime.utcnow().isoformat(),))

    # 4. system_status (System coexistence and health states)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS system_status (
            id INTEGER PRIMARY KEY,
            current_mode TEXT NOT NULL,
            analytics_healthy INTEGER NOT NULL,
            legacy_healthy INTEGER NOT NULL,
            gateway_healthy INTEGER NOT NULL,
            db_healthy INTEGER NOT NULL,
            last_heartbeat TEXT NOT NULL
        )
    """)
    cur.execute("""
        INSERT OR IGNORE INTO system_status (id, current_mode, analytics_healthy, legacy_healthy, gateway_healthy, db_healthy, last_heartbeat)
        VALUES (1, 'COEXISTENCE', 1, 1, 1, 1, ?)
    """, (datetime.utcnow().isoformat(),))

    # 5. audit_log (Administrative and security audit trails)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            actor_role TEXT NOT NULL,
            details TEXT,
            status TEXT NOT NULL
        )
    """)
    cur.execute("""
        INSERT INTO audit_log (timestamp, action, actor_role, details, status)
        VALUES (?, 'INITIALIZE_DATABASE', 'SYSTEM', 'Database initialized with secure defaults.', 'SUCCESS')
    """, (datetime.utcnow().isoformat(),))

    conn.commit()
    conn.close()
    print(f"[OK] Database schema successfully initialized at: {db_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize SQLite database for Insurance Privacy Analytics")
    parser.add_argument("--db-path", type=str, default=DEFAULT_DB_PATH, help="Path to SQLite database file")
    args = parser.parse_args()
    create_schema(args.db_path)
