"""get_result用の変換関数.

UMAGOTO_RACE_JOHOテーブルの結果データを統一スキーマに変換する。
共通変換のあと、走破タイムの"MSSS"→"M:SS.S"変換を行う。
"""

from typing import Any

import pandas as pd

from keiba_data_interface.providers.mykeibadb_converters.convert_entry import convert_base
from keiba_data_interface.utils.converters import convert_time_msss_to_display


def convert_result(raw: pd.DataFrame) -> pd.DataFrame:
    """UMAGOTO_RACE_JOHOの結果データを統一スキーマに変換する.

    共通変換のあと、走破タイムを"MSSS"→"M:SS.S"形式に変換する。

    Args:
        raw (pd.DataFrame): RaceGetter.get_umagoto_race_joho()の出力（convert_codes=True）

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame
    """
    df = convert_base(raw)

    if "走破タイム" in df.columns:
        df["走破タイム"] = df["走破タイム"].apply(_convert_soha_time)

    if "タイム差" in df.columns:
        df["タイム差"] = df["タイム差"].apply(_convert_time_sa)

    # コーナー順位の0→NaN変換（競走中止等でコーナー通過がない場合）
    for i in range(1, 5):
        col = f"{i}コーナー順位"
        if col in df.columns:
            df[col] = (
                df[col]
                .apply(lambda v: pd.NA if not pd.isna(v) and int(v) == 0 else v)
                .astype("Int64")
            )

    return df


def _convert_soha_time(value: Any) -> Any:
    """走破タイムをMSSS形式からM:SS.S形式に変換する."""
    if pd.isna(value):
        return value
    str_val = str(value).strip()
    if str_val and str_val.isdigit() and int(str_val) > 0:
        return convert_time_msss_to_display(str_val)
    return value


def _convert_time_sa(value: Any) -> Any:
    """タイム差を1/10秒単位の整数から秒単位に変換する."""
    if pd.isna(value):
        return value
    try:
        int_val = int(value)
    except (ValueError, TypeError):
        return value
    return round(int_val / 10, 1)
