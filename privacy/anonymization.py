"""
Anonymisation & Data Minimisation Subsystem
Enforces zero personal identifiable information (PII), irreversible session hashing,
and timestamp bucketization to prevent temporal linkage attacks.
"""

import hashlib
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd

# Explicit prohibited personal attributes
PROHIBITED_PII_FIELDS = {
    "name",
    "customer_name",
    "email",
    "phone",
    "phone_number",
    "address",
    "street",
    "zip",
    "postal_code",
    "policy_number",
    "medical_info",
    "ssn",
    "national_id",
    "claim_number",
    "ip_address",
    "device_fingerprint",
}

# Salt for session hashing within current operational cycle
ANON_SALT = "INS_PRIVACY_SALT_2026_COEXISTENCE"


def generate_anonymous_session_id(seed_string: Optional[str] = None) -> str:
    """
    Generates a cryptographically strong, non-reversible anonymous session identifier.
    Does not allow reverse lookup to actual policyholder identity.
    """
    raw_material = f"{seed_string or uuid.uuid4().hex}:{ANON_SALT}"
    hashed = hashlib.sha256(raw_material.encode("utf-8")).hexdigest()
    # Format as friendly standard token: ANON-XXXX-XXXX
    return f"ANON-{hashed[:4].upper()}-{hashed[4:8].upper()}"


def bucketize_timestamp(dt_str_or_obj: Any, bucket_hours: int = 1) -> str:
    """
    Bucketizes timestamps into discrete hour intervals.
    Prevents precise millisecond correlation attacks while preserving longitudinal funnel trends.
    """
    if dt_str_or_obj is None:
        dt = datetime.utcnow()
    elif isinstance(dt_str_or_obj, str):
        try:
            dt = datetime.fromisoformat(dt_str_or_obj.replace("Z", "+00:00"))
        except Exception:
            dt = datetime.utcnow()
    elif isinstance(dt_str_or_obj, (datetime, pd.Timestamp)):
        dt = dt_str_or_obj
    else:
        dt = datetime.utcnow()

    # Round to nearest bucket_hours interval, zero out minutes and seconds
    bucketed_hour = (dt.hour // bucket_hours) * bucket_hours
    bucketed_dt = dt.replace(hour=bucketed_hour, minute=0, second=0, microsecond=0)
    return bucketed_dt.strftime("%Y-%m-%d %H:00:00")


def sanitize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Applies data minimisation by stripping prohibited PII attributes
    and enforcing compliant schema tokens.
    """
    sanitized = {}
    for k, v in event.items():
        k_clean = k.lower().strip()
        if k_clean in PROHIBITED_PII_FIELDS:
            continue  # Drop prohibited personal data
        sanitized[k] = v

    # Ensure anonymous session ID
    raw_session = sanitized.get("anonymous_session_id") or sanitized.get("session_id")
    if not raw_session or not str(raw_session).startswith("ANON-"):
        sanitized["anonymous_session_id"] = generate_anonymous_session_id(str(raw_session or ""))
    else:
        sanitized["anonymous_session_id"] = str(raw_session)

    if "session_id" in sanitized and sanitized["session_id"] != sanitized["anonymous_session_id"]:
        del sanitized["session_id"]

    # Bucketize timestamp
    raw_ts = sanitized.get("timestamp_bucket") or sanitized.get("timestamp") or sanitized.get("created_at")
    sanitized["timestamp_bucket"] = bucketize_timestamp(raw_ts)

    # Standardize allowed schema
    allowed_keys = {
        "event_id",
        "anonymous_session_id",
        "workflow_stage",
        "event_type",
        "timestamp_bucket",
        "consent_status",
        "portal_version",
        "event_source",
    }
    return {k: sanitized[k] for k in sanitized if k in allowed_keys}
