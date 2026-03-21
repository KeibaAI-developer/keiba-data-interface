"""スキーマ定義モジュール.

各テーブルのカラム名定数リストおよび型定義辞書を提供する。
"""

from keiba_data_interface.schema.columns import (
    HORSE_RACE_INFO_COLUMNS,
    ODDS_COLUMNS,
    PAYOFF_COLUMNS,
    RACE_INFO_COLUMNS,
    RACE_RESULT_INFO_COLUMNS,
    SCHEDULE_COLUMNS,
)
from keiba_data_interface.schema.types import (
    HORSE_RACE_INFO_TYPES,
    ODDS_TYPES,
    PAYOFF_TYPES,
    RACE_INFO_TYPES,
    RACE_RESULT_INFO_TYPES,
    SCHEDULE_TYPES,
)

__all__ = [
    "RACE_INFO_COLUMNS",
    "RACE_RESULT_INFO_COLUMNS",
    "HORSE_RACE_INFO_COLUMNS",
    "PAYOFF_COLUMNS",
    "ODDS_COLUMNS",
    "SCHEDULE_COLUMNS",
    "RACE_INFO_TYPES",
    "RACE_RESULT_INFO_TYPES",
    "HORSE_RACE_INFO_TYPES",
    "PAYOFF_TYPES",
    "ODDS_TYPES",
    "SCHEDULE_TYPES",
]
