"""convert_race_basic_info_bulk関数のテスト."""

import pandas as pd
import pytest

from keiba_data_interface.providers.mykeibadb_converters import (
    convert_race_basic_info,
    convert_race_basic_info_bulk,
)
from keiba_data_interface.schema.columns import RACE_BASIC_INFO_COLUMNS

from ..mykeibadb_provider.conftest import create_race_shosai_df


def _make_raw(race_codes: list[str]) -> pd.DataFrame:
    """指定したレースコードを持つRACE_SHOSAI出力を生成する.

    Args:
        race_codes (list[str]): レースコードのリスト

    Returns:
        pd.DataFrame: 各レースコード1行のRACE_SHOSAI出力形式
    """
    rows = []
    for race_code in race_codes:
        row = create_race_shosai_df().iloc[0].copy()
        row["race_code"] = race_code
        row["race_bango"] = int(race_code[-2:])
        rows.append(row)
    return pd.DataFrame(rows).reset_index(drop=True)


# 正常系
def test_output_columns_match_single_row_version() -> None:
    """出力カラム構成が1行版と一致する."""
    raw = _make_raw(["2025050206050811", "2025050206050812"])

    result = convert_race_basic_info_bulk(raw)

    assert list(result.columns) == RACE_BASIC_INFO_COLUMNS


def test_each_row_matches_single_row_version() -> None:
    """各行の値が1行版convert_race_basic_infoの結果と一致する.

    複数行対応は変換本体の切り出しのみで、変換ロジックは1行版と共有している。
    """
    race_codes = ["2025050206050811", "2025050206050812", "2025050206050810"]
    raw = _make_raw(race_codes)

    result = convert_race_basic_info_bulk(raw)

    for race_code in race_codes:
        single_raw = raw[raw["race_code"] == race_code].reset_index(drop=True)
        expected = convert_race_basic_info(single_raw)
        actual = result[result["レースコード"] == race_code].reset_index(drop=True)
        pd.testing.assert_frame_equal(actual, expected)


def test_rows_are_sorted_by_race_code() -> None:
    """戻り値がレースコード昇順に並ぶ."""
    raw = _make_raw(["2025050206050812", "2025050206050810", "2025050206050811"])

    result = convert_race_basic_info_bulk(raw)

    assert result["レースコード"].tolist() == [
        "2025050206050810",
        "2025050206050811",
        "2025050206050812",
    ]


def test_single_row_input_returns_one_row() -> None:
    """1行の入力でも1行を返す."""
    raw = _make_raw(["2025050206050811"])

    result = convert_race_basic_info_bulk(raw)

    assert len(result) == 1


# 準正常系
def test_empty_input_returns_empty_frame_with_columns() -> None:
    """0行の入力でRACE_BASIC_INFO_COLUMNSを持つ0行のDataFrameを返す.

    存在しないレースコードだけを指定した場合にこの経路を通る。
    """
    raw = _make_raw(["2025050206050811"]).iloc[0:0]

    result = convert_race_basic_info_bulk(raw)

    assert result.empty
    assert list(result.columns) == RACE_BASIC_INFO_COLUMNS


# 回帰（1行版の振る舞いを変えていないこと）
def test_single_row_version_raises_for_empty_input() -> None:
    """1行版が0行の入力でValueErrorを送出する."""
    raw = _make_raw(["2025050206050811"]).iloc[0:0]

    with pytest.raises(ValueError, match="空のDataFrame"):
        convert_race_basic_info(raw)


def test_single_row_version_raises_for_multiple_rows() -> None:
    """1行版が2行以上の入力でValueErrorを送出する."""
    raw = _make_raw(["2025050206050811", "2025050206050812"])

    with pytest.raises(ValueError, match="1行のDataFrameを返す必要があります"):
        convert_race_basic_info(raw)
