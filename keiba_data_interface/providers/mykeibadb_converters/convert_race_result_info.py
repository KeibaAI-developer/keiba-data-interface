"""get_race_result_info用の変換関数.

RACE_SHOSAIテーブルのラップタイム・コーナー通過順部分を統一スキーマに変換する。
"""

import pandas as pd

from keiba_data_interface.schema.columns import RACE_RESULT_INFO_COLUMNS
from keiba_data_interface.schema.types import RACE_RESULT_INFO_TYPES
from keiba_data_interface.utils.converters import convert_tenth_to_unit
from keiba_data_interface.utils.dataframe import apply_types, ensure_columns

# 0.1秒→秒変換が必要なハロンタイムカラム
_HARLON_TIME_COLUMNS: dict[str, str] = {
    "zenhan_3f": "前3ハロン",
    "zenhan_4f": "前4ハロン",
    "kohan_3f": "後3ハロン",
    "kohan_4f": "後4ハロン",
}

# コーナー情報のマッピング（src_prefix, dst_suffix）
_CORNER_COLUMNS: list[tuple[str, str]] = [
    ("shukaisu", "コーナー周回数"),
    ("kaku_tsuka_juni", "コーナー通過順"),
]

# その他のリネームマッピング
_DIRECT_RENAME: dict[str, str] = {
    "shogai_mile_time": "障害マイルタイム",
    "record_koshin_kubun": "レコード更新区分",
}


def convert_race_result_info(raw: pd.DataFrame) -> pd.DataFrame:
    """RACE_SHOSAIの結果情報部分を統一スキーマに変換する.

    ラップタイム（200m刻み→100m刻み展開、0.1秒→秒変換）、
    ハロンタイム（0.1秒→秒変換）、コーナー通過順を統一スキーマに変換する。

    Args:
        raw (pd.DataFrame): RaceGetter.get_race_shosai()の出力（convert_codes=True）

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame

    Raises:
        ValueError: rawが0行または2行以上の場合
    """
    if len(raw) == 0:
        raise ValueError("get_race_shosai()が空のDataFrameを返しました")
    if len(raw) > 1:
        raise ValueError(
            f"get_race_shosai()は1行のDataFrameを返す必要がありますが、" f"{len(raw)}行返しました"
        )

    row = raw.iloc[0]
    converted: dict[str, object] = {}

    converted["レースコード"] = row["race_code"]

    # 距離を取得してラップ展開方法を決定
    distance = int(row["kyori"]) if "kyori" in row.index and pd.notna(row["kyori"]) else 0
    is_odd_distance = (distance % 200) != 0

    # ラップタイム展開（200m刻み → 100m刻み、0.1秒 → 秒）
    for i in range(1, 26):
        col = f"lap_time{i}"
        if col in row.index and pd.notna(row[col]) and int(row[col]) > 0:
            val = convert_tenth_to_unit(int(row[col]))
            if is_odd_distance:
                target_dist = 100 if i == 1 else 100 + (i - 1) * 200
            else:
                target_dist = i * 200
            if target_dist <= 5000:
                converted[f"ラップ{target_dist}m"] = val

    # ハロンタイム（0.1秒 → 秒）
    for src, dst in _HARLON_TIME_COLUMNS.items():
        if src in row.index and pd.notna(row[src]) and int(row[src]) > 0:
            converted[dst] = convert_tenth_to_unit(int(row[src]))

    # コーナー情報
    # corner{i}は「スロットiに収録されているのは実際に第何コーナーか」を示す数値文字列
    # ("0"はデータなし)。kaku_tsuka_juni{i}を実際のコーナー番号に対応する
    # nコーナー通過順カラムに格納する。
    for i in range(1, 5):
        corner_src = f"corner{i}"
        if corner_src not in row.index:
            continue
        corner_val = str(row[corner_src]).strip() if pd.notna(row[corner_src]) else "0"
        if corner_val in ("0", ""):
            continue
        for src_prefix, dst_suffix in _CORNER_COLUMNS:
            src = f"{src_prefix}{i}"
            dst = f"{corner_val}{dst_suffix}"
            if src in row.index and pd.notna(row[src]):
                val = row[src]
                if dst_suffix == "コーナー周回数" and int(val) == 0:
                    continue
                if dst_suffix == "コーナー通過順" and str(val).strip() == "":
                    continue
                converted[dst] = str(val).strip() if dst_suffix == "コーナー通過順" else val

    # その他のカラム
    for src, dst in _DIRECT_RENAME.items():
        if src in row.index and pd.notna(row[src]):
            converted[dst] = row[src]

    result = pd.DataFrame([converted])
    result = ensure_columns(result, RACE_RESULT_INFO_COLUMNS)
    result = apply_types(result, RACE_RESULT_INFO_TYPES)
    return result
