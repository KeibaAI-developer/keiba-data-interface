"""get_win_show_odds用の変換関数.

ODDS1_TANSHOとODDS1_FUKUSHOの出力をマージして統一スキーマに変換する。
"""

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
    "keibajo": "競馬場",
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


def convert_odds(raw_tansho: pd.DataFrame, raw_fukusho: pd.DataFrame) -> pd.DataFrame:
    """ODDS1_TANSHOとODDS1_FUKUSHOの出力をマージして統一スキーマに変換する.

    Args:
        raw_tansho (pd.DataFrame): OddsGetter.get_odds1_tansho()の出力（convert_codes=True）
        raw_fukusho (pd.DataFrame): OddsGetter.get_odds1_fukusho()の出力（convert_codes=True）

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame（ODDS_COLUMNSのカラム）
    """
    # 単勝側: ヘッダ＋馬番＋オッズ＋人気
    df_t = raw_tansho.rename(columns=_TANSHO_RENAME).copy()
    if "odds" in raw_tansho.columns:
        df_t["単勝オッズ"] = raw_tansho["odds"].apply(
            lambda v: convert_tenth_to_unit(int(v)) if pd.notna(v) and int(v) > 0 else pd.NA
        )

    # 複勝側: 馬番＋オッズ＋人気
    df_f = raw_fukusho.rename(columns=_FUKUSHO_RENAME).copy()
    if "odds_saitei" in raw_fukusho.columns:
        df_f["複勝最低オッズ"] = raw_fukusho["odds_saitei"].apply(
            lambda v: convert_tenth_to_unit(int(v)) if pd.notna(v) and int(v) > 0 else pd.NA
        )
    if "odds_saikou" in raw_fukusho.columns:
        df_f["複勝最高オッズ"] = raw_fukusho["odds_saikou"].apply(
            lambda v: convert_tenth_to_unit(int(v)) if pd.notna(v) and int(v) > 0 else pd.NA
        )

    # マージ（馬番で結合）
    keep_cols_t = [
        c
        for c in ODDS_COLUMNS
        if c in df_t.columns and c != "複勝最低オッズ" and c != "複勝最高オッズ" and c != "複勝人気"
    ]
    keep_cols_f = ["馬番", "複勝最低オッズ", "複勝最高オッズ", "複勝人気"]
    keep_cols_f = [c for c in keep_cols_f if c in df_f.columns]

    result = df_t[keep_cols_t].merge(df_f[keep_cols_f], on="馬番", how="outer")
    result = ensure_columns(result, ODDS_COLUMNS)
    result = apply_types(result, ODDS_TYPES)
    return result
