"""get_chakudosu: 両Providerの出力一致テスト."""

import pandas as pd

from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.providers.scraping_provider import ScrapingProvider
from keiba_data_interface.schema.columns import CHAKUDOSU_COLUMNS

from .assertion_helpers import assert_columns_match, assert_common_values_match
from .column_definitions import KNOWN_DIFF_CHAKUDOSU
from .conftest import RaceFixtures

# 競走中止（着順NaN）の過去走をmykeibadbは着外、scrapingは集計対象外として扱う既知差分の対象セル
# レースコード→血統登録番号→差分が発生するカラム
CHUSHI_KNOWN_DIFF_CELLS: dict[str, dict[str, set[str]]] = {
    "2025080304020407": {  # アイビスSD2025
        "2020104429": {"新潟ダ着外", "ダ1200以下着外", "ダ左着外", "ダ稍着外"},
    },
    "2023112605050812": {  # ジャパンC2023
        "2018103559": {"京都芝着外", "芝2801以上着外", "芝右着外", "芝稍着外"},
    },
    "2023043008010411": {  # 天皇賞(春)2023
        "2015102735": {"阪神芝着外", "芝1801-2000着外", "芝右着外", "芝良着外"},
        "2016104946": {"阪神芝着外", "芝2801以上着外", "芝右着外", "芝稍着外"},
    },
}

# KNOWN_DIFF_CHAKUDOSU（障害馬場状態カラム）の差分が実際に発生するレース
# 中山大障害2024は障害レース自体、アイビスSD2025は過去に障害を走った馬を含む
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
    m_df = _apply_chushi_known_diff_overrides(s_df, m_df, rc)

    exclude_columns = KNOWN_DIFF_CHAKUDOSU if rc in SHOGAI_BABA_KNOWN_DIFF_RACE_CODES else set()

    assert_common_values_match(
        s_df,
        m_df,
        CHAKUDOSU_COLUMNS,
        "出走別着度数",
        sort_by="血統登録番号",
        exclude_columns=exclude_columns,
    )


def _apply_chushi_known_diff_overrides(
    s_df: pd.DataFrame, m_df: pd.DataFrame, race_code: str
) -> pd.DataFrame:
    """競走中止馬の既知差分セルをscraping側の値で上書きする.

    過去走の競走中止を着外として数えるか否かのmykeibadb/scraping間の既知差分を、
    対象馬・対象カラムのセル単位で値比較から除外する。

    Args:
        s_df (pd.DataFrame): ScrapingProvider出力
        m_df (pd.DataFrame): MykeibaDBProvider出力
        race_code (str): 16桁レースコード

    Returns:
        pd.DataFrame: 既知差分セルをscraping側の値で上書きしたMykeibaDBProvider出力
    """
    m_df = m_df.copy()
    for horse_id, columns in CHUSHI_KNOWN_DIFF_CELLS.get(race_code, {}).items():
        s_mask = s_df["血統登録番号"] == horse_id
        m_mask = m_df["血統登録番号"] == horse_id
        for col in columns:
            m_df.loc[m_mask, col] = s_df.loc[s_mask, col].iloc[0]
    return m_df
