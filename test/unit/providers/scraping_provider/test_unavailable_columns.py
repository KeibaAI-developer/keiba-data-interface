"""scraping で取得できないカラムが常に NaN であることのテスト."""

from unittest.mock import MagicMock

import pandas as pd

from keiba_data_interface.providers.scraping_provider import ScrapingProvider
from keiba_data_interface.schema.columns import (
    RACE_BASIC_INFO_COLUMNS_UNAVAILABLE_IN_SCRAPING,
    RACE_INFO_BY_HORSE_COLUMNS_UNAVAILABLE_IN_SCRAPING,
)

from .conftest import (
    create_scraping_entry,
    create_scraping_past_performances,
    create_scraping_race_info,
    create_scraping_result,
)


def _assert_all_nan(df: pd.DataFrame, columns: frozenset[str]) -> None:
    """指定カラムがすべて NaN であることを確かめる."""
    assert len(df) > 0
    assert df[sorted(columns)].isna().all().all()


# 正常系
def test_race_basic_info(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    turf_race_info: pd.DataFrame,
    race_code: str,
) -> None:
    """レース基本情報で取得できないカラムは NaN."""
    mock_scraper.get_race_info.return_value = turf_race_info

    result = provider.get_race_basic_info(race_code)

    _assert_all_nan(result, RACE_BASIC_INFO_COLUMNS_UNAVAILABLE_IN_SCRAPING)


def test_entry(provider: ScrapingProvider, mock_scraper: MagicMock, race_code: str) -> None:
    """出馬表で取得できないカラムは NaN."""
    mock_scraper.get_entry.return_value = create_scraping_entry()

    result = provider.get_entry(race_code)

    _assert_all_nan(result, RACE_INFO_BY_HORSE_COLUMNS_UNAVAILABLE_IN_SCRAPING)


def test_result(
    provider_full: ScrapingProvider,
    mock_scraper: MagicMock,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """レース結果で取得できないカラムは NaN."""
    mock_scraper.get_race_info.return_value = create_scraping_race_info()
    mock_result_scraper.get_result.return_value = create_scraping_result()

    result = provider_full.get_result(race_code)

    _assert_all_nan(result, RACE_INFO_BY_HORSE_COLUMNS_UNAVAILABLE_IN_SCRAPING)


def test_past_performances(provider_full: ScrapingProvider, mock_past_scraper: MagicMock) -> None:
    """過去戦績で取得できないカラムは NaN."""
    mock_past_scraper.get_past_performances.return_value = create_scraping_past_performances()

    result = provider_full.get_past_performances("2021105001")

    _assert_all_nan(result, RACE_INFO_BY_HORSE_COLUMNS_UNAVAILABLE_IN_SCRAPING)
