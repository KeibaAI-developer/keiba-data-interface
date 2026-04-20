"""get_win_show_odds: 両Providerの出力一致テスト."""

from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.providers.scraping_provider import ScrapingProvider
from keiba_data_interface.schema.columns import ODDS_COLUMNS

from .assertion_helpers import assert_columns_match, assert_common_values_match
from .column_definitions import KNOWN_DIFF_ODDS, ODDS_SCRAPING_COLUMNS
from .conftest import RaceFixtures


# 正常系
def test_get_win_show_odds_columns_match(
    scraping_provider_with_mocks: tuple[ScrapingProvider, RaceFixtures],
    mykeibadb_provider_with_mocks: tuple[MykeibaDBProvider, RaceFixtures],
) -> None:
    """get_win_show_odds: 両Providerの出力DataFrameが同一カラム構成を持つ."""
    s_provider, fixtures = scraping_provider_with_mocks
    m_provider, _ = mykeibadb_provider_with_mocks
    rc = fixtures.race_code

    s_df = s_provider.get_win_show_odds(rc)
    m_df = m_provider.get_win_show_odds(rc)

    assert_columns_match(s_df, m_df, ODDS_COLUMNS, "単複オッズ")


def test_get_win_show_odds_common_values_match(
    scraping_provider_with_mocks: tuple[ScrapingProvider, RaceFixtures],
    mykeibadb_provider_with_mocks: tuple[MykeibaDBProvider, RaceFixtures],
) -> None:
    """get_win_show_odds: 共通カラムの型と値が一致する."""
    s_provider, fixtures = scraping_provider_with_mocks
    m_provider, _ = mykeibadb_provider_with_mocks
    rc = fixtures.race_code

    s_df = s_provider.get_win_show_odds(rc)
    m_df = m_provider.get_win_show_odds(rc)

    assert_common_values_match(
        s_df,
        m_df,
        ODDS_SCRAPING_COLUMNS,
        "単複オッズ",
        sort_by="馬番",
        exclude_columns=KNOWN_DIFF_ODDS,
    )
