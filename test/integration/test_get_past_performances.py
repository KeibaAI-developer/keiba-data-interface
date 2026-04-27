"""get_past_performances: 両Providerの出力一致テスト."""

from unittest.mock import MagicMock, patch

from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.providers.scraping_provider import ScrapingProvider
from keiba_data_interface.schema.columns import HORSE_RACE_INFO_COLUMNS

from .assertion_helpers import (
    assert_columns_match,
    assert_common_values_match,
    assert_scraping_nan_columns,
    get_scraping_only_columns,
)
from .column_definitions import (
    HORSE_RACE_INFO_SCRAPING_COLUMNS,
    KNOWN_DIFF_HORSE_RACE,
    PAST_PERF_ADDITIONAL_SCRAPING_COLUMNS,
    PAST_PERF_EXCLUDE,
)
from .conftest import HorseFixtures


# 正常系
def test_get_past_performances_columns_match(
    horse_fixtures: HorseFixtures,
) -> None:
    """get_past_performances: 両Providerの出力DataFrameが同一カラム構成を持つ."""
    # Scraping
    mock_past_scraper = MagicMock()
    mock_past_scraper.get_past_performances.return_value = horse_fixtures.scraping[
        "past_performances"
    ]
    horse_basic_info = horse_fixtures.scraping["horse_basic_info"]
    mock_past_scraper.get_horse_basic_info.return_value = horse_basic_info

    with patch(
        "keiba_data_interface.providers.scraping_provider.HorsePageScraper",
        return_value=mock_past_scraper,
    ):
        s_provider = ScrapingProvider()
        s_df = s_provider.get_past_performances(horse_fixtures.horse_id)

    # MykeibaDB
    mock_race_getter = MagicMock()
    mock_race_getter.get_umagoto_race_joho.return_value = horse_fixtures.mykeibadb[
        "umagoto_race_joho"
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
    ):
        m_provider = MykeibaDBProvider()
        m_df = m_provider.get_past_performances(horse_fixtures.horse_id)

    assert_columns_match(s_df, m_df, HORSE_RACE_INFO_COLUMNS, "過去成績")


def test_get_past_performances_common_values_match(
    horse_fixtures: HorseFixtures,
) -> None:
    """get_past_performances: 共通カラムの型と値が一致する."""
    mock_past_scraper = MagicMock()
    mock_past_scraper.get_past_performances.return_value = horse_fixtures.scraping[
        "past_performances"
    ]
    horse_basic_info = horse_fixtures.scraping["horse_basic_info"]
    mock_past_scraper.get_horse_basic_info.return_value = horse_basic_info

    with patch(
        "keiba_data_interface.providers.scraping_provider.HorsePageScraper",
        return_value=mock_past_scraper,
    ):
        s_provider = ScrapingProvider()
        s_df = s_provider.get_past_performances(horse_fixtures.horse_id)

    mock_race_getter = MagicMock()
    mock_race_getter.get_umagoto_race_joho.return_value = horse_fixtures.mykeibadb[
        "umagoto_race_joho"
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
    ):
        m_provider = MykeibaDBProvider()
        m_df = m_provider.get_past_performances(horse_fixtures.horse_id)

    past_perf_scraping_columns = [
        c for c in HORSE_RACE_INFO_SCRAPING_COLUMNS if c not in PAST_PERF_EXCLUDE
    ] + PAST_PERF_ADDITIONAL_SCRAPING_COLUMNS

    assert_common_values_match(
        s_df,
        m_df,
        past_perf_scraping_columns,
        "過去成績",
        sort_by="レースコード",
        exclude_columns=KNOWN_DIFF_HORSE_RACE,
    )


def test_get_past_performances_scraping_nan_columns(
    horse_fixtures: HorseFixtures,
) -> None:
    """get_past_performances: scraping×のカラムがNaNである."""
    mock_past_scraper = MagicMock()
    mock_past_scraper.get_past_performances.return_value = horse_fixtures.scraping[
        "past_performances"
    ]
    horse_basic_info = horse_fixtures.scraping["horse_basic_info"]
    mock_past_scraper.get_horse_basic_info.return_value = horse_basic_info

    with patch(
        "keiba_data_interface.providers.scraping_provider.HorsePageScraper",
        return_value=mock_past_scraper,
    ):
        s_provider = ScrapingProvider()
        s_df = s_provider.get_past_performances(horse_fixtures.horse_id)

    nan_cols = get_scraping_only_columns(
        HORSE_RACE_INFO_COLUMNS,
        HORSE_RACE_INFO_SCRAPING_COLUMNS + PAST_PERF_ADDITIONAL_SCRAPING_COLUMNS,
    )
    assert_scraping_nan_columns(s_df, nan_cols, "過去成績")
