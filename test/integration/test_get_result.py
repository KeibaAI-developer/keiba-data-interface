"""get_result: 両Providerの出力一致テスト."""

from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.providers.scraping_provider import ScrapingProvider
from keiba_data_interface.schema.columns import HORSE_RACE_INFO_COLUMNS

from .assertion_helpers import (
    assert_columns_match,
    assert_common_values_match,
    assert_scraping_nan_columns,
    get_scraping_only_columns,
)
from .column_definitions import HORSE_RACE_INFO_SCRAPING_COLUMNS, KNOWN_DIFF_HORSE_RACE
from .conftest import RaceFixtures


# 正常系
def test_get_result_columns_match(
    scraping_provider_with_mocks: tuple[ScrapingProvider, RaceFixtures],
    mykeibadb_provider_with_mocks: tuple[MykeibaDBProvider, RaceFixtures],
) -> None:
    """get_result: 両Providerの出力DataFrameが同一カラム構成を持つ."""
    s_provider, fixtures = scraping_provider_with_mocks
    m_provider, _ = mykeibadb_provider_with_mocks
    rc = fixtures.race_code

    s_df = s_provider.get_result(rc)
    m_df = m_provider.get_result(rc)

    assert_columns_match(s_df, m_df, HORSE_RACE_INFO_COLUMNS, "レース結果")


def test_get_result_common_values_match(
    scraping_provider_with_mocks: tuple[ScrapingProvider, RaceFixtures],
    mykeibadb_provider_with_mocks: tuple[MykeibaDBProvider, RaceFixtures],
) -> None:
    """get_result: 共通カラムの型と値が一致する."""
    s_provider, fixtures = scraping_provider_with_mocks
    m_provider, _ = mykeibadb_provider_with_mocks
    rc = fixtures.race_code

    s_df = s_provider.get_result(rc)
    m_df = m_provider.get_result(rc)

    assert_common_values_match(
        s_df,
        m_df,
        HORSE_RACE_INFO_SCRAPING_COLUMNS,
        "レース結果",
        sort_by="馬番",
        exclude_columns=KNOWN_DIFF_HORSE_RACE,
    )


def test_get_result_scraping_nan_columns(
    scraping_provider_with_mocks: tuple[ScrapingProvider, RaceFixtures],
) -> None:
    """get_result: scraping×のカラムがNaNである."""
    s_provider, fixtures = scraping_provider_with_mocks
    rc = fixtures.race_code

    s_df = s_provider.get_result(rc)
    nan_cols = get_scraping_only_columns(HORSE_RACE_INFO_COLUMNS, HORSE_RACE_INFO_SCRAPING_COLUMNS)
    assert_scraping_nan_columns(s_df, nan_cols, "レース結果")
