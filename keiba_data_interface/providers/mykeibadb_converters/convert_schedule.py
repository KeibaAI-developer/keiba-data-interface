"""get_schedule用の変換関数.

KAISAI_SCHEDULEテーブルの出力を統一スキーマに変換する。
"""

import pandas as pd

from keiba_data_interface.schema.columns import SCHEDULE_COLUMNS
from keiba_data_interface.schema.types import SCHEDULE_TYPES
from keiba_data_interface.utils.dataframe import apply_types, ensure_columns

# KAISAI_SCHEDULE → 開催スケジュール情報の基本カラムリネームマッピング
_BASE_SCHEDULE_RENAME: dict[str, str] = {
    "kaisai_code": "開催コード",
    "kaisai_nen": "開催年",
    "kaisai_gappi": "開催月日",
    "keibajo_code": "競馬場コード",
    "kaisai_kaiji": "開催回",
    "kaisai_nichiji": "開催日目",
    "yobi_code": "曜日コード",
}


def _build_schedule_rename() -> dict[str, str]:
    """開催スケジュールの完全なリネームマッピングを構築する."""
    rename = dict(_BASE_SCHEDULE_RENAME)

    for i in range(1, 4):
        rename[f"jusho{i}_tokubetsu_kyoso_bango"] = f"重賞{i}特別競走番号"
        rename[f"jusho{i}_kyosomei_hondai"] = f"重賞{i}競走名本題"
        rename[f"jusho{i}_kyosomei_ryakusho_10"] = f"重賞{i}競走名略称10文字"
        rename[f"jusho{i}_kyosomei_ryakusho_6"] = f"重賞{i}競走名略称6文字"
        rename[f"jusho{i}_kyosomei_ryakusho_3"] = f"重賞{i}競走名略称3文字"
        rename[f"jusho{i}_jusho_kaiji"] = f"重賞{i}重賞回次"
        rename[f"jusho{i}_grade_code"] = f"重賞{i}グレードコード"
        rename[f"jusho{i}_kyoso_shubetsu_code"] = f"重賞{i}競走種別コード"
        rename[f"jusho{i}_kyoso_kigo_code"] = f"重賞{i}競走記号コード"
        rename[f"jusho{i}_juryo_shubetsu_code"] = f"重賞{i}重量種別コード"
        rename[f"jusho{i}_kyori"] = f"重賞{i}距離"
        rename[f"jusho{i}_track_code"] = f"重賞{i}トラックコード"

    return rename


_SCHEDULE_RENAME: dict[str, str] = _build_schedule_rename()


def convert_schedule(raw: pd.DataFrame) -> pd.DataFrame:
    """KAISAI_SCHEDULEの出力を統一スキーマに変換する.

    Args:
        raw (pd.DataFrame): RaceGetter.get_kaisai_schedule()の出力（convert_codes=False）

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame（SCHEDULE_COLUMNSのカラム）
    """
    if len(raw) == 0:
        return apply_types(
            ensure_columns(pd.DataFrame(), SCHEDULE_COLUMNS),
            SCHEDULE_TYPES,
        )

    df = raw.rename(columns=_SCHEDULE_RENAME)
    df = ensure_columns(df, SCHEDULE_COLUMNS)
    df = apply_types(df, SCHEDULE_TYPES)
    return df
