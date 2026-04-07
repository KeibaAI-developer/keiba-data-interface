"""get_race_info用の変換関数.

RACE_SHOSAIテーブルの出力を統一スキーマに変換する。
"""

import pandas as pd

from keiba_data_interface.schema.columns import RACE_INFO_COLUMNS
from keiba_data_interface.schema.types import RACE_INFO_TYPES
from keiba_data_interface.utils.converters import convert_hhmm_to_display
from keiba_data_interface.utils.dataframe import apply_types, ensure_columns

# RACE_SHOSAI → レース基本情報のカラムリネームマッピング
RACE_INFO_RENAME: dict[str, str] = {
    "race_code": "レースコード",
    "kaisai_nen": "開催年",
    "kaisai_gappi": "開催月日",
    "keibajo": "競馬場",
    "kaisai_kai": "開催回",
    "kaisai_nichime": "開催日目",
    "race_bango": "レース番号",
    "yobi": "曜日",
    "tokubetsu_kyoso_bango": "特別競走番号",
    "kyosomei_hondai": "競走名本題",
    "kyosomei_fukudai": "競走名副題",
    "kyosomei_kakkonai": "競走名カッコ内",
    "kyosomei_hondai_eng": "競走名本題欧字",
    "kyosomei_fukudai_eng": "競走名副題欧字",
    "kyosomei_kakkonai_eng": "競走名カッコ内欧字",
    "kyosomei_ryakusho_10": "競走名略称10文字",
    "kyosomei_ryakusho_6": "競走名略称6文字",
    "kyosomei_ryakusho_3": "競走名略称3文字",
    "kyosomei_kubun": "競走名区分",
    "jusho_kaiji": "重賞回次",
    "grade_code": "グレードコード",
    "henkomae_grade_code": "変更前グレードコード",
    "kyoso_shubetsu": "競走種別",
    "kyoso_kigo_code": "競走記号コード",
    "juryo_shubetsu": "重量種別",
    "kyoso_joken_code_2sai": "競走条件2歳",
    "kyoso_joken_code_3sai": "競走条件3歳",
    "kyoso_joken_code_4sai": "競走条件4歳",
    "kyoso_joken_code_5sai_ijo": "競走条件5歳以上",
    "kyoso_joken_code_saijakunen": "競走条件最若年",
    "kyoso_joken_meisho": "競走条件名称",
    "kyori": "距離",
    "henkomae_kyori": "変更前距離",
    "track": "トラック",
    "henkomae_track": "変更前トラック",
    "course_kubun": "コース区分",
    "henkomae_course_kubun": "変更前コース区分",
    "honshokin1": "本賞金1着",
    "honshokin2": "本賞金2着",
    "honshokin3": "本賞金3着",
    "honshokin4": "本賞金4着",
    "honshokin5": "本賞金5着",
    "honshokin6": "本賞金6着",
    "honshokin7": "本賞金7着",
    "henkomae_honshokin1": "変更前本賞金1着",
    "henkomae_honshokin2": "変更前本賞金2着",
    "henkomae_honshokin3": "変更前本賞金3着",
    "henkomae_honshokin4": "変更前本賞金4着",
    "henkomae_honshokin5": "変更前本賞金5着",
    "fukashokin1": "付加賞金1着",
    "fukashokin2": "付加賞金2着",
    "fukashokin3": "付加賞金3着",
    "fukashokin4": "付加賞金4着",
    "fukashokin5": "付加賞金5着",
    "henkomae_fukashokin1": "変更前付加賞金1着",
    "henkomae_fukashokin2": "変更前付加賞金2着",
    "henkomae_fukashokin3": "変更前付加賞金3着",
    "hasso_jikoku": "発走時刻",
    "henkomae_hasso_jikoku": "変更前発走時刻",
    "toroku_tosu": "登録頭数",
    "shusso_tosu": "出走頭数",
    "nyusen_tosu": "入線頭数",
    "tenko": "天候",
    "shiba_babajotai_code": "芝馬場状態コード",
    "dirt_babajotai_code": "ダート馬場状態コード",
}


def convert_race_info(raw: pd.DataFrame) -> pd.DataFrame:
    """RACE_SHOSAIの出力を統一スキーマに変換する.

    Args:
        raw (pd.DataFrame): RaceGetter.get_race_shosai()の出力（convert_codes=True）

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame

    Raises:
        ValueError: rawが0行または2行以上の場合
    """
    race_code_info = ""
    if "race_code" in raw.columns:
        unique_race_codes = raw["race_code"].dropna().unique()
        if len(unique_race_codes) == 1:
            race_code_info = f" (race_code={unique_race_codes[0]})"
        elif len(unique_race_codes) > 1:
            race_code_info = f" (race_code一覧={unique_race_codes.tolist()})"

    if len(raw) == 0:
        raise ValueError(f"get_race_shosai()が空のDataFrameを返しました{race_code_info}")
    if len(raw) > 1:
        raise ValueError(
            f"get_race_shosai()は1行のDataFrameを返す必要がありますが、"
            f"{len(raw)}行返しました{race_code_info}"
        )

    df = raw.copy()

    # 発走時刻 "HHMM" → "HH:MM" 変換
    for col in ["hasso_jikoku", "henkomae_hasso_jikoku"]:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda v: convert_hhmm_to_display(str(v)) if pd.notna(v) and str(v).strip() else v
            )

    # グレードコード: スペース（未設定の初期値）は "_"（一般競走）に統一する
    for col in ["grade_code", "henkomae_grade_code"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda v: "_" if pd.notna(v) and str(v).strip() == "" else v)

    # 馬場状態コード: "0"（未設定）または空白（対象トラックなし）は NaN に統一する
    for col in ["shiba_babajotai_code", "dirt_babajotai_code"]:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda v: (
                    pd.NA if pd.isna(v) or str(v).strip() == "" or str(v).strip() == "0" else v
                )
            )

    # コース区分: 末尾スペース除去（例: "A " → "A"）
    for col in ["course_kubun", "henkomae_course_kubun"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda v: str(v).strip() if pd.notna(v) else v)

    df = df.rename(columns=RACE_INFO_RENAME)

    df = ensure_columns(df, RACE_INFO_COLUMNS)
    df = apply_types(df, RACE_INFO_TYPES)
    return df
