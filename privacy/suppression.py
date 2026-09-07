"""
Small-Group Suppression Subsystem
Implements minimum group-size threshold protection (k-anonymity principle).
Any aggregate count below MIN_GROUP_SIZE is suppressed with an explicit notice.
"""

from typing import Dict, Any, List, Union
from dataclasses import dataclass
import pandas as pd

DEFAULT_MIN_GROUP_SIZE = 10
SUPPRESSION_NOTICE = "Insufficient group size. Result suppressed for privacy protection."


@dataclass
class SuppressionResult:
    is_suppressed: bool
    display_value: Union[int, float, str]
    raw_value: Union[int, float]
    min_threshold: int
    notice: str = ""


def check_and_suppress_count(count_value: Union[int, float], min_group_size: int = DEFAULT_MIN_GROUP_SIZE) -> SuppressionResult:
    """
    Checks if a count is below the minimum group size threshold.
    Returns a SuppressionResult with notice if suppressed.
    """
    if count_value < min_group_size:
        return SuppressionResult(
            is_suppressed=True,
            display_value="[SUPPRESSED < 10]",
            raw_value=count_value,
            min_threshold=min_group_size,
            notice=SUPPRESSION_NOTICE,
        )
    return SuppressionResult(
        is_suppressed=False,
        display_value=int(count_value),
        raw_value=count_value,
        min_threshold=min_group_size,
        notice="",
    )


def apply_small_group_suppression(
    df: pd.DataFrame,
    count_columns: List[str] = None,
    min_group_size: int = DEFAULT_MIN_GROUP_SIZE
) -> Dict[str, Any]:
    """
    Applies small-group suppression across designated count columns in a DataFrame.
    Returns:
      - suppressed_df: DataFrame with suppressed values masked
      - suppression_rate: fraction of cells suppressed
      - total_suppressions: integer count of suppressed cells
    """
    if count_columns is None:
        count_columns = ["entered_count", "completed_count", "abandoned_count", "error_count"]

    df_suppressed = df.copy()
    total_checked = 0
    suppressed_count = 0

    for col in count_columns:
        if col in df_suppressed.columns:
            df_suppressed[col] = df_suppressed[col].astype(object)
            for idx in df_suppressed.index:
                val = df_suppressed.at[idx, col]
                if isinstance(val, (int, float)):
                    total_checked += 1
                    if val < min_group_size:
                        df_suppressed.at[idx, col] = "[SUPPRESSED < 10]"
                        suppressed_count += 1

    suppression_rate = round(suppressed_count / max(total_checked, 1), 4)

    return {
        "suppressed_df": df_suppressed,
        "suppression_rate": suppression_rate,
        "total_suppressed": suppressed_count,
        "total_cells_checked": total_checked,
        "min_group_size": min_group_size,
        "notice": SUPPRESSION_NOTICE if suppressed_count > 0 else "",
    }
