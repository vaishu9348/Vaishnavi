"""
Tests for System Coexistence & Rollback Controller
Validates state transitions between LEGACY, COEXISTENCE, MODERN, and LEGACY_FALLBACK.
"""

import sys
import os
import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from app.rollback import RollbackController, SystemMode


def test_initial_mode_is_coexistence(tmp_path):
    db_file = str(tmp_path / "rollback_test.db")
    controller = RollbackController(db_path=db_file)
    assert controller.current_mode == SystemMode.COEXISTENCE
    assert controller.is_analytics_failed is False


def test_mode_transitions(tmp_path):
    db_file = str(tmp_path / "rollback_test.db")
    controller = RollbackController(db_path=db_file)

    controller.set_mode(SystemMode.MODERN)
    assert controller.current_mode == SystemMode.MODERN

    controller.set_mode(SystemMode.LEGACY)
    assert controller.current_mode == SystemMode.LEGACY


def test_simulate_failure_and_restore(tmp_path):
    db_file = str(tmp_path / "rollback_test.db")
    controller = RollbackController(db_path=db_file)

    # Trigger failure
    controller.simulate_analytics_failure()
    assert controller.is_analytics_failed is True
    assert controller.current_mode == SystemMode.LEGACY_FALLBACK

    # Record claim during outage
    controller.record_claim_processed()
    assert controller.outage_stats["claims_processed_during_outage"] == 1

    # Restore service
    controller.restore_services(SystemMode.COEXISTENCE)
    assert controller.is_analytics_failed is False
    assert controller.current_mode == SystemMode.COEXISTENCE
