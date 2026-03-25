"""get_win_show_odds用の変換関数."""

import pandas as pd

from keiba_data_interface.schema.columns import ODDS_COLUMNS
from keiba_data_interface.schema.types import ODDS_TYPES
from keiba_data_interface.utils.dataframe import apply_types, ensure_columns
from keiba_data_interface.utils.race_code import extract_race_code_parts, keibajo_code_to_name


def convert_odds(raw: pd.DataFrame, race_code: str) -> pd.DataFrame:
    """get_win_show_odds用: scraping出力を統一スキーマに変換する.

    Args:
        raw (pd.DataFrame): scrape_odds_from_jra()の出力
        race_code (str): 16桁レースコード

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame（ODDS_COLUMNSのカラム）
    """
    parts = extract_race_code_parts(race_code)
    rows: list[dict[str, object]] = []

    for _, row in raw.iterrows():
        converted: dict[str, object] = {}
        converted["レースコード"] = race_code
        converted["開催年"] = parts["年"]
        converted["開催月日"] = parts["月日"]
        converted["競馬場"] = keibajo_code_to_name(parts["競馬場"])
        converted["開催回"] = int(parts["回"])
        converted["開催日目"] = int(parts["日目"])
        converted["レース番号"] = int(parts["R"])
        converted["馬番"] = row["馬番"]

        if pd.notna(row.get("単勝オッズ")):
            converted["単勝オッズ"] = row["単勝オッズ"]
        if pd.notna(row.get("単勝人気")):
            converted["単勝人気"] = row["単勝人気"]
        if pd.notna(row.get("複勝最小オッズ")):
            converted["複勝最低オッズ"] = row["複勝最小オッズ"]
        if pd.notna(row.get("複勝最大オッズ")):
            converted["複勝最高オッズ"] = row["複勝最大オッズ"]
        if pd.notna(row.get("複勝人気")):
            converted["複勝人気"] = row["複勝人気"]

        rows.append(converted)

    result = pd.DataFrame(rows)
    result = ensure_columns(result, ODDS_COLUMNS)
    result = apply_types(result, ODDS_TYPES)
    return result
