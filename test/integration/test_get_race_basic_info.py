"""get_race_basic_info: 両Providerの出力一致テスト."""

from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.providers.scraping_provider import ScrapingProvider
from keiba_data_interface.schema.columns import RACE_INFO_COLUMNS

from .assertion_helpers import (
    assert_columns_match,
    assert_common_values_match,
    assert_scraping_nan_columns,
    get_scraping_only_columns,
)
from .column_definitions import KNOWN_DIFF_RACE_INFO, RACE_INFO_SCRAPING_COLUMNS
from .conftest import RaceFixtures


# 正常系
def test_get_race_basic_info_columns_match(
    scraping_provider_with_mocks: tuple[ScrapingProvider, RaceFixtures],
    mykeibadb_provider_with_mocks: tuple[MykeibaDBProvider, RaceFixtures],
) -> None:
    """get_race_basic_info: 両Providerの出力DataFrameが同一カラム構成を持つ."""
    s_provider, fixtures = scraping_provider_with_mocks
    m_provider, _ = mykeibadb_provider_with_mocks
    rc = fixtures.race_code

    s_df = s_provider.get_race_basic_info(rc)
    m_df = m_provider.get_race_basic_info(rc)

    assert_columns_match(s_df, m_df, RACE_INFO_COLUMNS, "レース基本情報")


def test_get_race_basic_info_common_values_match(
    scraping_provider_with_mocks: tuple[ScrapingProvider, RaceFixtures],
    mykeibadb_provider_with_mocks: tuple[MykeibaDBProvider, RaceFixtures],
) -> None:
    """get_race_basic_info: 共通カラムの型と値が一致する."""
    s_provider, fixtures = scraping_provider_with_mocks
    m_provider, _ = mykeibadb_provider_with_mocks
    rc = fixtures.race_code

    s_df = s_provider.get_race_basic_info(rc)
    m_df = m_provider.get_race_basic_info(rc)

    assert_common_values_match(
        s_df,
        m_df,
        RACE_INFO_SCRAPING_COLUMNS,
        "レース基本情報",
        exclude_columns=KNOWN_DIFF_RACE_INFO,
    )


def test_get_race_basic_info_scraping_nan_columns(
    scraping_provider_with_mocks: tuple[ScrapingProvider, RaceFixtures],
) -> None:
    """get_race_basic_info: scraping×のカラムがNaNである."""
    s_provider, fixtures = scraping_provider_with_mocks
    rc = fixtures.race_code

    s_df = s_provider.get_race_basic_info(rc)
    nan_cols = get_scraping_only_columns(RACE_INFO_COLUMNS, RACE_INFO_SCRAPING_COLUMNS)
    assert_scraping_nan_columns(s_df, nan_cols, "レース基本情報")
