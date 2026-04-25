"""get_schedule用の変換関数."""

from datetime import date

import pandas as pd

from keiba_data_interface.exceptions import RaceCodeError
from keiba_data_interface.schema.columns import SCHEDULE_COLUMNS
from keiba_data_interface.schema.types import SCHEDULE_TYPES
from keiba_data_interface.utils.dataframe import apply_types, ensure_columns
from keiba_data_interface.utils.race_code import keibajo_name_to_code


def convert_schedule(raw: pd.DataFrame) -> pd.DataFrame:
    """get_schedule用: レース単位の出力を開催場単位に集約して統一スキーマに変換する.

    Args:
        raw (pd.DataFrame): RaceScheduleScraper.get_race_schedule()の出力

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame（SCHEDULE_COLUMNSのカラム）
    """
    # レースIDから開催コード的な情報を導出するため、
    # グループキーとして競馬場・日付・回・開催日を使用
    seen: dict[str, dict[str, object]] = {}

    for _, row in raw.iterrows():
        race_id = str(row["レースID"])
        # レースID: 年(4)+競馬場(2)+回(2)+日目(2)+R(2)
        if len(race_id) == 12:
            year = race_id[0:4]
            keibajo_code = race_id[4:6]
            kai = race_id[6:8]
            nichime = race_id[8:10]
            kaisai_key = f"{year}{keibajo_code}{kai}{nichime}"
        else:
            continue

        if kaisai_key in seen:
            continue

        converted: dict[str, object] = {}

        # 日付 → 開催年 + 開催月日
        dt = row["日付"]
        if isinstance(dt, date):
            monthday = f"{dt.month:02d}{dt.day:02d}"
            converted["開催コード"] = f"{year}{monthday}{keibajo_code}{kai}{nichime}"
            converted["開催年"] = year
            converted["開催月日"] = monthday

        keibajo_name = str(row.get("競馬場")) if pd.notna(row.get("競馬場")) else ""
        try:
            converted["競馬場コード"] = keibajo_name_to_code(keibajo_name)
        except RaceCodeError:
            pass
        if pd.notna(row.get("回")):
            converted["開催回"] = row["回"]
        if pd.notna(row.get("開催日")):
            converted["開催日目"] = row["開催日"]

        seen[kaisai_key] = converted

    if not seen:
        return apply_types(
            ensure_columns(pd.DataFrame(), SCHEDULE_COLUMNS),
            SCHEDULE_TYPES,
        )

    result = pd.DataFrame(list(seen.values()))
    result = ensure_columns(result, SCHEDULE_COLUMNS)
    result = apply_types(result, SCHEDULE_TYPES)
    return result
