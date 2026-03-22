"""ScrapingProvider.get_schedule関数のテスト."""

from unittest.mock import MagicMock

import pandas as pd

from keiba_data_interface.providers.scraping_provider import ScrapingProvider
from keiba_data_interface.schema.columns import SCHEDULE_COLUMNS


# 正常系
def test_output_columns_match_schema(
    provider_full: ScrapingProvider,
    mock_schedule_scraper: MagicMock,
) -> None:
    """出力DataFrameのカラム構成がSCHEDULE_COLUMNSと一致する."""
    from .conftest import _create_scraping_schedule

    mock_schedule_scraper.get_race_schedule.return_value = _create_scraping_schedule()

    result = provider_full.get_schedule("2025-01-05", "2025-01-05")

    assert list(result.columns) == SCHEDULE_COLUMNS


def test_aggregation_to_kaisaijo(
    provider_full: ScrapingProvider,
    mock_schedule_scraper: MagicMock,
) -> None:
    """レース単位から開催場単位に正しく集約される."""
    from .conftest import _create_scraping_schedule

    mock_schedule_scraper.get_race_schedule.return_value = _create_scraping_schedule()

    result = provider_full.get_schedule("2025-01-05", "2025-01-05")

    # 3レース（中山2レース + 京都1レース）→ 2開催場
    assert len(result) == 2


def test_kaisai_code_derived(
    provider_full: ScrapingProvider,
    mock_schedule_scraper: MagicMock,
) -> None:
    """開催コードがレースIDから正しく導出される."""
    from .conftest import _create_scraping_schedule

    mock_schedule_scraper.get_race_schedule.return_value = _create_scraping_schedule()

    result = provider_full.get_schedule("2025-01-05", "2025-01-05")

    codes = set(result["開催コード"].tolist())
    # 中山: レースID=202505010101 → 開催コード=20250105050101
    # 京都: レースID=202506020101 → 開催コード=20250105060201
    assert codes == {"20250105050101", "20250105060201"}


def test_multiple_days(
    provider_full: ScrapingProvider,
    mock_schedule_scraper_cls: MagicMock,
    mock_schedule_scraper: MagicMock,
) -> None:
    """複数日の日付範囲で各日のスクレイパが呼び出される."""
    from .conftest import _create_scraping_schedule

    mock_schedule_scraper.get_race_schedule.return_value = _create_scraping_schedule()

    provider_full.get_schedule("2025-01-05", "2025-01-06")

    # 2日分のスクレイパが作成される
    assert mock_schedule_scraper_cls.call_count == 2
    mock_schedule_scraper_cls.assert_any_call(2025, 1, 5)
    mock_schedule_scraper_cls.assert_any_call(2025, 1, 6)


def test_empty_schedule(
    provider_full: ScrapingProvider,
    mock_schedule_scraper: MagicMock,
) -> None:
    """開催なしの日は空DataFrameが返される."""
    mock_schedule_scraper.get_race_schedule.return_value = pd.DataFrame()

    result = provider_full.get_schedule("2025-01-05", "2025-01-05")

    assert len(result) == 0
    assert list(result.columns) == SCHEDULE_COLUMNS


def test_keibajo_name_stored(
    provider_full: ScrapingProvider,
    mock_schedule_scraper: MagicMock,
) -> None:
    """競馬場名が正しく格納される."""
    from .conftest import _create_scraping_schedule

    mock_schedule_scraper.get_race_schedule.return_value = _create_scraping_schedule()

    result = provider_full.get_schedule("2025-01-05", "2025-01-05")

    keibajo_set = set(result["競馬場"].tolist())
    assert "中山" in keibajo_set
    assert "京都" in keibajo_set


def test_date_to_year_and_monthday(
    provider_full: ScrapingProvider,
    mock_schedule_scraper: MagicMock,
) -> None:
    """日付が開催年と開催月日に正しく分割される."""
    from .conftest import _create_scraping_schedule

    mock_schedule_scraper.get_race_schedule.return_value = _create_scraping_schedule()

    result = provider_full.get_schedule("2025-01-05", "2025-01-05")

    row = result.iloc[0]
    assert row["開催年"] == "2025"
    assert row["開催月日"] == "0105"
