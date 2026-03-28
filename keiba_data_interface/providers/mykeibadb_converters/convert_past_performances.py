"""get_past_performances用の変換関数.

UMAGOTO_RACE_JOHOテーブルの馬ID指定出力を統一スキーマに変換する。
get_resultと同じ変換を適用する。
"""

import pandas as pd

from keiba_data_interface.providers.mykeibadb_converters.convert_result import convert_result


def convert_past_performances(raw: pd.DataFrame) -> pd.DataFrame:
    """UMAGOTO_RACE_JOHOの馬ID指定出力を統一スキーマに変換する.

    get_resultと同じ変換を適用する。新馬の場合は0行のDataFrameを返す。

    Args:
        raw (pd.DataFrame): RaceGetter.get_umagoto_race_joho()の出力（convert_codes=True）

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame（HORSE_RACE_INFO_COLUMNSのカラム）
    """
    return convert_result(raw)
