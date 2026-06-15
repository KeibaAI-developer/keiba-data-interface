"""get_chakudosu: 両Providerの出力一致テスト."""

import pandas as pd

from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.providers.scraping_provider import ScrapingProvider
from keiba_data_interface.schema.columns import CHAKUDOSU_COLUMNS

from .assertion_helpers import assert_columns_match, assert_common_values_match
from .column_definitions import KNOWN_DIFF_CHAKUDOSU
from .conftest import RaceFixtures

# 競走中止（着順NaN）の過去走をmykeibadbは着外、scrapingは集計対象外として扱う既知差分の対象馬
# レースコード→対象馬の血統登録番号一覧
CHUSHI_KNOWN_DIFF_HORSE_IDS: dict[str, set[str]] = {
    "2025080304020407": {"2020104429"},  # アイビスSD2025
    "2023112605050812": {"2018103559"},  # ジャパンC2023
    "2023043008010411": {"2015102735", "2016104946"},  # 天皇賞(春)2023
}


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

    for horse_id in CHUSHI_KNOWN_DIFF_HORSE_IDS.get(rc, set()):
        # 競走中止馬の着回数はmykeibadb/scraping間で既知差分があるため対象馬を除外する
        s_df = _drop_horse(s_df, horse_id)
        m_df = _drop_horse(m_df, horse_id)

    assert_common_values_match(
        s_df,
        m_df,
        CHAKUDOSU_COLUMNS,
        "出走別着度数",
        sort_by="血統登録番号",
        exclude_columns=KNOWN_DIFF_CHAKUDOSU,
    )


def _drop_horse(df: pd.DataFrame, horse_id: str) -> pd.DataFrame:
    """指定した血統登録番号の行を除外する.

    Args:
        df (pd.DataFrame): 出走別着度数DataFrame
        horse_id (str): 除外する血統登録番号

    Returns:
        pd.DataFrame: 対象馬を除外したDataFrame
    """
    return df[df["血統登録番号"] != horse_id].reset_index(drop=True)
