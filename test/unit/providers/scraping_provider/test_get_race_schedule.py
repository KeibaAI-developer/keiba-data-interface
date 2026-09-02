"""ScrapingProvider.get_race_schedule関数のテスト."""

from datetime import date
from unittest.mock import MagicMock

import pandas as pd
import pytest

from keiba_data_interface.exceptions import RaceCodeError
from keiba_data_interface.providers.scraping_provider import ScrapingProvider
from keiba_data_interface.schema.columns import RACE_SCHEDULE_COLUMNS

from .conftest import create_scraping_schedule


# 正常系
def test_output_columns_match_schema(
    provider_full: ScrapingProvider, mock_schedule_scraper: MagicMock
) -> None:
    """出力DataFrameのカラム構成がRACE_SCHEDULE_COLUMNSと一致する."""
    mock_schedule_scraper.get_race_schedule.return_value = create_scraping_schedule()

    result = provider_full.get_race_schedule("20250105")

    assert list(result.columns) == RACE_SCHEDULE_COLUMNS


def test_scraper_created_for_target_date(
    provider_full: ScrapingProvider,
    mock_schedule_scraper_cls: MagicMock,
    mock_schedule_scraper: MagicMock,
) -> None:
    """対象日のRaceScheduleScraperが1回だけ作られる."""
    mock_schedule_scraper.get_race_schedule.return_value = create_scraping_schedule()

    provider_full.get_race_schedule("20250105")

    mock_schedule_scraper_cls.assert_called_once_with(2025, 1, 5, logger=provider_full._logger)


def test_race_code_built_from_race_id_and_date(
    provider_full: ScrapingProvider, mock_schedule_scraper: MagicMock
) -> None:
    """レースIDと日付から16桁のレースコードを組み立て、レースコード昇順に並ぶ."""
    mock_schedule_scraper.get_race_schedule.return_value = create_scraping_schedule()

    result = provider_full.get_race_schedule("20250105")

    assert result["レースコード"].tolist() == [
        "2025010505010101",
        "2025010505010102",
        "2025010506020101",
    ]


def test_values_converted(
    provider_full: ScrapingProvider, mock_schedule_scraper: MagicMock
) -> None:
    """競馬場コード・レース番号・発走時刻・競走名が統一スキーマの値になる."""
    mock_schedule_scraper.get_race_schedule.return_value = create_scraping_schedule()

    result = provider_full.get_race_schedule("20250105")

    row = result.iloc[1]
    assert row["競馬場コード"] == "05"
    assert row["レース番号"] == 2
    assert row["発走時刻"] == "10:30"
    assert row["競走名"] == "3歳未勝利"


def test_missing_start_time_is_na(
    provider_full: ScrapingProvider, mock_schedule_scraper: MagicMock
) -> None:
    """発走時刻が空のレースは欠損になる."""
    raw = create_scraping_schedule()
    raw.loc[0, "発走時刻"] = ""
    mock_schedule_scraper.get_race_schedule.return_value = raw

    result = provider_full.get_race_schedule("20250105")

    assert pd.isna(result.iloc[0]["発走時刻"])


def test_empty_schedule(provider_full: ScrapingProvider, mock_schedule_scraper: MagicMock) -> None:
    """開催が無い日は0行のDataFrameが返る（カラムはスキーマと一致）."""
    mock_schedule_scraper.get_race_schedule.return_value = pd.DataFrame()

    result = provider_full.get_race_schedule("20250105")

    assert len(result) == 0
    assert list(result.columns) == RACE_SCHEDULE_COLUMNS


# 準正常系
def test_invalid_race_id_raises(
    provider_full: ScrapingProvider, mock_schedule_scraper: MagicMock
) -> None:
    """レースIDが12桁の数字でない場合はRaceCodeErrorが発生する."""
    raw = create_scraping_schedule()
    raw.loc[0, "レースID"] = "abc"
    mock_schedule_scraper.get_race_schedule.return_value = raw

    with pytest.raises(RaceCodeError):
        provider_full.get_race_schedule("20250105")


def test_date_object_not_used_for_race_code(
    provider_full: ScrapingProvider, mock_schedule_scraper: MagicMock
) -> None:
    """レースコードの日付部分は引数の日付から組み立てる（出力の日付列には依存しない）."""
    raw = create_scraping_schedule()
    raw["日付"] = date(2024, 12, 31)
    mock_schedule_scraper.get_race_schedule.return_value = raw

    result = provider_full.get_race_schedule("20250105")

    assert result["レースコード"].tolist()[0].startswith("20250105")
