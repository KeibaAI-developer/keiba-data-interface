"""get_result用の変換関数.

UMAGOTO_RACE_JOHOテーブルの結果データを統一スキーマに変換する。
共通変換のあと、走破タイムの"MSSS"→"M:SS.S"変換を行う。
"""

from typing import Any

import pandas as pd

from keiba_data_interface.providers.mykeibadb_converters.convert_entry import convert_base
from keiba_data_interface.utils.converters import convert_time_msss_to_display


def convert_result(raw: pd.DataFrame) -> pd.DataFrame:
    """UMAGOTO_RACE_JOHOの結果データを統一スキーマに変換する.

    共通変換のあと、走破タイム・タイム差・コーナー順位を変換し、
    単勝人気順を単勝オッズから再計算する。

    新潟芝1000m直線レースでは、4コーナー順位をDBの格納値（全0）の代わりに
    「走破タイム - 後3ハロン」の昇順ランクで算出する。

    Args:
        raw (pd.DataFrame): RaceGetter.get_umagoto_race_joho()の出力（convert_codes=True）

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame
    """
    # 新潟芝1000m直線レースか判定（変換前のrawデータで確認）
    niigata_straight_rank: pd.Series | None = None
    if _is_niigata_straight_1000m(raw):
        niigata_straight_rank = _calc_zenhan_time_rank(raw)

    df = convert_result_common(convert_base(raw))

    # 新潟芝1000m直線: 4コーナー順位を前半タイム（走破タイム-後3ハロン）の昇順ランクで設定
    if niigata_straight_rank is not None and "4コーナー順位" in df.columns:
        df["4コーナー順位"] = niigata_straight_rank.astype("Int64")

    # 単勝人気順: 単勝オッズから再計算（同一オッズは同順位、NaNオッズの馬はNaN）
    if "単勝オッズ" in df.columns and "単勝人気順" in df.columns:
        valid_mask = df["単勝オッズ"].notna()
        if valid_mask.any():
            df.loc[valid_mask, "単勝人気順"] = (
                df.loc[valid_mask, "単勝オッズ"].rank(method="min", ascending=True).astype("Int64")
            )
        df.loc[~valid_mask, "単勝人気順"] = pd.NA

    # 確定着順順にソート
    df = df.sort_values("確定着順").reset_index(drop=True)

    return df


def convert_result_common(df: pd.DataFrame) -> pd.DataFrame:
    """走破タイム・タイム差・コーナー順位の共通変換を適用する.

    convert_resultとconvert_past_performancesの共通後処理。
    単勝人気順の再計算は含めない（レース全馬揃いの時のみ有効のため）。
    """
    if "走破タイム" in df.columns:
        df["走破タイム"] = df["走破タイム"].apply(_convert_soha_time)

    if "タイム差" in df.columns:
        df["タイム差"] = df["タイム差"].apply(_convert_time_sa).astype("Float64")

    # コーナー順位の0→NaN変換（競走中止等でコーナー通過がない場合）
    for i in range(1, 5):
        col = f"{i}コーナー順位"
        if col in df.columns:
            df[col] = (
                df[col]
                .apply(lambda v: pd.NA if not pd.isna(v) and int(v) == 0 else v)
                .astype("Int64")
            )

    # 単勝人気順の0→NaN変換（出走取消等でオッズが存在しない場合）
    if "単勝人気順" in df.columns:
        df["単勝人気順"] = (
            df["単勝人気順"]
            .apply(lambda v: pd.NA if not pd.isna(v) and int(v) == 0 else v)
            .astype("Int64")
        )

    return df


def _convert_soha_time(value: Any) -> Any:
    """走破タイムをMSSS形式からM:SS.S形式に変換する."""
    if pd.isna(value):
        return value
    str_val = str(value).strip()
    if str_val and str_val.isdigit():
        int_val = int(str_val)
        if int_val == 0:
            return pd.NA  # 0000 = タイム未計測（競走中止等）
        return convert_time_msss_to_display(str_val)
    return value


def _convert_time_sa(value: Any) -> Any:
    """タイム差を1/10秒単位の整数から秒単位に変換する."""
    if pd.isna(value):
        return value
    try:
        int_val = int(value)
    except (ValueError, TypeError):
        return value
    if int_val == 9999:
        return pd.NA  # 9999 = タイム差計測不能（競走中止等）
    return round(int_val / 10, 1)


def _is_niigata_straight_1000m(raw: pd.DataFrame) -> bool:
    """新潟芝直線1000mレースか判定する.

    keibajo_code == "04"（新潟）かつ全コーナー通過順位が"00"（直線コース）の場合にTrueを返す。
    直線1000mではコーナーが存在しないためDBに全て"00"が格納される。

    Args:
        raw (pd.DataFrame): RaceGetter.get_umagoto_race_joho()の出力

    Returns:
        bool: 新潟芝直線1000mレースであればTrue
    """
    if "keibajo_code" not in raw.columns:
        return False
    if not (raw["keibajo_code"].astype(str) == "04").all():
        return False
    for col in ["corner1_juni", "corner2_juni", "corner3_juni", "corner4_juni"]:
        if col not in raw.columns:
            return False
        if not (pd.to_numeric(raw[col], errors="coerce").fillna(0) == 0).all():
            return False
    return True


def _calc_zenhan_time_rank(raw: pd.DataFrame) -> pd.Series:
    """前半タイム（走破タイム - 後3ハロン）の昇順ランクを計算する（新潟芝直線1000m用）.

    走破タイムまたは後3ハロンが無効値（0 / 999）の馬はNaN扱い。
    同タイムの馬は同順位（method='min'）。

    Args:
        raw (pd.DataFrame): RaceGetter.get_umagoto_race_joho()の出力

    Returns:
        pd.Series: rawと同一インデックスの4コーナー順位（Int64）
    """
    soha = pd.to_numeric(raw["soha_time"], errors="coerce")
    kohan = pd.to_numeric(raw["kohan_3f"], errors="coerce")
    valid_mask = soha.notna() & (soha != 0) & kohan.notna() & (kohan != 999)
    zenhan = soha - kohan

    result: pd.Series = pd.Series(pd.NA, index=raw.index, dtype="Int64")
    if valid_mask.any():
        result[valid_mask] = zenhan[valid_mask].rank(method="min", ascending=True).astype("Int64")
    return result
