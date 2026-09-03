"""get_race_schedule用の変換関数.

RACE_SHOSAIテーブルの出力からレース時刻表を組み立てる。
"""

import math

import pandas as pd

from keiba_data_interface.schema.columns import RACE_SCHEDULE_COLUMNS
from keiba_data_interface.schema.types import RACE_SCHEDULE_TYPES
from keiba_data_interface.utils.converters import convert_hhmm_to_display
from keiba_data_interface.utils.dataframe import apply_types, ensure_columns
from keiba_data_interface.utils.race_code import is_central_keibajo_code

# レース中止を表すデータ区分
_DATA_KUBUN_CANCELLED = "9"

# RACE_SHOSAI → レース時刻表のリネームマッピング
_RACE_SCHEDULE_RENAME: dict[str, str] = {
    "race_code": "レースコード",
    "keibajo_code": "競馬場コード",
    "race_bango": "レース番号",
    "hasso_jikoku": "発走時刻",
    "kyosomei_hondai": "競走名",
}


def convert_race_schedule(raw: pd.DataFrame) -> pd.DataFrame:
    """RACE_SHOSAIの出力をレース時刻表の統一スキーマに変換する.

    データ区分が9（レース中止）の行と、中央競馬以外（地方・海外。競馬場コードが01〜10以外）の
    行は含めない。発走時刻は "HHMM" を "HH:MM" にし、未設定（空文字）は欠損にする。

    Args:
        raw (pd.DataFrame): RaceGetter.get_race_shosai()の出力（convert_codes=False）

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame（RACE_SCHEDULE_COLUMNSのカラム、
            レースコード昇順）
    """
    if len(raw) == 0:
        return apply_types(
            ensure_columns(pd.DataFrame(), RACE_SCHEDULE_COLUMNS), RACE_SCHEDULE_TYPES
        )

    df = raw[
        (raw["data_kubun"].astype(str) != _DATA_KUBUN_CANCELLED)
        & raw["keibajo_code"].astype(str).map(is_central_keibajo_code)
    ]
    df = df.rename(columns=_RACE_SCHEDULE_RENAME)
    df = ensure_columns(df, RACE_SCHEDULE_COLUMNS)
    df["発走時刻"] = [_convert_start_time(value) for value in df["発走時刻"]]
    df = df.sort_values("レースコード").reset_index(drop=True)
    return apply_types(df, RACE_SCHEDULE_TYPES)


def _convert_start_time(value: object) -> str | None:
    """発走時刻を "HHMM" から "HH:MM" にする。未設定（欠損・空文字）は None にする."""
    if value is None or value is pd.NA or (isinstance(value, float) and math.isnan(value)):
        return None
    text = str(value).strip()
    if not text:
        return None
    return convert_hhmm_to_display(text)
