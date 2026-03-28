"""get_payoff用の変換関数.

HARAIMODOSHIテーブルの出力を統一スキーマに変換する。
"""

import pandas as pd

from keiba_data_interface.schema.columns import PAYOFF_COLUMNS
from keiba_data_interface.schema.types import PAYOFF_TYPES
from keiba_data_interface.utils.dataframe import apply_types, ensure_columns

# HARAIMODOSHI → 払戻情報の基本カラムリネームマッピング
_BASE_PAYOFF_RENAME: dict[str, str] = {
    "race_code": "レースコード",
    "kaisai_nen": "開催年",
    "kaisai_gappi": "開催月日",
    "keibajo": "競馬場",
    "kaisai_kaiji": "開催回",
    "kaisai_nichiji": "開催日目",
    "race_bango": "レース番号",
    "toroku_tosu": "登録頭数",
    "shusso_tosu": "出走頭数",
}

# 不成立フラグのマッピング
_FUSEIRITSU_MAP: dict[str, str] = {
    "fuseiritsu_flag_tansho": "不成立フラグ単勝",
    "fuseiritsu_flag_fukusho": "不成立フラグ複勝",
    "fuseiritsu_flag_wakuren": "不成立フラグ枠連",
    "fuseiritsu_flag_umaren": "不成立フラグ馬連",
    "fuseiritsu_flag_wide": "不成立フラグワイド",
    "fuseiritsu_flag_umatan": "不成立フラグ馬単",
    "fuseiritsu_flag_sanrenpuku": "不成立フラグ3連複",
    "fuseiritsu_flag_sanrentan": "不成立フラグ3連単",
}

# 特払フラグのマッピング
_TOKUBARAI_MAP: dict[str, str] = {
    "tokubarai_flag_tansho": "特払フラグ単勝",
    "tokubarai_flag_fukusho": "特払フラグ複勝",
    "tokubarai_flag_wakuren": "特払フラグ枠連",
    "tokubarai_flag_umaren": "特払フラグ馬連",
    "tokubarai_flag_wide": "特払フラグワイド",
    "tokubarai_flag_umatan": "特払フラグ馬単",
    "tokubarai_flag_sanrenpuku": "特払フラグ3連複",
    "tokubarai_flag_sanrentan": "特払フラグ3連単",
}

# 返還フラグのマッピング
_HENKAN_FLAG_MAP: dict[str, str] = {
    "henkan_flag_tansho": "返還フラグ単勝",
    "henkan_flag_fukusho": "返還フラグ複勝",
    "henkan_flag_wakuren": "返還フラグ枠連",
    "henkan_flag_umaren": "返還フラグ馬連",
    "henkan_flag_wide": "返還フラグワイド",
    "henkan_flag_umatan": "返還フラグ馬単",
    "henkan_flag_sanrenpuku": "返還フラグ3連複",
    "henkan_flag_sanrentan": "返還フラグ3連単",
}


def _build_payoff_rename() -> dict[str, str]:
    """払戻情報の完全なリネームマッピングを構築する."""
    rename = dict(_BASE_PAYOFF_RENAME)
    rename.update(_FUSEIRITSU_MAP)
    rename.update(_TOKUBARAI_MAP)
    rename.update(_HENKAN_FLAG_MAP)

    # 返還馬番情報1〜28
    for i in range(1, 29):
        rename[f"henkan_umaban_joho{i}"] = f"返還馬番情報{i}"

    # 返還枠番情報1〜8
    for i in range(1, 9):
        rename[f"henkan_wakuban_joho{i}"] = f"返還枠番情報{i}"

    # 返還同枠情報1〜8
    for i in range(1, 9):
        rename[f"henkan_dowaku_joho{i}"] = f"返還同枠情報{i}"

    # 単勝1〜3
    for i in range(1, 4):
        rename[f"tansho{i}_umaban"] = f"単勝{i}馬番"
        rename[f"tansho{i}_haraimodoshikin"] = f"単勝{i}払戻金"
        rename[f"tansho{i}_ninkijun"] = f"単勝{i}人気順"

    # 複勝1〜5
    for i in range(1, 6):
        rename[f"fukusho{i}_umaban"] = f"複勝{i}馬番"
        rename[f"fukusho{i}_haraimodoshikin"] = f"複勝{i}払戻金"
        rename[f"fukusho{i}_ninkijun"] = f"複勝{i}人気順"

    # 枠連1〜3
    for i in range(1, 4):
        rename[f"wakuren{i}_kumiban1"] = f"枠連{i}組番1"
        rename[f"wakuren{i}_kumiban2"] = f"枠連{i}組番2"
        rename[f"wakuren{i}_haraimodoshikin"] = f"枠連{i}払戻金"
        rename[f"wakuren{i}_ninkijun"] = f"枠連{i}人気順"

    # 馬連1〜3
    for i in range(1, 4):
        rename[f"umaren{i}_kumiban1"] = f"馬連{i}組番1"
        rename[f"umaren{i}_kumiban2"] = f"馬連{i}組番2"
        rename[f"umaren{i}_haraimodoshikin"] = f"馬連{i}払戻金"
        rename[f"umaren{i}_ninkijun"] = f"馬連{i}人気順"

    # ワイド1〜7
    for i in range(1, 8):
        rename[f"wide{i}_kumiban1"] = f"ワイド{i}組番1"
        rename[f"wide{i}_kumiban2"] = f"ワイド{i}組番2"
        rename[f"wide{i}_haraimodoshikin"] = f"ワイド{i}払戻金"
        rename[f"wide{i}_ninkijun"] = f"ワイド{i}人気順"

    # 馬単1〜6
    for i in range(1, 7):
        rename[f"umatan{i}_kumiban1"] = f"馬単{i}組番1"
        rename[f"umatan{i}_kumiban2"] = f"馬単{i}組番2"
        rename[f"umatan{i}_haraimodoshikin"] = f"馬単{i}払戻金"
        rename[f"umatan{i}_ninkijun"] = f"馬単{i}人気順"

    # 3連複1〜3
    for i in range(1, 4):
        rename[f"sanrenpuku{i}_kumiban1"] = f"3連複{i}組番1"
        rename[f"sanrenpuku{i}_kumiban2"] = f"3連複{i}組番2"
        rename[f"sanrenpuku{i}_kumiban3"] = f"3連複{i}組番3"
        rename[f"sanrenpuku{i}_haraimodoshikin"] = f"3連複{i}払戻金"
        rename[f"sanrenpuku{i}_ninkijun"] = f"3連複{i}人気順"

    # 3連単1〜6
    for i in range(1, 7):
        rename[f"sanrentan{i}_kumiban1"] = f"3連単{i}組番1"
        rename[f"sanrentan{i}_kumiban2"] = f"3連単{i}組番2"
        rename[f"sanrentan{i}_kumiban3"] = f"3連単{i}組番3"
        rename[f"sanrentan{i}_haraimodoshikin"] = f"3連単{i}払戻金"
        rename[f"sanrentan{i}_ninkijun"] = f"3連単{i}人気順"

    return rename


_PAYOFF_RENAME: dict[str, str] = _build_payoff_rename()


def convert_payoff(raw: pd.DataFrame) -> pd.DataFrame:
    """HARAIMODOSHIの出力を統一スキーマに変換する.

    Args:
        raw (pd.DataFrame): RaceGetter.get_haraimodoshi()の出力（convert_codes=True）

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame（PAYOFF_COLUMNSのカラム）

    Raises:
        ValueError: rawが0行または2行以上の場合
    """
    if len(raw) == 0:
        raise ValueError("get_haraimodoshi()が空のDataFrameを返しました")
    if len(raw) > 1:
        raise ValueError(
            f"get_haraimodoshi()は1行のDataFrameを返す必要がありますが、" f"{len(raw)}行返しました"
        )

    df = raw.rename(columns=_PAYOFF_RENAME)
    df = ensure_columns(df, PAYOFF_COLUMNS)
    df = apply_types(df, PAYOFF_TYPES)
    return df
