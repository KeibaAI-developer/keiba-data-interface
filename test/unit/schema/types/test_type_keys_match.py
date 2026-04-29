"""型定義辞書のキーがカラム名リストと一致することを検証するテスト."""

import pytest

from keiba_data_interface.schema.columns import (
    RACE_INFO_BY_HORSE_COLUMNS,
    WIN_SHOW_ODDS_COLUMNS,
    PAYOFF_COLUMNS,
    RACE_BASIC_INFO_COLUMNS,
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


# 正常系
@pytest.mark.parametrize(
    "columns, types_dict, table_name",
    [
        (RACE_BASIC_INFO_COLUMNS, RACE_INFO_TYPES, "レース基本情報"),
        (RACE_RESULT_INFO_COLUMNS, RACE_RESULT_INFO_TYPES, "レース結果情報"),
        (RACE_INFO_BY_HORSE_COLUMNS, HORSE_RACE_INFO_TYPES, "馬毎レース情報"),
        (PAYOFF_COLUMNS, PAYOFF_TYPES, "払戻情報"),
        (WIN_SHOW_ODDS_COLUMNS, ODDS_TYPES, "単複オッズ情報"),
        (SCHEDULE_COLUMNS, SCHEDULE_TYPES, "開催スケジュール情報"),
    ],
)
def test_type_keys_match_columns(
    columns: list[str], types_dict: dict[str, str], table_name: str
) -> None:
    """型定義辞書のキーがカラム名リストと一致する."""
    column_set = set(columns)
    type_key_set = set(types_dict.keys())

    missing_in_types = column_set - type_key_set
    extra_in_types = type_key_set - column_set

    assert (
        missing_in_types == set()
    ), f"{table_name}: 型定義に不足しているカラム: {missing_in_types}"
    assert extra_in_types == set(), f"{table_name}: 型定義に余分なカラム: {extra_in_types}"


@pytest.mark.parametrize(
    "columns, types_dict, table_name",
    [
        (RACE_BASIC_INFO_COLUMNS, RACE_INFO_TYPES, "レース基本情報"),
        (RACE_RESULT_INFO_COLUMNS, RACE_RESULT_INFO_TYPES, "レース結果情報"),
        (RACE_INFO_BY_HORSE_COLUMNS, HORSE_RACE_INFO_TYPES, "馬毎レース情報"),
        (PAYOFF_COLUMNS, PAYOFF_TYPES, "払戻情報"),
        (WIN_SHOW_ODDS_COLUMNS, ODDS_TYPES, "単複オッズ情報"),
        (SCHEDULE_COLUMNS, SCHEDULE_TYPES, "開催スケジュール情報"),
    ],
)
def test_type_values_are_valid_pandas_types(
    columns: list[str], types_dict: dict[str, str], table_name: str
) -> None:
    """型定義辞書の値が有効なpandas型文字列である."""
    valid_types = {"object", "Int64", "Float64"}
    for col_name, type_str in types_dict.items():
        assert (
            type_str in valid_types
        ), f"{table_name}.{col_name}: 無効な型 '{type_str}' (有効: {valid_types})"
