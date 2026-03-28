"""get_result用の変換関数.

UMAGOTO_RACE_JOHOテーブルの結果データを統一スキーマに変換する。
get_entry用の変換に加え、走破タイムの"MSSS"→"M:SS.S"変換を行う。
"""

from typing import Any

import pandas as pd

from keiba_data_interface.providers.mykeibadb_converters.convert_entry import convert_entry
from keiba_data_interface.utils.converters import convert_time_msss_to_display


def convert_result(raw: pd.DataFrame) -> pd.DataFrame:
    """UMAGOTO_RACE_JOHOの結果データを統一スキーマに変換する.

    get_entry用の変換を適用した後、走破タイムを"MSSS"→"M:SS.S"形式に変換する。

    Args:
        raw (pd.DataFrame): RaceGetter.get_umagoto_race_joho()の出力（convert_codes=True）

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame
    """
    df = convert_entry(raw)

    if "走破タイム" in df.columns:
        df["走破タイム"] = df["走破タイム"].apply(_convert_soha_time)

    return df


def _convert_soha_time(value: Any) -> Any:
    """走破タイムをMSSS形式からM:SS.S形式に変換する."""
    if pd.isna(value):
        return value
    str_val = str(value).strip()
    if str_val and str_val.isdigit() and int(str_val) > 0:
        return convert_time_msss_to_display(str_val)
    return value
