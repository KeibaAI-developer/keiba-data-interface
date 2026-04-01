"""get_entry用の変換関数.

UMAGOTO_RACE_JOHOテーブルの出力を統一スキーマに変換する。
"""

import pandas as pd

from keiba_data_interface.schema.columns import HORSE_RACE_INFO_COLUMNS
from keiba_data_interface.schema.types import HORSE_RACE_INFO_TYPES
from keiba_data_interface.utils.converters import convert_tenth_to_unit
from keiba_data_interface.utils.dataframe import apply_types, ensure_columns

# UMAGOTO_RACE_JOHO → 馬毎レース情報のカラムリネームマッピング
ENTRY_RENAME: dict[str, str] = {
    "race_code": "レースコード",
    "kaisai_nen": "開催年",
    "kaisai_gappi": "開催月日",
    "keibajo": "競馬場",
    "kaisai_kaiji": "開催回",
    "kaisai_nichiji": "開催日目",
    "race_bango": "レース番号",
    "wakuban": "枠番",
    "umaban": "馬番",
    "ketto_toroku_bango": "血統登録番号",
    "bamei": "馬名",
    "umakigo": "馬記号",
    "seibetsu_code": "性別コード",
    "hinshu": "品種",
    "moshoku": "毛色",
    "barei": "馬齢",
    "tozai_shozoku_code": "所属コード",
    "chokyoshi_code": "調教師コード",
    "chokyoshimei_ryakusho": "調教師名略称",
    "banushi_code": "馬主コード",
    "banushimei_hojinkaku_nashi": "馬主名",
    "fukushoku_hyoji": "服色標示",
    "blinker_shiyo_kubun": "ブリンカー使用区分",
    "kishu_code": "騎手コード",
    "henkomae_kishu_code": "変更前騎手コード",
    "kishumei_ryakusho": "騎手名略称",
    "henkomae_kishumei_ryakusho": "変更前騎手名略称",
    "kishu_minarai_code": "騎手見習コード",
    "henkomae_kishu_minarai_code": "変更前騎手見習コード",
    "bataiju": "馬体重",
    "zogen_fugo": "増減符号",
    "zogen_sa": "増減差",
    "ijo_kubun_code": "異常区分コード",
    "nyusen_juni": "入線順位",
    "kakutei_chakujun": "確定着順",
    "dochaku_kubun": "同着区分",
    "dochaku_tosu": "同着頭数",
    "soha_time": "走破タイム",
    "chakusa1": "着差1",
    "chakusa2": "着差2",
    "chakusa3": "着差3",
    "corner1_juni": "1コーナー順位",
    "corner2_juni": "2コーナー順位",
    "corner3_juni": "3コーナー順位",
    "corner4_juni": "4コーナー順位",
    "tansho_ninkijun": "単勝人気順",
    "kakutoku_honshokin": "獲得本賞金",
    "kakutoku_fukashokin": "獲得付加賞金",
    "aite1_ketto_toroku_bango": "相手1血統登録番号",
    "aite1_bamei": "相手1馬名",
    "aite2_ketto_toroku_bango": "相手2血統登録番号",
    "aite2_bamei": "相手2馬名",
    "aite3_ketto_toroku_bango": "相手3血統登録番号",
    "aite3_bamei": "相手3馬名",
    "time_sa": "タイム差",
    "record_koshin_kubun": "レコード更新区分",
    "mining_kubun": "マイニング区分",
    "mining_yoso_soha_time": "マイニング予想走破タイム",
    "mining_yoso_gosa_plus": "マイニング予想誤差プラス",
    "mining_yoso_gosa_minus": "マイニング予想誤差マイナス",
    "mining_yoso_juni": "マイニング予想順位",
    "kyakushitsu": "脚質判定",
}

# 値変換が必要なカラムのリネームマッピング
# ENTRY_RENAMEに含めず、値変換後に別途リネームする
_VALUE_CONVERT_RENAME: dict[str, str] = {
    "futan_juryo": "負担重量",
    "henkomae_futan_juryo": "変更前負担重量",
    "tansho_odds": "単勝オッズ",
    "kohan_3f": "後3ハロン",
    "kohan_4f": "後4ハロン",
}


def convert_entry(raw: pd.DataFrame) -> pd.DataFrame:
    """UMAGOTO_RACE_JOHOの出力を統一スキーマに変換する（get_entry用）.

    Args:
        raw (pd.DataFrame): RaceGetter.get_umagoto_race_joho()の出力（convert_codes=True）

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame
    """
    df = convert_base(raw)

    # 異常区分コード: 4以上（競走中止・失格・降着等）はエントリー時点では未確定なので0に正規化
    if "異常区分コード" in df.columns:
        df["異常区分コード"] = df["異常区分コード"].apply(
            lambda v: "0" if pd.notna(v) and int(v) >= 4 else (str(int(v)) if pd.notna(v) else v)
        )

    return df


def convert_base(raw: pd.DataFrame) -> pd.DataFrame:
    """UMAGOTO_RACE_JOHOの出力を統一スキーマに変換する（共通処理）.

    convert_entryとconvert_resultの共通処理。
    カラムリネーム・値変換・スキーマ適用を行う。
    異常区分コードは元の値をそのまま保持する。

    Args:
        raw (pd.DataFrame): RaceGetter.get_umagoto_race_joho()の出力（convert_codes=True）

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame
    """
    df = raw.copy()

    # 0.1単位 → 実数単位 変換（負担重量, 単勝オッズ, 後3F, 後4F）
    for col in _VALUE_CONVERT_RENAME:
        if col in df.columns:
            df[col] = df[col].apply(lambda v: convert_tenth_to_unit(int(v)) if pd.notna(v) else v)

    df = df.rename(columns=ENTRY_RENAME)
    df = df.rename(columns=_VALUE_CONVERT_RENAME)

    # 異常区分コード: str型に統一
    if "異常区分コード" in df.columns:
        df["異常区分コード"] = df["異常区分コード"].apply(
            lambda v: str(int(v)) if pd.notna(v) and str(v).strip() else "0"
        )

    df = ensure_columns(df, HORSE_RACE_INFO_COLUMNS)
    df = apply_types(df, HORSE_RACE_INFO_TYPES)
    return df
