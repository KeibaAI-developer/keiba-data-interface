"""get_schedule: 両Providerの出力一致テスト."""

from unittest.mock import MagicMock, patch

from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.providers.scraping_provider import ScrapingProvider
from keiba_data_interface.schema.columns import SCHEDULE_COLUMNS

from .assertion_helpers import (
    assert_columns_match,
    assert_common_values_match,
    assert_scraping_nan_columns,
    get_scraping_only_columns,
)
from .column_definitions import SCHEDULE_SCRAPING_COLUMNS
from .conftest import ScheduleFixtures


# 正常系
def test_get_schedule_columns_match(
    schedule_fixtures: ScheduleFixtures,
) -> None:
    """get_schedule: 両Providerの出力DataFrameが同一カラム構成を持つ."""
    target_date = schedule_fixtures.target_date

    # Scraping
    mock_schedule_scraper = MagicMock()
    mock_schedule_scraper.get_race_schedule.return_value = schedule_fixtures.scraping["schedule"]

    with patch(
        "keiba_data_interface.providers.scraping_provider.RaceScheduleScraper",
        return_value=mock_schedule_scraper,
    ):
        s_provider = ScrapingProvider()
        s_df = s_provider.get_schedule(target_date, target_date)

    # MykeibaDB
    mock_race_getter = MagicMock()
    mock_race_getter.get_kaisai_schedule.return_value = schedule_fixtures.mykeibadb[
        "kaisai_schedule"
    ]

    with (
        patch(
            "keiba_data_interface.providers.mykeibadb_provider.RaceGetter",
            return_value=mock_race_getter,
        ),
        patch(
            "keiba_data_interface.providers.mykeibadb_provider.OddsGetter",
            return_value=MagicMock(),
        ),
        patch(
            "keiba_data_interface.providers.mykeibadb_provider.MasterGetter",
        ),
    ):
        m_provider = MykeibaDBProvider()
        m_df = m_provider.get_schedule(target_date, target_date)

    assert_columns_match(s_df, m_df, SCHEDULE_COLUMNS, "開催スケジュール")


def test_get_schedule_common_values_match(
    schedule_fixtures: ScheduleFixtures,
) -> None:
    """get_schedule: 共通カラムの型と値が一致する."""
    target_date = schedule_fixtures.target_date

    # Scraping
    mock_schedule_scraper = MagicMock()
    mock_schedule_scraper.get_race_schedule.return_value = schedule_fixtures.scraping["schedule"]

    with patch(
        "keiba_data_interface.providers.scraping_provider.RaceScheduleScraper",
        return_value=mock_schedule_scraper,
    ):
        s_provider = ScrapingProvider()
        s_df = s_provider.get_schedule(target_date, target_date)

    # MykeibaDB
    mock_race_getter = MagicMock()
    mock_race_getter.get_kaisai_schedule.return_value = schedule_fixtures.mykeibadb[
        "kaisai_schedule"
    ]

    with (
        patch(
            "keiba_data_interface.providers.mykeibadb_provider.RaceGetter",
            return_value=mock_race_getter,
        ),
        patch(
            "keiba_data_interface.providers.mykeibadb_provider.OddsGetter",
            return_value=MagicMock(),
        ),
        patch(
            "keiba_data_interface.providers.mykeibadb_provider.MasterGetter",
        ),
    ):
        m_provider = MykeibaDBProvider()
        m_df = m_provider.get_schedule(target_date, target_date)

    assert_common_values_match(
        s_df, m_df, SCHEDULE_SCRAPING_COLUMNS, "開催スケジュール", sort_by="開催コード"
    )


def test_get_schedule_scraping_nan_columns(
    schedule_fixtures: ScheduleFixtures,
) -> None:
    """get_schedule: scraping×のカラムがNaNである."""
    target_date = schedule_fixtures.target_date

    mock_schedule_scraper = MagicMock()
    mock_schedule_scraper.get_race_schedule.return_value = schedule_fixtures.scraping["schedule"]

    with patch(
        "keiba_data_interface.providers.scraping_provider.RaceScheduleScraper",
        return_value=mock_schedule_scraper,
    ):
        s_provider = ScrapingProvider()
        s_df = s_provider.get_schedule(target_date, target_date)

    nan_cols = get_scraping_only_columns(SCHEDULE_COLUMNS, SCHEDULE_SCRAPING_COLUMNS)
    assert_scraping_nan_columns(s_df, nan_cols, "開催スケジュール")
