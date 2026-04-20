"""カラム名リストを検証するテスト."""

from collections import Counter

import pytest

from keiba_data_interface.schema.columns import (
    HORSE_RACE_INFO_COLUMNS,
    ODDS_COLUMNS,
    PAYOFF_COLUMNS,
    RACE_INFO_COLUMNS,
    RACE_RESULT_INFO_COLUMNS,
    SCHEDULE_COLUMNS,
)

_TABLE_PARAMS = [
    (RACE_INFO_COLUMNS, 70, "レース基本情報"),
    (RACE_RESULT_INFO_COLUMNS, 65, "レース結果情報"),
    (HORSE_RACE_INFO_COLUMNS, 67, "馬毎レース情報"),
    (PAYOFF_COLUMNS, 222, "払戻情報"),
    (ODDS_COLUMNS, 13, "単複オッズ情報"),
    (SCHEDULE_COLUMNS, 43, "開催スケジュール情報"),
]


# 正常系
@pytest.mark.parametrize("columns, expected_count, table_name", _TABLE_PARAMS)
def test_column_count_matches_schema(
    columns: list[str], expected_count: int, table_name: str
) -> None:
    """各テーブルのカラム数がdoc/SCHEMA.mdの定義と一致する."""
    assert (
        len(columns) == expected_count
    ), f"{table_name}のカラム数が不一致: 期待値={expected_count}, 実際={len(columns)}"


@pytest.mark.parametrize("columns, expected_count, table_name", _TABLE_PARAMS)
def test_no_duplicate_columns(columns: list[str], expected_count: int, table_name: str) -> None:
    """各テーブルのカラム名に重複がない."""
    duplicates = [col for col, count in Counter(columns).items() if count > 1]
    assert len(duplicates) == 0, f"{table_name}に重複カラムあり: {set(duplicates)}"
