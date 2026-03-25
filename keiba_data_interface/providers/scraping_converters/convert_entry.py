"""get_entry用の変換関数."""

import pandas as pd

from keiba_data_interface.providers.scraping_converters.common import (
    IJO_KUBUN_MAP,
    set_header_columns,
    set_zogen,
)
from keiba_data_interface.schema.columns import HORSE_RACE_INFO_COLUMNS
from keiba_data_interface.schema.types import HORSE_RACE_INFO_TYPES
from keiba_data_interface.utils.dataframe import apply_types, ensure_columns
from keiba_data_interface.utils.race_code import extract_race_code_parts


def convert_entry(raw: pd.DataFrame, race_code: str) -> pd.DataFrame:
    """get_entry用: scraping出力を統一スキーマに変換する.

    Args:
        raw (pd.DataFrame): EntryPageScraper.get_entry()の出力
        race_code (str): 16桁レースコード

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame（HORSE_RACE_INFO_COLUMNSのカラム）
    """
    parts = extract_race_code_parts(race_code)
    rows: list[dict[str, object]] = []

    for _, row in raw.iterrows():
        converted: dict[str, object] = {}
        set_header_columns(converted, race_code, parts)
        converted["枠番"] = row["枠"]
        converted["馬番"] = row["馬番"]
        converted["血統登録番号"] = row["馬ID"]
        converted["馬名"] = row["馬名"]
        converted["性別"] = row["性別"]
        converted["馬齢"] = row["年齢"]
        converted["負担重量"] = row["斤量"]
        converted["騎手名略称"] = row["騎手"]
        converted["騎手コード"] = row["騎手ID"]
        converted["所属"] = row["所属"]
        converted["調教師名略称"] = row["厩舎"]
        converted["調教師コード"] = row["厩舎ID"]
        converted["馬体重"] = row["馬体重"]

        # 増減 → 増減符号 + 増減差
        set_zogen(converted, row["増減"])

        # 出走区分 → 異常区分
        shutsuso_kubun = row["出走区分"]
        if pd.notna(shutsuso_kubun):
            converted["異常区分"] = IJO_KUBUN_MAP.get(str(shutsuso_kubun), str(shutsuso_kubun))

        rows.append(converted)

    result = pd.DataFrame(rows)
    result = ensure_columns(result, HORSE_RACE_INFO_COLUMNS)
    result = apply_types(result, HORSE_RACE_INFO_TYPES)
    return result
