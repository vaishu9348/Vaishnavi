"""
Tests for Small-Group Suppression
Validates minimum group-size masking and suppression notices.
"""

import sys
import os
import pytest
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from privacy.suppression import check_and_suppress_count, apply_small_group_suppression, DEFAULT_MIN_GROUP_SIZE


def test_check_and_suppress_count():
    # Below threshold (count = 4 < 10)
    res_small = check_and_suppress_count(4, min_group_size=10)
    assert res_small.is_suppressed is True
    assert "[SUPPRESSED" in str(res_small.display_value)
    assert "Insufficient group size" in res_small.notice

    # Above threshold (count = 15 >= 10)
    res_ok = check_and_suppress_count(15, min_group_size=10)
    assert res_ok.is_suppressed is False
    assert res_ok.display_value == 15


def test_apply_small_group_suppression_df():
    df = pd.DataFrame([
        {"workflow_stage": "Stage A", "entered_count": 120, "abandoned_count": 3},
        {"workflow_stage": "Stage B", "entered_count": 5, "abandoned_count": 2},
    ])

    result = apply_small_group_suppression(df, count_columns=["entered_count", "abandoned_count"], min_group_size=10)
    supp_df = result["suppressed_df"]

    assert supp_df.at[0, "entered_count"] == 120
    assert supp_df.at[0, "abandoned_count"] == "[SUPPRESSED < 10]"
    assert supp_df.at[1, "entered_count"] == "[SUPPRESSED < 10]"
    assert supp_df.at[1, "abandoned_count"] == "[SUPPRESSED < 10]"
    assert result["total_suppressed"] == 3
