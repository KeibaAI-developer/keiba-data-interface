"""get_result用の変換関数."""

import pandas as pd

from keiba_data_interface.providers.scraping_converters.common import (
    SEIBETSU_TO_CODE,
    TOZAI_SHOZOKU_TO_CODE,
    parse_time_to_seconds,
    set_header_columns,
    set_ijo_kubun,
    set_zogen,
)
from keiba_data_interface.schema.columns import HORSE_RACE_INFO_COLUMNS
from keiba_data_interface.schema.types import HORSE_RACE_INFO_TYPES
from keiba_data_interface.utils.dataframe import apply_types, ensure_columns
from keiba_data_interface.utils.race_code import extract_race_code_parts


def convert_result(
    raw: pd.DataFrame,
    race_code: str,
    prize_map: dict[int, int] | None = None,
) -> pd.DataFrame:
    """get_result用: scraping出力を統一スキーマに変換する.

    Args:
        raw (pd.DataFrame): ResultPageScraper.get_result()の出力
        race_code (str): 16桁レースコード
        prize_map (dict[int, int] | None): 着順→獲得本賞金(百円単位)のマッピング。
            Noneの場合は獲得本賞金を設定しない。

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame（HORSE_RACE_INFO_COLUMNSのカラム）
    """
    parts = extract_race_code_parts(race_code)

    # 1着・2着タイムを取得（タイム差計算用）
    first_time: float | None = None
    second_time: float | None = None
    for _, row in raw.iterrows():
        if pd.notna(row.get("着順")) and str(row["着順"]).isdigit():
            chakujun = int(row["着順"])
            if chakujun == 1 and pd.notna(row.get("タイム")):
                first_time = parse_time_to_seconds(str(row["タイム"]))
            elif chakujun == 2 and pd.notna(row.get("タイム")):
                second_time = parse_time_to_seconds(str(row["タイム"]))
        if first_time is not None and second_time is not None:
            break

    rows: list[dict[str, object]] = []
    for _, row in raw.iterrows():
        converted: dict[str, object] = {}
        set_header_columns(converted, race_code, parts)
        converted["枠番"] = row["枠"]
        converted["馬番"] = row["馬番"]
        converted["血統登録番号"] = row["馬ID"]
        converted["馬名"] = row["馬名"]
        converted["性別コード"] = SEIBETSU_TO_CODE.get(str(row["性別"]), str(row["性別"]))
        converted["馬齢"] = row["年齢"]
        converted["負担重量"] = row["斤量"]
        converted["騎手名略称"] = row["騎手"]
        converted["騎手コード"] = row["騎手ID"]
        shozoku = str(row["所属"]) if pd.notna(row["所属"]) else ""
        converted["所属コード"] = TOZAI_SHOZOKU_TO_CODE.get(shozoku, shozoku)
        converted["調教師名略称"] = row["厩舎"]
        converted["調教師コード"] = row["厩舎ID"]
        converted["馬体重"] = row["馬体重"]

        # 増減 → 増減符号 + 増減差
        set_zogen(converted, row["増減"])

        # 異常区分の判定
        ijo_kubun = row.get("異常区分", "")
        chakusa = row.get("着差", "")
        chakujun_raw = row.get("着順")

        is_kokaku = set_ijo_kubun(converted, ijo_kubun, chakusa)

        # 結果固有カラム
        if pd.notna(chakujun_raw) and str(chakujun_raw).isdigit():
            converted["確定着順"] = int(chakujun_raw)

        if pd.notna(row.get("タイム")):
            converted["走破タイム"] = row["タイム"]

        if pd.notna(chakusa) and not is_kokaku:
            converted["着差1"] = chakusa

        if pd.notna(row.get("人気")) and str(row["人気"]).isdigit():
            converted["単勝人気順"] = int(row["人気"])

        if pd.notna(row.get("単勝オッズ")):
            converted["単勝オッズ"] = row["単勝オッズ"]

        if pd.notna(row.get("後3F")):
            converted["後3ハロン"] = row["後3F"]

        # コーナー通過順
        for i in range(1, 5):
            col = f"{i}コーナー通過順"
            if pd.notna(row.get(col)):
                converted[f"{i}コーナー順位"] = row[col]

        # タイム差の算出
        if (
            first_time is not None
            and pd.notna(row.get("タイム"))
            and converted.get("異常区分コード") == "0"
        ):
            horse_time = parse_time_to_seconds(str(row["タイム"]))
            if (
                pd.notna(chakujun_raw)
                and str(chakujun_raw).isdigit()
                and int(chakujun_raw) == 1
                and second_time is not None
            ):
                # 1着馬: 2着との差を負の値で表現
                converted["タイム差"] = round(first_time - second_time, 1)
            else:
                converted["タイム差"] = round(horse_time - first_time, 1)

        # 獲得本賞金の導出
        if (
            prize_map is not None
            and pd.notna(chakujun_raw)
            and str(chakujun_raw).isdigit()
            and converted.get("異常区分コード") == "0"
        ):
            chakujun = int(chakujun_raw)
            if chakujun in prize_map:
                converted["獲得本賞金"] = prize_map[chakujun]

        rows.append(converted)

    result = pd.DataFrame(rows)
    result = ensure_columns(result, HORSE_RACE_INFO_COLUMNS)
    result = apply_types(result, HORSE_RACE_INFO_TYPES)
    return result
