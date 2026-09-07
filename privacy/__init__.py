"""
Privacy Layer for Insurance Journey Analytics Platform
Includes strict consent enforcement, one-way anonymisation,
aggregation without individual traces, minimum group-size suppression,
and differential privacy using Laplace mechanism with bounded privacy budget.
"""

from .consent import ConsentStatus, filter_consented_events, validate_event_consent
from .anonymization import sanitize_event, generate_anonymous_session_id, bucketize_timestamp
from .aggregation import AggregateJourneyStats, aggregate_stage_metrics
from .suppression import apply_small_group_suppression, SuppressionResult
from .differential_privacy import LaplaceMechanism, PrivacyBudgetManager, BudgetExhaustedError, InvalidEpsilonError

__all__ = [
    "ConsentStatus",
    "filter_consented_events",
    "validate_event_consent",
    "sanitize_event",
    "generate_anonymous_session_id",
    "bucketize_timestamp",
    "AggregateJourneyStats",
    "aggregate_stage_metrics",
    "apply_small_group_suppression",
    "SuppressionResult",
    "LaplaceMechanism",
    "PrivacyBudgetManager",
    "BudgetExhaustedError",
    "InvalidEpsilonError",
]
