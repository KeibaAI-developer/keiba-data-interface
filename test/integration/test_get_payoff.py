"""get_payoff: 両Providerの出力一致テスト."""

from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.providers.scraping_provider import ScrapingProvider
from keiba_data_interface.schema.columns import PAYOFF_COLUMNS

from .assertion_helpers import (
    assert_columns_match,
    assert_common_values_match,
    assert_scraping_nan_columns,
    get_scraping_only_columns,
)
from .column_definitions import KNOWN_DIFF_PAYOFF, PAYOFF_SCRAPING_COLUMNS
from .conftest import RaceFixtures


# 正常系
def test_get_payoff_columns_match(
    scraping_provider_with_mocks: tuple[ScrapingProvider, RaceFixtures],
    mykeibadb_provider_with_mocks: tuple[MykeibaDBProvider, RaceFixtures],
) -> None:
    """get_payoff: 両Providerの出力DataFrameが同一カラム構成を持つ."""
    s_provider, fixtures = scraping_provider_with_mocks
    m_provider, _ = mykeibadb_provider_with_mocks
    rc = fixtures.race_code

    s_df = s_provider.get_payoff(rc)
    m_df = m_provider.get_payoff(rc)

    assert_columns_match(s_df, m_df, PAYOFF_COLUMNS, "払戻情報")


def test_get_payoff_common_values_match(
    scraping_provider_with_mocks: tuple[ScrapingProvider, RaceFixtures],
    mykeibadb_provider_with_mocks: tuple[MykeibaDBProvider, RaceFixtures],
) -> None:
    """get_payoff: 共通カラムの型と値が一致する."""
    s_provider, fixtures = scraping_provider_with_mocks
    m_provider, _ = mykeibadb_provider_with_mocks
    rc = fixtures.race_code

    s_df = s_provider.get_payoff(rc)
    m_df = m_provider.get_payoff(rc)

    assert_common_values_match(
        s_df,
        m_df,
        PAYOFF_SCRAPING_COLUMNS,
        "払戻情報",
        exclude_columns=KNOWN_DIFF_PAYOFF,
    )


def test_get_payoff_scraping_nan_columns(
    scraping_provider_with_mocks: tuple[ScrapingProvider, RaceFixtures],
) -> None:
    """get_payoff: scraping×のカラムがNaNである."""
    s_provider, fixtures = scraping_provider_with_mocks
    rc = fixtures.race_code

    s_df = s_provider.get_payoff(rc)
    nan_cols = get_scraping_only_columns(PAYOFF_COLUMNS, PAYOFF_SCRAPING_COLUMNS)
    assert_scraping_nan_columns(s_df, nan_cols, "払戻情報")
