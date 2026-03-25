"""get_race_result_info用の変換関数."""

import pandas as pd

from keiba_data_interface.schema.columns import RACE_RESULT_INFO_COLUMNS
from keiba_data_interface.schema.types import RACE_RESULT_INFO_TYPES
from keiba_data_interface.utils.dataframe import apply_types, ensure_columns


def convert_race_result_info(
    raw_lap: pd.DataFrame, raw_corner: pd.DataFrame, race_code: str
) -> pd.DataFrame:
    """get_race_result_info用: ラップタイムとコーナー通過順を統一スキーマに変換する.

    Args:
        raw_lap (pd.DataFrame): ResultPageScraper.get_lap_time()の出力
        raw_corner (pd.DataFrame): ResultPageScraper.get_corner()の出力
        race_code (str): 16桁レースコード

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame（RACE_RESULT_INFO_COLUMNSのカラム）
    """
    converted: dict[str, object] = {}
    converted["レースコード"] = race_code

    # ラップタイム
    if len(raw_lap) > 0:
        lap_row = raw_lap.iloc[0]
        for dist in range(100, 5001, 100):
            col = f"{dist}m"
            if col in lap_row.index and pd.notna(lap_row[col]):
                converted[f"ラップ{dist}m"] = lap_row[col]

        # 前3ハロン / 後3ハロン
        if "レース前3F" in lap_row.index and pd.notna(lap_row["レース前3F"]):
            converted["前3ハロン"] = lap_row["レース前3F"]
        if "レース後3F" in lap_row.index and pd.notna(lap_row["レース後3F"]):
            converted["後3ハロン"] = lap_row["レース後3F"]

    # コーナー通過順
    if len(raw_corner) > 0:
        corner_row = raw_corner.iloc[0]
        for i in range(1, 5):
            col = f"{i}コーナー通過順"
            if col in corner_row.index and pd.notna(corner_row[col]):
                converted[f"{i}コーナー通過順"] = corner_row[col]

    result = pd.DataFrame([converted])
    result = ensure_columns(result, RACE_RESULT_INFO_COLUMNS)
    result = apply_types(result, RACE_RESULT_INFO_TYPES)
    return result
