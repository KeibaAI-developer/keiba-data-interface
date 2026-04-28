"""get_horse_master: 両Providerの出力一致テスト."""

from unittest.mock import MagicMock, patch

from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.providers.scraping_provider import ScrapingProvider
from keiba_data_interface.schema.columns import HORSE_MASTER_COLUMNS

from .assertion_helpers import (
    assert_columns_match,
    assert_common_values_match,
    assert_scraping_nan_columns,
    get_scraping_only_columns,
)
from .column_definitions import HORSE_MASTER_SCRAPING_COLUMNS, KNOWN_DIFF_HORSE_MASTER
from .conftest import HorseFixtures


# 正常系
def test_get_horse_master_columns_match(
    horse_fixtures: HorseFixtures,
) -> None:
    """get_horse_master: 両Providerの出力DataFrameが同一カラム構成を持つ."""
    mock_horse_scraper = MagicMock()
    mock_horse_scraper.get_past_performances.return_value = horse_fixtures.scraping[
        "past_performances"
    ]
    horse_basic_info = horse_fixtures.scraping["horse_basic_info"]
    mock_horse_scraper.get_horse_basic_info.return_value = horse_basic_info

    with patch(
        "keiba_data_interface.providers.scraping_provider.HorsePageScraper",
        return_value=mock_horse_scraper,
    ):
        s_provider = ScrapingProvider()
        s_df = s_provider.get_horse_master(horse_fixtures.horse_id)

    mock_master_getter = MagicMock()
    kyosoba_master2 = horse_fixtures.mykeibadb["kyosoba_master2"]
    mock_master_getter.get_kyosoba_master2.return_value = kyosoba_master2

    with (
        patch(
            "keiba_data_interface.providers.mykeibadb_provider.RaceGetter",
            return_value=MagicMock(),
        ),
        patch(
            "keiba_data_interface.providers.mykeibadb_provider.OddsGetter",
            return_value=MagicMock(),
        ),
        patch(
            "keiba_data_interface.providers.mykeibadb_provider.MasterGetter",
            return_value=mock_master_getter,
        ),
    ):
        m_provider = MykeibaDBProvider()
        m_df = m_provider.get_horse_master(horse_fixtures.horse_id)

    assert_columns_match(s_df, m_df, HORSE_MASTER_COLUMNS, "競走馬情報")


def test_get_horse_master_common_values_match(
    horse_fixtures: HorseFixtures,
) -> None:
    """get_horse_master: 共通カラムの型と値が一致する."""
    mock_horse_scraper = MagicMock()
    mock_horse_scraper.get_past_performances.return_value = horse_fixtures.scraping[
        "past_performances"
    ]
    horse_basic_info = horse_fixtures.scraping["horse_basic_info"]
    mock_horse_scraper.get_horse_basic_info.return_value = horse_basic_info

    with patch(
        "keiba_data_interface.providers.scraping_provider.HorsePageScraper",
        return_value=mock_horse_scraper,
    ):
        s_provider = ScrapingProvider()
        s_df = s_provider.get_horse_master(horse_fixtures.horse_id)

    mock_master_getter = MagicMock()
    kyosoba_master2 = horse_fixtures.mykeibadb["kyosoba_master2"]
    mock_master_getter.get_kyosoba_master2.return_value = kyosoba_master2

    with (
        patch(
            "keiba_data_interface.providers.mykeibadb_provider.RaceGetter",
            return_value=MagicMock(),
        ),
        patch(
            "keiba_data_interface.providers.mykeibadb_provider.OddsGetter",
            return_value=MagicMock(),
        ),
        patch(
            "keiba_data_interface.providers.mykeibadb_provider.MasterGetter",
            return_value=mock_master_getter,
        ),
    ):
        m_provider = MykeibaDBProvider()
        m_df = m_provider.get_horse_master(horse_fixtures.horse_id)

    assert_common_values_match(
        s_df,
        m_df,
        HORSE_MASTER_SCRAPING_COLUMNS,
        "競走馬情報",
        exclude_columns=KNOWN_DIFF_HORSE_MASTER,
    )


def test_get_horse_master_scraping_nan_columns(
    horse_fixtures: HorseFixtures,
) -> None:
    """get_horse_master: scraping×のカラムがNaNである."""
    mock_horse_scraper = MagicMock()
    mock_horse_scraper.get_past_performances.return_value = horse_fixtures.scraping[
        "past_performances"
    ]
    horse_basic_info = horse_fixtures.scraping["horse_basic_info"]
    mock_horse_scraper.get_horse_basic_info.return_value = horse_basic_info

    with patch(
        "keiba_data_interface.providers.scraping_provider.HorsePageScraper",
        return_value=mock_horse_scraper,
    ):
        s_provider = ScrapingProvider()
        s_df = s_provider.get_horse_master(horse_fixtures.horse_id)

    nan_cols = get_scraping_only_columns(HORSE_MASTER_COLUMNS, HORSE_MASTER_SCRAPING_COLUMNS)
    assert_scraping_nan_columns(s_df, nan_cols, "競走馬情報")
