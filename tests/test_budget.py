"""
Tests for Privacy Budget Accounting
Validates budget deduction, persistence, rejection upon exhaustion, and reset.
"""

import sys
import os
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from privacy.differential_privacy import PrivacyBudgetManager, BudgetExhaustedError, InvalidEpsilonError


def test_budget_deduction():
    mgr = PrivacyBudgetManager(total_budget=1.0)
    stat0 = mgr.get_status()
    assert stat0["total_budget"] == 1.0
    assert stat0["consumed_budget"] == 0.0
    assert stat0["remaining_budget"] == 1.0

    mgr.request_budget(0.4)
    stat1 = mgr.get_status()
    assert stat1["consumed_budget"] == 0.4
    assert stat1["remaining_budget"] == 0.6
    assert stat1["query_count"] == 1


def test_budget_exhaustion_rejection():
    mgr = PrivacyBudgetManager(total_budget=1.0)
    mgr.request_budget(0.7)

    # Next query requesting 0.4 exceeds 0.3 remaining -> must raise BudgetExhaustedError
    with pytest.raises(BudgetExhaustedError):
        mgr.request_budget(0.4)


def test_budget_reset():
    mgr = PrivacyBudgetManager(total_budget=1.0)
    mgr.request_budget(0.8)
    mgr.reset_budget()
    stat = mgr.get_status()
    assert stat["consumed_budget"] == 0.0
    assert stat["remaining_budget"] == 1.0
    assert stat["query_count"] == 0
