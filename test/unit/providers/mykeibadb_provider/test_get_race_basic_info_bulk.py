"""MykeibaDBProvider.get_race_basic_info_bulk関数のテスト."""

from unittest.mock import MagicMock

import pandas as pd

from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.schema.columns import RACE_BASIC_INFO_COLUMNS

from .conftest import create_race_shosai_df

_RACE_CODES = ["2025050206050811", "2025050206050812", "2025050206050810"]


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
def test_output_columns_match_schema(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
) -> None:
    """出力DataFrameのカラム構成がRACE_BASIC_INFO_COLUMNSと一致する."""
    mock_race_getter.get_race_shosai.return_value = _make_raw(_RACE_CODES)

    result = provider.get_race_basic_info_bulk(_RACE_CODES)

    assert list(result.columns) == RACE_BASIC_INFO_COLUMNS


def test_returns_one_row_per_race_code(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
) -> None:
    """指定したレースコードごとに1行を返す."""
    mock_race_getter.get_race_shosai.return_value = _make_raw(_RACE_CODES)

    result = provider.get_race_basic_info_bulk(_RACE_CODES)

    assert len(result) == len(_RACE_CODES)


def test_rows_are_sorted_by_race_code(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
) -> None:
    """戻り値がレースコード昇順に並ぶ."""
    mock_race_getter.get_race_shosai.return_value = _make_raw(_RACE_CODES)

    result = provider.get_race_basic_info_bulk(_RACE_CODES)

    assert result["レースコード"].tolist() == sorted(_RACE_CODES)


def test_issues_single_query(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
) -> None:
    """レース数によらずクエリが1回だけ発行される.

    レースコードごとに取得するとレース数だけクエリが発行される。まとめて取得する
    ことがこのメソッドの目的であるため、呼び出し回数を固定する。
    """
    mock_race_getter.get_race_shosai.return_value = _make_raw(_RACE_CODES)

    provider.get_race_basic_info_bulk(_RACE_CODES)

    mock_race_getter.get_race_shosai.assert_called_once()


def test_passes_race_codes_as_list(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
) -> None:
    """get_race_shosaiへレースコードのリストが渡される."""
    mock_race_getter.get_race_shosai.return_value = _make_raw(_RACE_CODES)

    provider.get_race_basic_info_bulk(_RACE_CODES)

    kwargs = mock_race_getter.get_race_shosai.call_args.kwargs
    assert kwargs["race_code"] == _RACE_CODES
    assert kwargs["convert_codes"] is False


# 準正常系
def test_duplicated_race_codes_are_deduplicated(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
) -> None:
    """重複したレースコードを渡しても1レース1行を返す."""
    duplicated = ["2025050206050811", "2025050206050811", "2025050206050812"]
    mock_race_getter.get_race_shosai.return_value = _make_raw(
        ["2025050206050811", "2025050206050812"]
    )

    result = provider.get_race_basic_info_bulk(duplicated)

    kwargs = mock_race_getter.get_race_shosai.call_args.kwargs
    assert kwargs["race_code"] == ["2025050206050811", "2025050206050812"]
    assert len(result) == 2


def test_missing_race_code_is_not_included(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
) -> None:
    """存在しないレースコードが混ざっても例外にならず、その行だけ返らない."""
    mock_race_getter.get_race_shosai.return_value = _make_raw(["2025050206050811"])

    result = provider.get_race_basic_info_bulk(["2025050206050811", "9999999999999999"])

    assert len(result) == 1
    assert result["レースコード"].tolist() == ["2025050206050811"]


def test_empty_list_returns_empty_frame_without_query(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
) -> None:
    """空リストを渡すとクエリを発行せず、カラムを持つ0行のDataFrameを返す."""
    result = provider.get_race_basic_info_bulk([])

    mock_race_getter.get_race_shosai.assert_not_called()
    assert result.empty
    assert list(result.columns) == RACE_BASIC_INFO_COLUMNS


def test_all_race_codes_missing_returns_empty_frame(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
) -> None:
    """指定した全レースコードが存在しない場合、0行のDataFrameを返す."""
    mock_race_getter.get_race_shosai.return_value = _make_raw(["2025050206050811"]).iloc[0:0]

    result = provider.get_race_basic_info_bulk(["9999999999999999"])

    assert result.empty
    assert list(result.columns) == RACE_BASIC_INFO_COLUMNS
