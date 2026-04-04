"""get_past_performances用の変換関数.

UMAGOTO_RACE_JOHOテーブルの馬ID指定出力を統一スキーマに変換する。
走破タイム・タイム差・コーナー順位の変換はget_resultと共通だが、
単勝人気順の再計算は適用しない（馬単位のデータで同レースの全馬情報がないため）。
"""

import pandas as pd

from keiba_data_interface.providers.mykeibadb_converters.convert_entry import convert_base
from keiba_data_interface.providers.mykeibadb_converters.convert_result import convert_result_common


def convert_past_performances(raw: pd.DataFrame) -> pd.DataFrame:
    """馬ID指定のUMAGOTO_RACE_JOHO出力を統一スキーマに変換する.

    走破タイム・タイム差・コーナー順位の変換を適用するが、
    単勝人気順の再計算は適用しない。新馬の場合は0行のDataFrameを返す。

    Args:
        raw (pd.DataFrame): RaceGetter.get_umagoto_race_joho()の出力（convert_codes=True）

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame（HORSE_RACE_INFO_COLUMNSのカラム）
    """
    return convert_result_common(convert_base(raw))
