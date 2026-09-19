"""get_expected_win_show_odds用の変換関数."""

import pandas as pd

from keiba_data_interface.schema.columns import WIN_SHOW_ODDS_COLUMNS
from keiba_data_interface.schema.types import ODDS_TYPES
from keiba_data_interface.utils.dataframe import apply_types, ensure_columns
from keiba_data_interface.utils.race_code import extract_race_code_parts


def convert_expected_odds(raw: pd.DataFrame, race_code: str) -> pd.DataFrame:
    """get_expected_win_show_odds用: netkeibaの予想オッズを単複オッズのスキーマに変換する.

    予想単勝オッズを `単勝オッズ` に入れ、`単勝人気` は予想単勝オッズの昇順の順位にする
    （オッズがNaNの馬はNaN）。複勝のカラムは予想オッズに無いためNaN。

    Args:
        raw (pd.DataFrame): scrape_yoso_odds_from_netkeiba()の出力（馬番がすべて埋まっていること）
        race_code (str): 16桁レースコード

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame（WIN_SHOW_ODDS_COLUMNSのカラム、馬番順）
    """
    parts = extract_race_code_parts(race_code)
    odds = pd.to_numeric(raw["予想単勝オッズ"], errors="coerce")
    ninki = odds.rank(method="min")
    result = pd.DataFrame(
        {
            "レースコード": race_code,
            "開催年": parts["年"],
            "開催月日": parts["月日"],
            "競馬場コード": parts["競馬場コード"],
            "開催回": int(parts["回"]),
            "開催日目": int(parts["日目"]),
            "レース番号": int(parts["R"]),
            "馬番": raw["馬番"].astype(int).to_numpy(),
            "単勝オッズ": odds.to_numpy(),
            "単勝人気": ninki.to_numpy(),
        }
    )
    result = ensure_columns(result, WIN_SHOW_ODDS_COLUMNS)
    result = apply_types(result, ODDS_TYPES)
    return result.sort_values("馬番").reset_index(drop=True)
