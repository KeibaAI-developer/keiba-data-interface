"""get_race_info用の変換関数."""

import pandas as pd

from keiba_data_interface.providers.scraping_converters.common import (
    BABAJOTAI_TO_CODE,
    GRADE_TO_CODE,
    JURYO_SHUBETSU_TO_CODE,
    KYOSO_KIGO_TO_CODE,
    KYOSO_SHUBETSU_TO_CODE,
    TENKO_TO_CODE,
    YOBI_TO_CODE,
)
from keiba_data_interface.schema.columns import RACE_INFO_COLUMNS
from keiba_data_interface.schema.types import RACE_INFO_TYPES
from keiba_data_interface.utils.converters import convert_manyen_to_hyakuyen
from keiba_data_interface.utils.dataframe import apply_types, ensure_columns
from keiba_data_interface.utils.race_code import extract_race_code_parts, keibajo_name_to_code


def convert_race_info(raw: pd.DataFrame, race_code: str) -> pd.DataFrame:
    """scraping出力を統一スキーマに変換する.

    Args:
        raw (pd.DataFrame): EntryPageScraper.get_race_info()の出力
        race_code (str): 16桁レースコード

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame

    Raises:
        ValueError: rawが0行または2行以上の場合
    """
    parts = extract_race_code_parts(race_code)

    if len(raw) == 0:
        raise ValueError(
            f"EntryPageScraper.get_race_info() が空のDataFrameを返しました。"
            f"race_code={race_code!r}"
        )
    if len(raw) > 1:
        raise ValueError(
            f"EntryPageScraper.get_race_info() は1行のDataFrameを返す必要がありますが、"
            f"{len(raw)}行返しました。race_code={race_code!r}"
        )

    row = raw.iloc[0]

    converted: dict[str, object] = {}

    # レースコード: 引数の16桁をそのまま使用
    converted["レースコード"] = race_code

    # 日付 → 開催年 + 開催月日（race_codeから導出してキー整合性を保証）
    converted["開催年"] = parts["年"]
    converted["開催月日"] = parts["月日"]

    # そのままマッピングするカラム
    converted["競馬場コード"] = keibajo_name_to_code(str(row["競馬場"]))
    converted["開催回"] = row["回"]
    converted["開催日目"] = row["開催日"]
    converted["レース番号"] = int(parts["R"])
    converted["曜日コード"] = YOBI_TO_CODE.get(str(row["曜日"]) if pd.notna(row["曜日"]) else "")
    converted["競走名本題"] = row["レース名"]
    converted["発走時刻"] = row["発走時刻"]
    converted["天候コード"] = TENKO_TO_CODE.get(str(row["天候"]) if pd.notna(row["天候"]) else "")
    converted["距離"] = row["距離"]
    converted["競走種別コード"] = KYOSO_SHUBETSU_TO_CODE.get(
        str(row["競走種別"]) if pd.notna(row.get("競走種別")) else ""
    )
    converted["競走条件名称"] = row["競走条件"]
    converted["グレードコード"] = GRADE_TO_CODE.get(
        str(row["グレード"]) if pd.notna(row["グレード"]) else "", "_"
    )
    converted["競走記号コード"] = KYOSO_KIGO_TO_CODE.get(
        str(row["競走記号"]) if pd.notna(row.get("競走記号")) else "", "000"
    )
    converted["重量種別コード"] = JURYO_SHUBETSU_TO_CODE.get(
        str(row["重量種別"]) if pd.notna(row["重量種別"]) else ""
    )
    converted["登録頭数"] = row["頭数"]

    # レース種別・芝ダ・左右・内外
    converted["レース種別"] = row["レース種別"]
    shiba_da = str(row["芝ダ"]) if pd.notna(row["芝ダ"]) else ""
    if shiba_da in ("芝", "ダ"):
        converted["芝ダ"] = shiba_da
    sayuu = str(row["左右"]) if pd.notna(row["左右"]) else ""
    if sayuu:
        converted["左右"] = sayuu
    uchisoto = str(row["内外"]) if pd.notna(row.get("内外")) else ""
    if uchisoto:
        converted["内外"] = uchisoto

    # コース
    course = str(row["コース"]) if pd.notna(row["コース"]) else ""
    converted["コース区分"] = course

    # 賞金: 万円 → 百円単位変換
    for i in range(1, 6):
        scraping_col = f"{i}着賞金"
        schema_col = f"本賞金{i}着"
        val = row[scraping_col]
        if pd.notna(val):
            converted[schema_col] = convert_manyen_to_hyakuyen(int(val))

    # 馬場 → 芝馬場状態コード / ダート馬場状態コードの振り分け
    baba = row["馬場"] if pd.notna(row.get("馬場")) else None
    if baba is not None:
        baba_code = BABAJOTAI_TO_CODE.get(str(baba))
        if shiba_da == "芝":
            converted["芝馬場状態コード"] = baba_code
        elif shiba_da == "ダ":
            converted["ダート馬場状態コード"] = baba_code

    result = pd.DataFrame([converted])
    result = ensure_columns(result, RACE_INFO_COLUMNS)
    result = apply_types(result, RACE_INFO_TYPES)
    return result
