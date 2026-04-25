"""get_entry: 両Providerの出力一致テスト."""

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
    ENTRY_ONLY_EXCLUDE,
    HORSE_RACE_INFO_SCRAPING_COLUMNS,
    KNOWN_DIFF_HORSE_RACE,
)
from .conftest import RaceFixtures


# 正常系
def test_get_entry_columns_match(
    scraping_provider_with_mocks: tuple[ScrapingProvider, RaceFixtures],
    mykeibadb_provider_with_mocks: tuple[MykeibaDBProvider, RaceFixtures],
) -> None:
    """get_entry: 両Providerの出力DataFrameが同一カラム構成を持つ."""
    s_provider, fixtures = scraping_provider_with_mocks
    m_provider, _ = mykeibadb_provider_with_mocks
    rc = fixtures.race_code

    s_df = s_provider.get_entry(rc)
    m_df = m_provider.get_entry(rc)

    assert_columns_match(s_df, m_df, HORSE_RACE_INFO_COLUMNS, "出馬表")


def test_get_entry_common_values_match(
    scraping_provider_with_mocks: tuple[ScrapingProvider, RaceFixtures],
    mykeibadb_provider_with_mocks: tuple[MykeibaDBProvider, RaceFixtures],
) -> None:
    """get_entry: 共通カラムの型と値が一致する."""
    s_provider, fixtures = scraping_provider_with_mocks
    m_provider, _ = mykeibadb_provider_with_mocks
    rc = fixtures.race_code

    s_df = s_provider.get_entry(rc)
    m_df = m_provider.get_entry(rc)

    assert_common_values_match(
        s_df,
        m_df,
        HORSE_RACE_INFO_SCRAPING_COLUMNS,
        "出馬表",
        sort_by="馬番",
        exclude_columns=KNOWN_DIFF_HORSE_RACE | ENTRY_ONLY_EXCLUDE,
    )


def test_get_entry_scraping_nan_columns(
    scraping_provider_with_mocks: tuple[ScrapingProvider, RaceFixtures],
) -> None:
    """get_entry: scraping×のカラムがNaNである."""
    s_provider, fixtures = scraping_provider_with_mocks
    rc = fixtures.race_code

    s_df = s_provider.get_entry(rc)
    nan_cols = get_scraping_only_columns(HORSE_RACE_INFO_COLUMNS, HORSE_RACE_INFO_SCRAPING_COLUMNS)
    assert_scraping_nan_columns(s_df, nan_cols, "出馬表")
