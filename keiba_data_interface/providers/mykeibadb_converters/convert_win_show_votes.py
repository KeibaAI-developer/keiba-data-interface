"""get_win_show_votes用の変換関数.

HYOSU1_TANSHO・HYOSU1_FUKUSHO（馬番ごとの票数）と ODDS1（票数合計）の出力をマージして
統一スキーマに変換する。
"""

from typing import Any

import pandas as pd

from keiba_data_interface.schema.columns import WIN_SHOW_VOTES_COLUMNS
from keiba_data_interface.schema.types import VOTES_TYPES
from keiba_data_interface.utils.dataframe import apply_types, ensure_columns

# 単勝票数のリネームマッピング（ヘッダはこちらから取る）
_TANSHO_RENAME: dict[str, str] = {
    "race_code": "レースコード",
    "kaisai_nen": "開催年",
    "kaisai_gappi": "開催月日",
    "keibajo_code": "競馬場コード",
    "kaisai_kaiji": "開催回",
    "kaisai_nichiji": "開催日目",
    "race_bango": "レース番号",
    "data_kubun": "データ区分",
    "umaban": "馬番",
    "hyosu": "単勝票数",
    "ninki": "単勝票数人気",
}

# 複勝票数のリネームマッピング
_FUKUSHO_RENAME: dict[str, str] = {
    "umaban": "馬番",
    "hyosu": "複勝票数",
    "ninki": "複勝票数人気",
}

# ODDS1（ベース情報）から取る票数合計
_TOTAL_RENAME: dict[str, str] = {
    "tansho_hyosu_gokei": "単勝票数合計",
    "fukusho_hyosu_gokei": "複勝票数合計",
}


def convert_win_show_votes(
    raw_tansho: pd.DataFrame, raw_fukusho: pd.DataFrame, raw_odds1: pd.DataFrame
) -> pd.DataFrame:
    """HYOSU1_TANSHO・HYOSU1_FUKUSHO・ODDS1 の出力をマージして統一スキーマに変換する.

    票数（HYOSU）は「ALL0: 発売前取消・発売票数なし」を0、「スペース: 登録なし」を欠損に
    変換し、登録なし（単勝票数・複勝票数がともに欠損）の行は除く。人気順（NINKI）は
    「--: 発売前取消」「**: 発売後取消」「スペース: 登録なし」を欠損にする。
    票数の単位は mykeibadb のまま百円とし、円に換算しない。

    Args:
        raw_tansho (pd.DataFrame): HyosuGetter.get_hyosu1_tansho()の出力（convert_codes=False）
        raw_fukusho (pd.DataFrame): HyosuGetter.get_hyosu1_fukusho()の出力（convert_codes=False）
        raw_odds1 (pd.DataFrame): OddsGetter.get_odds1()の出力（convert_codes=False、1行）

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame（WIN_SHOW_VOTES_COLUMNSのカラム、馬番順）

    Raises:
        ValueError: いずれかの入力が空、または raw_odds1 が複数行の場合
    """
    if len(raw_tansho) == 0 or len(raw_fukusho) == 0 or len(raw_odds1) == 0:
        raise ValueError("票数の変換元が空です（HYOSU1_TANSHO / HYOSU1_FUKUSHO / ODDS1）")
    if len(raw_odds1) != 1:
        raise ValueError(f"ODDS1 は1行である必要があります: {len(raw_odds1)}行")

    df_t = raw_tansho.rename(columns=_TANSHO_RENAME)
    df_t = df_t[[c for c in _TANSHO_RENAME.values() if c in df_t.columns]].copy()
    df_t["単勝票数"] = df_t["単勝票数"].apply(_convert_votes_value)
    df_t["単勝票数人気"] = df_t["単勝票数人気"].apply(_convert_ninki_value)

    df_f = raw_fukusho.rename(columns=_FUKUSHO_RENAME)
    df_f = df_f[[c for c in _FUKUSHO_RENAME.values() if c in df_f.columns]].copy()
    df_f["複勝票数"] = df_f["複勝票数"].apply(_convert_votes_value)
    df_f["複勝票数人気"] = df_f["複勝票数人気"].apply(_convert_ninki_value)

    result = df_t.merge(df_f, on="馬番", how="outer")
    # 登録なし（票数がともに欠損）の行は除く
    result = result[result["単勝票数"].notna() | result["複勝票数"].notna()]

    totals = raw_odds1.iloc[0]
    for source, column in _TOTAL_RENAME.items():
        result[column] = _convert_votes_value(totals[source])

    result = ensure_columns(result, WIN_SHOW_VOTES_COLUMNS)
    result = apply_types(result, VOTES_TYPES)
    result["馬番"] = result["馬番"].astype("Int64")
    return result.sort_values("馬番").reset_index(drop=True)


def _convert_votes_value(value: Any) -> Any:
    """票数文字列を整数に変換する（数値以外・NAはpd.NAを返す。ALL0は0）."""
    if pd.isna(value) or not str(value).strip().isdigit():
        return pd.NA
    return int(value)


def _convert_ninki_value(value: Any) -> Any:
    """人気順文字列を整数に変換する（数値以外・NAはpd.NAを返す）."""
    if pd.isna(value) or not str(value).strip().isdigit():
        return pd.NA
    return int(value)
