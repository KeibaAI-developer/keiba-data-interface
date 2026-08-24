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
        raw (pd.DataFrame): RaceGetter.get_umagoto_race_joho()の出力（convert_codes=False）

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame（HORSE_RACE_INFO_COLUMNSのカラム）
    """
    return convert_result_common(convert_base(raw))


def convert_past_performances_bulk(raw: pd.DataFrame) -> pd.DataFrame:
    """馬ID指定のUMAGOTO_RACE_JOHO出力（複数馬分）を統一スキーマに変換する.

    変換は要素単位・カラム単位の処理だけで構成されており、馬をまたいで影響し合う
    処理が無い（単勝人気順の再計算は行わない）。そのため複数馬分をまとめて渡しても
    馬ごとに変換した結果と一致する。

    分割は呼び出し側が行う。`血統登録番号` カラムはそのまま保持する。

    Args:
        raw (pd.DataFrame): RaceGetter.get_umagoto_race_joho()の出力（複数馬分）

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame（複数馬分）
    """
    return convert_past_performances(raw)
