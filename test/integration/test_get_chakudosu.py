"""get_chakudosu: 両Providerの出力一致テスト."""

from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.providers.scraping_provider import ScrapingProvider
from keiba_data_interface.schema.columns import CHAKUDOSU_COLUMNS

from .assertion_helpers import assert_columns_match, assert_common_values_match
from .column_definitions import KNOWN_DIFF_CHAKUDOSU
from .conftest import RaceFixtures

# KNOWN_DIFF_CHAKUDOSU（障害馬場状態カラム）の差分が実際に発生するレース
# 中山大障害2024は障害レース自体が対象、アイビスSD2025（障害レースではない）は
# 出走馬が過去に障害レースを走った際の馬場状態の扱いがプロバイダー間で異なる
SHOGAI_BABA_KNOWN_DIFF_RACE_CODES: set[str] = {"2024122106050710", "2025080304020407"}


# 正常系
def test_get_chakudosu_columns_match(
    chakudosu_scraping_provider_with_mocks: tuple[ScrapingProvider, RaceFixtures],
    chakudosu_mykeibadb_provider_with_mocks: tuple[MykeibaDBProvider, RaceFixtures],
) -> None:
    """get_chakudosu: 両Providerの出力DataFrameが同一カラム構成を持つ."""
    s_provider, fixtures = chakudosu_scraping_provider_with_mocks
    m_provider, _ = chakudosu_mykeibadb_provider_with_mocks
    rc = fixtures.race_code

    s_df = s_provider.get_chakudosu(rc)
    m_df = m_provider.get_chakudosu(rc)

    assert_columns_match(s_df, m_df, CHAKUDOSU_COLUMNS, "出走別着度数")


def test_get_chakudosu_values_match(
    chakudosu_scraping_provider_with_mocks: tuple[ScrapingProvider, RaceFixtures],
    chakudosu_mykeibadb_provider_with_mocks: tuple[MykeibaDBProvider, RaceFixtures],
) -> None:
    """get_chakudosu: 血統登録番号昇順ソート後、全カラムの型と値が一致する."""
    s_provider, fixtures = chakudosu_scraping_provider_with_mocks
    m_provider, _ = chakudosu_mykeibadb_provider_with_mocks
    rc = fixtures.race_code

    s_df = s_provider.get_chakudosu(rc)
    m_df = m_provider.get_chakudosu(rc)

    exclude_columns = KNOWN_DIFF_CHAKUDOSU if rc in SHOGAI_BABA_KNOWN_DIFF_RACE_CODES else set()

    assert_common_values_match(
        s_df,
        m_df,
        CHAKUDOSU_COLUMNS,
        "出走別着度数",
        sort_by="血統登録番号",
        exclude_columns=exclude_columns,
    )
