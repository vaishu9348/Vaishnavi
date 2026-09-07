"""
Coexistence & Rollback Controller
Manages operational states (LEGACY, COEXISTENCE, MODERN),
failure injection simulation, automatic fallback triggers,
and non-blocking event adapter dispatch.
"""

from enum import Enum
from typing import Dict, Any, Optional
import sqlite3
import os
import threading
from datetime import datetime
from app.health import global_health_monitor

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "synthetic", "insurance_portal.db")


class SystemMode(str, Enum):
    LEGACY = "LEGACY"
    COEXISTENCE = "COEXISTENCE"
    MODERN = "MODERN"
    LEGACY_FALLBACK = "LEGACY_FALLBACK"


class RollbackController:
    """
    Controls operational modes and orchestrates non-blocking fallback transitions.
    Guarantees that analytics downtime NEVER interrupts core insurance claim submission.
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._current_mode = SystemMode.COEXISTENCE
        self._analytics_simulated_failed = False
        self._claims_processed_during_outage = 0
        self._outage_timestamp: Optional[str] = None

    @property
    def current_mode(self) -> SystemMode:
        return self._current_mode

    @property
    def is_analytics_failed(self) -> bool:
        return self._analytics_simulated_failed

    @property
    def outage_stats(self) -> Dict[str, Any]:
        return {
            "current_mode": self._current_mode.value,
            "analytics_simulated_failed": self._analytics_simulated_failed,
            "claims_processed_during_outage": self._claims_processed_during_outage,
            "outage_timestamp": self._outage_timestamp,
        }

    def set_mode(self, mode: SystemMode, actor: str = "ADMIN"):
        """Explicitly sets operational mode."""
        with self._lock:
            old_mode = self._current_mode
            self._current_mode = mode
            self._log_audit("MODE_CHANGE", actor, f"Mode changed from {old_mode.value} to {mode.value}", "SUCCESS")

    def simulate_analytics_failure(self, actor: str = "DEMO_SIMULATOR"):
        """
        Simulates an unexpected analytics service failure:
        1. Sets analytics health state to unavailable
        2. Automatically triggers rollback to LEGACY_FALLBACK
        3. Core claim processing continues without interruption
        """
        with self._lock:
            self._analytics_simulated_failed = True
            self._outage_timestamp = datetime.utcnow().isoformat()
            global_health_monitor.set_analytics_simulated_health(False)
            self._current_mode = SystemMode.LEGACY_FALLBACK
            self._log_audit(
                "ANALYTICS_FAILURE_SIMULATED",
                actor,
                "Simulated analytics outage triggered. Auto-rollback to LEGACY_FALLBACK activated.",
                "ACTIVE_OUTAGE"
            )

    def restore_services(self, target_mode: SystemMode = SystemMode.COEXISTENCE, actor: str = "ADMIN"):
        """Restores healthy operations after failure test or resolved outage."""
        with self._lock:
            self._analytics_simulated_failed = False
            self._outage_timestamp = None
            global_health_monitor.set_analytics_simulated_health(True)
            self._current_mode = target_mode
            self._log_audit(
                "ANALYTICS_RESTORED",
                actor,
                f"Analytics service restored. Mode returned to {target_mode.value}.",
                "SUCCESS"
            )

    def restore_analytics_service(self, target_mode: SystemMode = SystemMode.COEXISTENCE, actor: str = "ADMIN"):
        """Alias for restore_services."""
        return self.restore_services(target_mode=target_mode, actor=actor)

    def record_claim_processed(self, is_outage: bool = False):
        """Records a successful claim submission during normal or degraded mode."""
        if self._analytics_simulated_failed or is_outage:
            self._claims_processed_during_outage += 1

    def dispatch_event_adapter(self, event_data: Dict[str, Any]) -> bool:
        """
        Non-blocking event dispatch adapter.
        If analytics is in LEGACY mode or analytics service has failed:
        Drops analytics dispatch gracefully, logs warning, returns True.
        Legacy claim processing NEVER halts!
        """
        # If in Legacy mode, event dispatch is completely decoupled/bypassed
        if self._current_mode == SystemMode.LEGACY:
            return True

        # If analytics failure is simulated, bypass analytics ingestion gracefully
        if self._analytics_simulated_failed or self._current_mode == SystemMode.LEGACY_FALLBACK:
            # Silently drop analytics event to guarantee zero customer impact
            return True

        # In COEXISTENCE or MODERN mode: Attempt non-blocking event recording
        try:
            if os.path.exists(self.db_path):
                conn = sqlite3.connect(self.db_path, timeout=1.0)
                cur = conn.cursor()
                cur.execute("""
                    INSERT OR IGNORE INTO interaction_events (
                        event_id, anonymous_session_id, workflow_stage, event_type,
                        timestamp_bucket, consent_status, portal_version, event_source, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event_data.get("event_id"),
                    event_data.get("anonymous_session_id"),
                    event_data.get("workflow_stage"),
                    event_data.get("event_type"),
                    event_data.get("timestamp_bucket"),
                    event_data.get("consent_status"),
                    event_data.get("portal_version", "v2.5-coexistence"),
                    event_data.get("event_source", "web_claims_portal"),
                    event_data.get("created_at", datetime.utcnow().isoformat()),
                ))
                conn.commit()
                conn.close()
            return True
        except Exception:
            # Fall-safe: Even if DB write fails, return True so customer claim proceeds!
            return True

    def _log_audit(self, action: str, actor: str, details: str, status: str):
        try:
            if os.path.exists(self.db_path):
                conn = sqlite3.connect(self.db_path, timeout=1.0)
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO audit_log (timestamp, action, actor_role, details, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (datetime.utcnow().isoformat(), action, actor, details, status))
                conn.commit()
                conn.close()
        except Exception:
            pass


# Singleton global controller instance
global_rollback_controller = RollbackController()

# Alias for CoexistenceController
CoexistenceController = RollbackController
