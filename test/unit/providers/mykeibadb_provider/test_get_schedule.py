"""MykeibaDBProvider.get_schedule関数のテスト."""

from datetime import date
from unittest.mock import MagicMock

import pandas as pd

from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.schema.columns import SCHEDULE_COLUMNS

from .conftest import create_kaisai_schedule_df


# 正常系
def test_output_columns_match_schema(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
) -> None:
    """出力DataFrameのカラム構成がSCHEDULE_COLUMNSと一致する."""
    mock_race_getter.get_kaisai_schedule.return_value = create_kaisai_schedule_df()

    result = provider.get_schedule("2025-05-02", "2025-05-02")

    assert list(result.columns) == SCHEDULE_COLUMNS


def test_output_row_count(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
) -> None:
    """出力DataFrameの行数が入力の開催場数と一致する."""
    mock_race_getter.get_kaisai_schedule.return_value = create_kaisai_schedule_df()

    result = provider.get_schedule("2025-05-02", "2025-05-02")

    assert len(result) == 2


def test_race_getter_called_with_correct_args(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
) -> None:
    """RaceGetter.get_kaisai_schedule()が正しい引数で呼ばれる."""
    mock_race_getter.get_kaisai_schedule.return_value = create_kaisai_schedule_df()

    provider.get_schedule("2025-05-02", "2025-05-02")

    mock_race_getter.get_kaisai_schedule.assert_called_once_with(
        start_date=date(2025, 5, 2),
        end_date=date(2025, 5, 2),
        convert_codes=True,
    )


def test_header_columns_renamed(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
) -> None:
    """ヘッダカラムが日本語にリネームされる."""
    mock_race_getter.get_kaisai_schedule.return_value = create_kaisai_schedule_df()

    result = provider.get_schedule("2025-05-02", "2025-05-02")

    row = result.iloc[0]
    assert row["開催コード"] == "2025050206050800"
    assert row["開催年"] == "2025"
    assert row["開催月日"] == "0502"
    assert row["競馬場コード"] == "06"
    assert row["開催回"] == 5
    assert row["開催日目"] == 8
    assert row["曜日コード"] == "0"


def test_jusho_columns_renamed(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
) -> None:
    """重賞情報カラムが日本語にリネームされる."""
    mock_race_getter.get_kaisai_schedule.return_value = create_kaisai_schedule_df()

    result = provider.get_schedule("2025-05-02", "2025-05-02")

    row = result.iloc[0]
    assert row["重賞1特別競走番号"] == 1234
    assert row["重賞1競走名本題"] == "皐月賞"
    assert row["重賞1競走名略称3文字"] == "皐月"
    assert row["重賞1重賞回次"] == 85
    assert row["重賞1グレードコード"] == "A"
    assert row["重賞1競走種別コード"] == "12"
    assert row["重賞1距離"] == 2000
    assert row["重賞1トラックコード"] == "17"


def test_missing_jusho_nan(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
) -> None:
    """重賞情報がない開催場では重賞カラムがNaNである."""
    mock_race_getter.get_kaisai_schedule.return_value = create_kaisai_schedule_df()

    result = provider.get_schedule("2025-05-02", "2025-05-02")

    row = result.iloc[1]  # 東京（重賞情報なし）
    assert pd.isna(row["重賞1特別競走番号"])
    assert pd.isna(row["重賞1競走名本題"])
    assert pd.isna(row["重賞1グレードコード"])


def test_second_row_data(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
) -> None:
    """2行目のデータが正しく変換される."""
    mock_race_getter.get_kaisai_schedule.return_value = create_kaisai_schedule_df()

    result = provider.get_schedule("2025-05-02", "2025-05-02")

    row = result.iloc[1]
    assert row["開催コード"] == "2025050205050800"
    assert row["競馬場コード"] == "05"


def test_empty_schedule(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
) -> None:
    """空の入力で空DataFrameが返る（カラムはスキーマと一致）."""
    mock_race_getter.get_kaisai_schedule.return_value = pd.DataFrame()

    result = provider.get_schedule("2025-01-01", "2025-01-01")

    assert len(result) == 0
    assert list(result.columns) == SCHEDULE_COLUMNS
