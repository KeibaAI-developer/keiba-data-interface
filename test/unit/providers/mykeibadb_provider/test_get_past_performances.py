"""MykeibaDBProvider.get_past_performances関数のテスト."""

from unittest.mock import MagicMock

import pandas as pd

from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.schema.columns import RACE_INFO_BY_HORSE_COLUMNS

from .conftest import create_umagoto_race_joho_df


# 正常系
def test_output_columns_match_schema(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
) -> None:
    """出力DataFrameのカラム構成がHORSE_RACE_INFO_COLUMNSと一致する."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    result = provider.get_past_performances("1234567890")

    assert list(result.columns) == RACE_INFO_BY_HORSE_COLUMNS


def test_output_row_count(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
) -> None:
    """出力DataFrameの行数が入力と一致する."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    result = provider.get_past_performances("1234567890")

    assert len(result) == 2


def test_race_getter_called_with_horse_id(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
) -> None:
    """RaceGetter.get_umagoto_race_joho()が馬IDで呼ばれる."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    provider.get_past_performances("1234567890")

    mock_race_getter.get_umagoto_race_joho.assert_called_once_with(
        ketto_toroku_bango="1234567890", convert_codes=False
    )


def test_soha_time_converted(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
) -> None:
    """走破タイムが"MSSS"から"M:SS.S"に変換される（get_resultと同じ変換）."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    result = provider.get_past_performances("1234567890")

    assert result.iloc[0]["走破タイム"] == "2:31.5"
    assert result.iloc[1]["走破タイム"] == "2:31.6"


def test_empty_dataframe_returns_empty(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
) -> None:
    """新馬（0行）の場合は空のDataFrameが返る."""
    empty = pd.DataFrame(columns=create_umagoto_race_joho_df().columns)
    mock_race_getter.get_umagoto_race_joho.return_value = empty

    result = provider.get_past_performances("9999999999")

    assert len(result) == 0
    assert list(result.columns) == RACE_INFO_BY_HORSE_COLUMNS
