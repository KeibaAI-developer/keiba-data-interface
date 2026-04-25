"""get_result用の変換関数."""

from typing import Any

import pandas as pd

from keiba_data_interface.providers.scraping_converters.common import (
    SEIBETSU_TO_CODE,
    TOZAI_SHOZOKU_TO_CODE,
    convert_chakusa_to_code,
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
    # 着順は整数(1)または浮動小数点(1.0)で渡される場合があるため _parse_chakujun で統一変換する
    first_time: float | None = None
    second_time: float | None = None
    for _, row in raw.iterrows():
        chakujun = _parse_chakujun(row.get("着順"))
        if chakujun is not None:
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
        chakujun_int = _parse_chakujun(chakujun_raw)
        if chakujun_int is not None:
            converted["確定着順"] = chakujun_int

        if pd.notna(row.get("タイム")):
            converted["走破タイム"] = row["タイム"]
        else:
            converted["走破タイム"] = pd.NA

        if pd.notna(chakusa) and not is_kokaku:
            converted["着差コード1"] = convert_chakusa_to_code(chakusa)
        else:
            converted["着差コード1"] = pd.NA

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
        # 異常区分コード "5"(失格), "7"(降着) も完走しているためタイム差を算出する
        if (
            first_time is not None
            and pd.notna(row.get("タイム"))
            and converted.get("異常区分コード") in {"0", "5", "7"}
        ):
            horse_time = parse_time_to_seconds(str(row["タイム"]))
            if chakujun_int is not None and chakujun_int == 1 and second_time is not None:
                # 1着馬: 2着との差を負の値で表現
                converted["タイム差"] = round(first_time - second_time, 1)
            else:
                converted["タイム差"] = round(horse_time - first_time, 1)

        # 獲得本賞金の導出
        # prize_mapがある場合: 正常完走馬(異常区分コード="0")と降着馬(="7")でprice_mapに着順がある→賞金額、それ以外→0
        # prize_mapがない場合: 獲得本賞金は設定しない（NaN）
        if prize_map is not None:
            if (
                chakujun_int is not None
                and converted.get("異常区分コード") in {"0", "7"}
                and chakujun_int in prize_map
            ):
                converted["獲得本賞金"] = prize_map[chakujun_int]
            else:
                converted["獲得本賞金"] = 0

        rows.append(converted)

    result = pd.DataFrame(rows)
    result = ensure_columns(result, HORSE_RACE_INFO_COLUMNS)
    result = apply_types(result, HORSE_RACE_INFO_TYPES)
    result = _recalculate_ninkijun(result)
    return result


def _recalculate_ninkijun(df: pd.DataFrame) -> pd.DataFrame:
    """単勝オッズから単勝人気順を再計算する.

    同一オッズの馬には同じ人気順を付与する。
    単勝オッズがNaN（出走取消等）の馬は単勝人気順もNaNにする。
    """
    if "単勝オッズ" not in df.columns or "単勝人気順" not in df.columns:
        return df
    valid_mask = df["単勝オッズ"].notna()
    if valid_mask.any():
        odds = df.loc[valid_mask, "単勝オッズ"]
        df.loc[valid_mask, "単勝人気順"] = odds.rank(method="min", ascending=True).astype("Int64")
    df.loc[~valid_mask, "単勝人気順"] = pd.NA
    return df


def _parse_chakujun(value: Any) -> int | None:
    """着順値を正の整数に変換する.

    整数(1)・浮動小数点(1.0)・整数文字列("1")のいずれも処理する。
    正の整数に変換できない場合はNoneを返す。
    """
    if pd.isna(value):
        return None
    try:
        result = int(float(str(value)))
        return result if result > 0 else None
    except (ValueError, TypeError):
        return None
