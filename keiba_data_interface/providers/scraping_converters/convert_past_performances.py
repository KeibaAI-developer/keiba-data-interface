"""get_past_performances用の変換関数."""

from datetime import date

import pandas as pd

from keiba_data_interface.providers.scraping_converters.common import (
    convert_chakusa_to_code,
    set_ijo_kubun,
    set_zogen,
)
from keiba_data_interface.schema.columns import HORSE_RACE_INFO_COLUMNS
from keiba_data_interface.schema.types import HORSE_RACE_INFO_TYPES
from keiba_data_interface.utils.converters import convert_manyen_to_hyakuyen
from keiba_data_interface.utils.dataframe import apply_types, ensure_columns


def convert_past_performances(raw: pd.DataFrame, horse_id: str) -> pd.DataFrame:
    """get_past_performances用: scraping出力を統一スキーマに変換する.

    Args:
        raw (pd.DataFrame): PastPerformancesScraper.get_past_performances()の出力
        horse_id (str): 馬ID（血統登録番号）

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame（HORSE_RACE_INFO_COLUMNSのカラム）
    """
    if len(raw) == 0:
        return apply_types(
            ensure_columns(pd.DataFrame(), HORSE_RACE_INFO_COLUMNS),
            HORSE_RACE_INFO_TYPES,
        )

    rows: list[dict[str, object]] = []
    for _, row in raw.iterrows():
        converted: dict[str, object] = {}

        # 血統登録番号
        converted["血統登録番号"] = horse_id

        # レースIDからレースコードを構築
        race_id_raw = row.get("レースID")
        if pd.notna(race_id_raw) and pd.notna(row.get("日付")):
            dt = row["日付"]
            if isinstance(dt, date):
                monthday = f"{dt.month:02d}{dt.day:02d}"
                race_id_str = str(race_id_raw)
                # レースコード = 年(4) + 月日(4) + 競馬場(2) + 回(2) + 日目(2) + R(2)
                converted["レースコード"] = race_id_str[:4] + monthday + race_id_str[4:]

        # 日付 → 開催年 + 開催月日
        if pd.notna(row.get("日付")):
            dt = row["日付"]
            if isinstance(dt, date):
                converted["開催年"] = str(dt.year)
                converted["開催月日"] = f"{dt.month:02d}{dt.day:02d}"

        converted["競馬場"] = row.get("競馬場")
        if pd.notna(row.get("回")):
            converted["開催回"] = row["回"]
        if pd.notna(row.get("開催日")):
            converted["開催日目"] = row["開催日"]
        if pd.notna(row.get("R")):
            converted["レース番号"] = row["R"]
        if pd.notna(row.get("枠")):
            converted["枠番"] = row["枠"]
        if pd.notna(row.get("馬番")):
            converted["馬番"] = row["馬番"]
        if pd.notna(row.get("馬名")):
            converted["馬名"] = row["馬名"]

        if pd.notna(row.get("斤量")):
            converted["負担重量"] = row["斤量"]
        if pd.notna(row.get("騎手")):
            converted["騎手名略称"] = row["騎手"]
        if pd.notna(row.get("騎手ID")):
            converted["騎手コード"] = row["騎手ID"]
        if pd.notna(row.get("馬体重")):
            converted["馬体重"] = row["馬体重"]

        # 増減 → 増減符号 + 増減差
        set_zogen(converted, row.get("増減"))

        # 異常区分
        ijo_kubun = row.get("異常区分", "")
        chakusa = row.get("着差", "")
        chakujun_raw = row.get("着順")

        is_kokaku = set_ijo_kubun(converted, ijo_kubun, chakusa)

        # 結果カラム
        if pd.notna(chakujun_raw) and str(chakujun_raw).isdigit():
            converted["確定着順"] = int(chakujun_raw)

        if pd.notna(row.get("タイム")):
            converted["走破タイム"] = row["タイム"]

        if pd.notna(chakusa) and not is_kokaku:
            converted["着差コード1"] = convert_chakusa_to_code(chakusa)

        if pd.notna(row.get("人気")) and str(row["人気"]).isdigit():
            converted["単勝人気順"] = int(row["人気"])

        if pd.notna(row.get("単勝オッズ")):
            converted["単勝オッズ"] = row["単勝オッズ"]

        if pd.notna(row.get("後3F")):
            converted["後3ハロン"] = row["後3F"]

        if pd.notna(row.get("頭数")):
            converted["出走頭数"] = row["頭数"]

        # コーナー通過順
        for i in range(1, 5):
            col = f"{i}コーナー通過順"
            if pd.notna(row.get(col)):
                converted[f"{i}コーナー順位"] = row[col]

        # 賞金: 万円 → 百円単位
        if pd.notna(row.get("賞金")):
            converted["獲得本賞金"] = convert_manyen_to_hyakuyen(int(row["賞金"]))

        # 勝ち馬(2着馬) → 相手1馬名（先頭・末尾のカッコを除去）
        if pd.notna(row.get("勝ち馬(2着馬)")):
            horse_name = str(row["勝ち馬(2着馬)"])
            if horse_name.startswith("(") and horse_name.endswith(")"):
                horse_name = horse_name[1:-1]
            converted["相手1馬名"] = horse_name

        rows.append(converted)

    result = pd.DataFrame(rows)
    result = ensure_columns(result, HORSE_RACE_INFO_COLUMNS)
    result = apply_types(result, HORSE_RACE_INFO_TYPES)
    return result
