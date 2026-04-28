"""get_win_show_odds用の変換関数.

ODDS1_TANSHOとODDS1_FUKUSHOの出力をマージして統一スキーマに変換する。
"""

from typing import Any

import pandas as pd

from keiba_data_interface.schema.columns import ODDS_COLUMNS
from keiba_data_interface.schema.types import ODDS_TYPES
from keiba_data_interface.utils.converters import convert_tenth_to_unit
from keiba_data_interface.utils.dataframe import apply_types, ensure_columns

# 単勝オッズのリネームマッピング
_TANSHO_RENAME: dict[str, str] = {
    "race_code": "レースコード",
    "kaisai_nen": "開催年",
    "kaisai_gappi": "開催月日",
    "keibajo_code": "競馬場コード",
    "kaisai_kaiji": "開催回",
    "kaisai_nichiji": "開催日目",
    "race_bango": "レース番号",
    "umaban": "馬番",
    "ninki": "単勝人気",
}

# 複勝オッズのリネームマッピング
_FUKUSHO_RENAME: dict[str, str] = {
    "umaban": "馬番",
    "ninki": "複勝人気",
}

# 複勝側のみのカラム（マージ時に単勝側から除外する）
_FUKUSHO_ONLY_COLS: set[str] = {"複勝最低オッズ", "複勝最高オッズ", "複勝人気"}


def convert_win_show_odds(raw_tansho: pd.DataFrame, raw_fukusho: pd.DataFrame) -> pd.DataFrame:
    """ODDS1_TANSHOとODDS1_FUKUSHOの出力をマージして統一スキーマに変換する.

    両方空の場合はスキーマカラム付き空DataFrameを返す。
    片方が空の場合はもう片方のみから組み立てる。

    Args:
        raw_tansho (pd.DataFrame): OddsGetter.get_odds1_tansho()の出力（convert_codes=False）
        raw_fukusho (pd.DataFrame): OddsGetter.get_odds1_fukusho()の出力（convert_codes=False）

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame（ODDS_COLUMNSのカラム）
    """
    empty_result = apply_types(ensure_columns(pd.DataFrame(), ODDS_COLUMNS), ODDS_TYPES)

    tansho_empty = len(raw_tansho) == 0
    fukusho_empty = len(raw_fukusho) == 0

    if tansho_empty and fukusho_empty:
        return empty_result

    # 単勝側: ヘッダ＋馬番＋オッズ＋人気
    df_t = raw_tansho.rename(columns=_TANSHO_RENAME).copy()
    if "odds" in raw_tansho.columns and not tansho_empty:
        df_t["単勝オッズ"] = raw_tansho["odds"].apply(_convert_odds_value)

    # 複勝側: 馬番＋オッズ＋人気
    df_f = raw_fukusho.rename(columns=_FUKUSHO_RENAME).copy()
    if "odds_saitei" in raw_fukusho.columns and not fukusho_empty:
        df_f["複勝最低オッズ"] = raw_fukusho["odds_saitei"].apply(_convert_odds_value)
    if "odds_saikou" in raw_fukusho.columns and not fukusho_empty:
        df_f["複勝最高オッズ"] = raw_fukusho["odds_saikou"].apply(_convert_odds_value)

    # マージ（馬番で結合）
    keep_cols_t = [c for c in ODDS_COLUMNS if c in df_t.columns and c not in _FUKUSHO_ONLY_COLS]
    keep_cols_f = ["馬番", "複勝最低オッズ", "複勝最高オッズ", "複勝人気"]
    keep_cols_f = [c for c in keep_cols_f if c in df_f.columns]

    if tansho_empty:
        result = ensure_columns(df_f[keep_cols_f], ODDS_COLUMNS)
    elif fukusho_empty:
        result = ensure_columns(df_t[keep_cols_t], ODDS_COLUMNS)
    else:
        result = df_t[keep_cols_t].merge(df_f[keep_cols_f], on="馬番", how="outer")
        result = ensure_columns(result, ODDS_COLUMNS)

    for col in ("単勝人気", "複勝人気"):
        if col in result.columns:
            result[col] = result[col].apply(_convert_ninki_value)

    result = apply_types(result, ODDS_TYPES)
    return result


def _convert_odds_value(value: Any) -> Any:
    """オッズ値を0.1倍単位から倍単位に変換する（数値以外・0・NAはpd.NAを返す）."""
    if pd.isna(value) or not str(value).isdigit():
        return pd.NA
    int_value = int(value)
    if int_value > 0:
        return convert_tenth_to_unit(int_value)
    return pd.NA


def _convert_ninki_value(value: Any) -> Any:
    """人気文字列を整数に変換する（数値以外・NAはpd.NAを返す）."""
    if pd.isna(value) or not str(value).isdigit():
        return pd.NA
    return int(value)
