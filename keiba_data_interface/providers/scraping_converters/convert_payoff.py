"""get_payoff用の変換関数."""

import pandas as pd
from scraping import ResultPageScraper

from keiba_data_interface.schema.columns import PAYOFF_COLUMNS
from keiba_data_interface.schema.types import PAYOFF_TYPES
from keiba_data_interface.utils.dataframe import apply_types, ensure_columns
from keiba_data_interface.utils.race_code import extract_race_code_parts, keibajo_code_to_name


def convert_payoff(scraper: ResultPageScraper, race_code: str) -> pd.DataFrame:
    """get_payoff用: 8券種の払戻データを1行のDataFrameに結合する.

    Args:
        scraper (ResultPageScraper): 結果ページスクレイパー
        race_code (str): 16桁レースコード

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame（PAYOFF_COLUMNSのカラム）
    """
    parts = extract_race_code_parts(race_code)
    converted: dict[str, object] = {}
    converted["レースコード"] = race_code
    converted["開催年"] = parts["年"]
    converted["開催月日"] = parts["月日"]
    converted["競馬場"] = keibajo_code_to_name(parts["競馬場"])
    converted["開催回"] = int(parts["回"])
    converted["開催日目"] = int(parts["日目"])
    converted["レース番号"] = int(parts["R"])

    def _map_single(
        raw: pd.DataFrame,
        kenshu: str,
        max_n: int,
    ) -> None:
        """単勝・複勝のカラムマッピング.

        Args:
            raw (pd.DataFrame): 払戻データ
            kenshu (str): 券種名（例: "単勝", "複勝"）
            max_n (int): 最大組数
        """
        if len(raw) == 0:
            return
        row = raw.iloc[0]
        for i in range(1, max_n + 1):
            for scraping_suffix, schema_suffix in [
                (f"馬番_{i}", f"{i}馬番"),
                (f"払戻金_{i}", f"{i}払戻金"),
                (f"人気_{i}", f"{i}人気順"),
            ]:
                scraping_col = f"{kenshu}{scraping_suffix}"
                schema_col = f"{kenshu}{schema_suffix}"
                if scraping_col in row.index and pd.notna(row[scraping_col]):
                    converted[schema_col] = row[scraping_col]

    def _map_combination(
        raw: pd.DataFrame,
        kenshu: str,
        max_n: int,
        num_horses: int,
    ) -> None:
        """組み合わせ券種のカラムマッピング.

        Args:
            raw (pd.DataFrame): 払戻データ
            kenshu (str): 券種名（例: "枠連", "馬連"）
            max_n (int): 最大組数
            num_horses (int): 1組あたりの馬数
        """
        if len(raw) == 0:
            return
        row = raw.iloc[0]
        for i in range(1, max_n + 1):
            # 組番
            for j in range(1, num_horses + 1):
                scraping_col = f"{kenshu}組番_{i}_{j}"
                schema_col = f"{kenshu}{i}組番{j}"
                if scraping_col in row.index and pd.notna(row[scraping_col]):
                    converted[schema_col] = row[scraping_col]
            # 払戻金
            scraping_col = f"{kenshu}払戻金_{i}"
            schema_col = f"{kenshu}{i}払戻金"
            if scraping_col in row.index and pd.notna(row[scraping_col]):
                converted[schema_col] = row[scraping_col]
            # 人気順
            scraping_col = f"{kenshu}人気_{i}"
            schema_col = f"{kenshu}{i}人気順"
            if scraping_col in row.index and pd.notna(row[scraping_col]):
                converted[schema_col] = row[scraping_col]

    # 単勝・複勝
    _map_single(scraper.get_win_payoff(), "単勝", 3)
    _map_single(scraper.get_show_payoff(), "複勝", 5)

    # 2頭組み合わせ
    _map_combination(scraper.get_bracket_payoff(), "枠連", 3, 2)
    _map_combination(scraper.get_quinella_payoff(), "馬連", 3, 2)
    _map_combination(scraper.get_quinella_place_payoff(), "ワイド", 7, 2)
    _map_combination(scraper.get_exacta_payoff(), "馬単", 6, 2)

    # 3頭組み合わせ
    _map_combination(scraper.get_trio_payoff(), "3連複", 3, 3)
    _map_combination(scraper.get_trifecta_payoff(), "3連単", 6, 3)

    result = pd.DataFrame([converted])
    result = ensure_columns(result, PAYOFF_COLUMNS)
    result = apply_types(result, PAYOFF_TYPES)
    return result
