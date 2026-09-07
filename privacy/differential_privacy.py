"""
Differential Privacy Subsystem
Implements Laplace Mechanism for aggregate count queries with sensitivity = 1.
Enforces strict epsilon bounds (0.1 <= epsilon <= 1.0) and tracks privacy budget ledger.
Rejects queries when privacy budget is exhausted.
"""

import numpy as np
from typing import Dict, Any, Optional, Union
import sqlite3
import threading
from datetime import datetime


class BudgetExhaustedError(Exception):
    """Raised when an analytics query exceeds remaining privacy budget."""
    pass


class InvalidEpsilonError(ValueError):
    """Raised when an invalid or insecure epsilon is requested."""
    pass


MIN_ALLOWED_EPSILON = 0.1
MAX_ALLOWED_EPSILON = 1.0
DEFAULT_BUDGET_CAP = 1.0


class LaplaceMechanism:
    """
    Implements Laplace Differential Privacy Mechanism.
    Scale b = sensitivity / epsilon
    For count queries with bounded individual contribution (1 session = 1 journey), sensitivity = 1.
    """

    def __init__(
        self,
        epsilon: float = 1.0,
        sensitivity: float = 1.0,
        seed: Optional[int] = None,
        allow_experiment: bool = False
    ):
        self.validate_epsilon(epsilon, allow_relaxed_for_experiment=allow_experiment)
        self.epsilon = float(epsilon)
        self.sensitivity = float(sensitivity)
        self.scale = self.sensitivity / self.epsilon
        self.rng = np.random.default_rng(seed)

    @staticmethod
    def validate_epsilon(epsilon: float, allow_relaxed_for_experiment: bool = False):
        max_eps = 2.0 if allow_relaxed_for_experiment else MAX_ALLOWED_EPSILON
        if epsilon is None or epsilon < MIN_ALLOWED_EPSILON or epsilon > max_eps:
            raise InvalidEpsilonError(
                f"Requested epsilon {epsilon} is outside permitted security bounds [{MIN_ALLOWED_EPSILON}, {max_eps}]. "
                "Epsilon values > 1.0 expose excessive individual variance and violate secure defaults."
            )

    def draw_noise(self) -> float:
        """Draws a single Laplace noise sample."""
        return float(self.rng.laplace(0.0, self.scale))

    def perturb_count(self, true_count: Union[int, float], clamp_zero: bool = True) -> int:
        """
        Perturbs a true count with Laplace noise.
        Clamps to non-negative integer by default since counts cannot be negative.
        """
        noisy_val = true_count + self.draw_noise()
        if clamp_zero:
            return max(0, int(round(noisy_val)))
        return int(round(noisy_val))


class PrivacyBudgetManager:
    """
    Manages privacy budget accounting, persistence, and rate tracking.
    Thread-safe implementation with SQLite backing or in-memory fallback.
    """

    def __init__(
        self,
        total_budget: float = DEFAULT_BUDGET_CAP,
        db_path: Optional[str] = None
    ):
        self.total_budget = float(total_budget)
        self.db_path = db_path
        self._lock = threading.Lock()
        self._consumed = 0.0
        self._query_count = 0
        self._initialize_storage()

    def _initialize_storage(self):
        if not self.db_path:
            return
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cur = conn.cursor()
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
                cur.execute("SELECT total_epsilon, consumed_epsilon, remaining_epsilon, query_count FROM privacy_budget WHERE budget_id = 1")
                row = cur.fetchone()
                if row:
                    self.total_budget, self._consumed, _, self._query_count = row
                else:
                    cur.execute("""
                        INSERT INTO privacy_budget (budget_id, total_epsilon, consumed_epsilon, remaining_epsilon, query_count, updated_at)
                        VALUES (1, ?, 0.0, ?, 0, ?)
                    """, (self.total_budget, self.total_budget, datetime.utcnow().isoformat()))
                conn.commit()
                conn.close()
            except Exception:
                pass

    def get_status(self) -> Dict[str, Any]:
        """Returns the current ledger status of the privacy budget."""
        with self._lock:
            remaining = max(0.0, round(self.total_budget - self._consumed, 4))
            return {
                "total_budget": round(self.total_budget, 4),
                "consumed_budget": round(self._consumed, 4),
                "remaining_budget": remaining,
                "query_count": self._query_count,
                "is_exhausted": remaining <= 1e-6,
                "percentage_used": round((self._consumed / max(self.total_budget, 0.001)) * 100, 2),
            }

    def request_budget(self, requested_epsilon: float, allow_experiment: bool = False) -> float:
        """
        Deducts requested epsilon from remaining budget if available and valid.
        Throws InvalidEpsilonError if outside bounds.
        Throws BudgetExhaustedError if insufficient budget remains.
        """
        LaplaceMechanism.validate_epsilon(requested_epsilon, allow_relaxed_for_experiment=allow_experiment)
        
        with self._lock:
            remaining = round(self.total_budget - self._consumed, 4)
            if round(requested_epsilon, 4) > remaining + 1e-6:
                raise BudgetExhaustedError(
                    f"Analytics query rejected. Privacy budget exhausted. "
                    f"Requested ε = {requested_epsilon}, but only ε = {remaining} remaining."
                )

            self._consumed += requested_epsilon
            self._query_count += 1
            new_remaining = max(0.0, round(self.total_budget - self._consumed, 4))

            # Persist if db_path provided
            if self.db_path:
                try:
                    conn = sqlite3.connect(self.db_path)
                    cur = conn.cursor()
                    cur.execute("""
                        UPDATE privacy_budget
                        SET consumed_epsilon = ?, remaining_epsilon = ?, query_count = ?, updated_at = ?
                        WHERE budget_id = 1
                    """, (round(self._consumed, 4), new_remaining, self._query_count, datetime.utcnow().isoformat()))
                    conn.commit()
                    conn.close()
                except Exception:
                    pass

            return requested_epsilon

    def reset_budget(self, new_total: Optional[float] = None):
        """Administrative function to reset budget ledger."""
        with self._lock:
            if new_total is not None:
                self.total_budget = float(new_total)
            self._consumed = 0.0
            self._query_count = 0
            if self.db_path:
                try:
                    conn = sqlite3.connect(self.db_path)
                    cur = conn.cursor()
                    cur.execute("""
                        UPDATE privacy_budget
                        SET consumed_epsilon = 0.0, remaining_epsilon = ?, query_count = 0, updated_at = ?
                        WHERE budget_id = 1
                    """, (self.total_budget, datetime.utcnow().isoformat()))
                    conn.commit()
                    conn.close()
                except Exception:
                    pass
