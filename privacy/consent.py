"""
Consent Management Subsystem
Enforces explicit consent verification for all interaction events.
Default state is NEVER consented (secure-by-default).
"""

from enum import Enum
from typing import Dict, Any, List, Tuple
import pandas as pd


class ConsentStatus(str, Enum):
    CONSENTED = "CONSENTED"
    NOT_CONSENTED = "NOT_CONSENTED"
    UNKNOWN = "UNKNOWN"


def validate_event_consent(consent_val: Any) -> bool:
    """
    Validates if an event has explicit CONSENTED status.
    Conservative default: Any missing, empty, or UNKNOWN state is rejected.
    """
    if consent_val is None:
        return False
    
    val_str = str(consent_val).strip().upper()
    return val_str == ConsentStatus.CONSENTED.value


def filter_consented_events(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Filters a DataFrame of events, keeping strictly CONSENTED rows.
    Returns the filtered DataFrame and audit rejection metrics.
    """
    if df.empty or "consent_status" not in df.columns:
        return pd.DataFrame(columns=df.columns), {
            "total_received": len(df),
            "consented_count": 0,
            "not_consented_count": 0,
            "unknown_count": len(df),
            "rejection_rate": 1.0,
        }

    total = len(df)
    consented_mask = df["consent_status"].astype(str).str.upper() == ConsentStatus.CONSENTED.value
    not_consented_mask = df["consent_status"].astype(str).str.upper() == ConsentStatus.NOT_CONSENTED.value
    unknown_mask = ~ (consented_mask | not_consented_mask) | (df["consent_status"].astype(str).str.upper() == ConsentStatus.UNKNOWN.value)

    consented_df = df[consented_mask].copy()
    consented_count = int(consented_mask.sum())
    not_consented_count = int(not_consented_mask.sum())
    unknown_count = total - consented_count - not_consented_count

    stats = {
        "total_received": total,
        "consented_count": consented_count,
        "not_consented_count": not_consented_count,
        "unknown_count": unknown_count,
        "rejection_rate": round((total - consented_count) / max(total, 1), 4),
    }

    return consented_df, stats


def is_event_allowed(event: Dict[str, Any]) -> bool:
    """Check a single event dictionary for explicit consent."""
    consent = event.get("consent_status")
    return validate_event_consent(consent)
