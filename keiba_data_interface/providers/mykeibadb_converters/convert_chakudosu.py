"""get_chakudosu用の変換関数.

SHUSSOBETSU_KEIBAJO / SHUSSOBETSU_KYORI / SHUSSOBETSU_BABAテーブルの出力を
血統登録番号で結合し、統一スキーマに変換する。
"""

import pandas as pd

from keiba_data_interface.schema.columns import CHAKUDOSU_COLUMNS
from keiba_data_interface.schema.types import CHAKUDOSU_TYPES
from keiba_data_interface.utils.dataframe import apply_types, ensure_columns

_KEY_COLUMN_MAP: dict[str, str] = {
    "race_code": "レースコード",
    "ketto_toroku_bango": "血統登録番号",
    "bamei": "馬名",
}

_KEIBAJO_ROMAJI_TO_NAME: dict[str, str] = {
    "sapporo": "札幌",
    "hakodate": "函館",
    "fukushima": "福島",
    "niigata": "新潟",
    "tokyo": "東京",
    "nakayama": "中山",
    "chukyo": "中京",
    "kyoto": "京都",
    "hanshin": "阪神",
    "kokura": "小倉",
}

_SURFACE_ROMAJI_TO_NAME: dict[str, str] = {
    "shiba": "芝",
    "dirt": "ダ",
    "shogai": "障",
}

_CHAKU_ROMAJI_TO_NAME: dict[str, str] = {
    "1chaku": "1着",
    "2chaku": "2着",
    "3chaku": "3着",
    "4chaku": "4着",
    "5chaku": "5着",
    "chakugai": "着外",
}

_KYORI_ROMAJI_TO_NAME: dict[str, str] = {
    "1200_ika": "1200以下",
    "1201_1400": "1201-1400",
    "1401_1600": "1401-1600",
    "1601_1800": "1601-1800",
    "1801_2000": "1801-2000",
    "2001_2200": "2001-2200",
    "2201_2400": "2201-2400",
    "2401_2800": "2401-2800",
    "2801_ijo": "2801以上",
}

_MAWARI_ROMAJI_TO_NAME: dict[str, str] = {
    "choku": "直",
    "migi": "右",
    "hidari": "左",
}

_BABA_JOTAI_ROMAJI_TO_NAME: dict[str, str] = {
    "ryo": "良",
    "yayaomo": "稍",
    "omo": "重",
    "furyo": "不",
}


def _build_keibajo_column_map() -> dict[str, str]:
    """SHUSSOBETSU_KEIBAJOの着回数カラム名マップを生成する."""
    col_map: dict[str, str] = {}
    for keibajo_romaji, keibajo in _KEIBAJO_ROMAJI_TO_NAME.items():
        for surface_romaji, surface in _SURFACE_ROMAJI_TO_NAME.items():
            for chaku_romaji, chaku in _CHAKU_ROMAJI_TO_NAME.items():
                col_map[f"{keibajo_romaji}_{surface_romaji}_{chaku_romaji}"] = (
                    f"{keibajo}{surface}{chaku}"
                )
    return col_map


def _build_kyori_column_map() -> dict[str, str]:
    """SHUSSOBETSU_KYORIの着回数カラム名マップを生成する."""
    col_map: dict[str, str] = {}
    for surface_romaji in ("shiba", "dirt"):
        surface = _SURFACE_ROMAJI_TO_NAME[surface_romaji]
        for kyori_romaji, kyori in _KYORI_ROMAJI_TO_NAME.items():
            for chaku_romaji, chaku in _CHAKU_ROMAJI_TO_NAME.items():
                col_map[f"{surface_romaji}_{kyori_romaji}_{chaku_romaji}"] = (
                    f"{surface}{kyori}{chaku}"
                )
    return col_map


def _build_baba_column_map() -> dict[str, str]:
    """SHUSSOBETSU_BABAの着回数カラム名マップを生成する.

    馬場別（芝ダ×右左直 + 障害）と馬場状態別（芝ダ障×良稍重不）のマップを生成する。
    """
    col_map: dict[str, str] = {}
    for surface_romaji in ("shiba", "dirt"):
        surface = _SURFACE_ROMAJI_TO_NAME[surface_romaji]
        for mawari_romaji, mawari in _MAWARI_ROMAJI_TO_NAME.items():
            for chaku_romaji, chaku in _CHAKU_ROMAJI_TO_NAME.items():
                col_map[f"{surface_romaji}_{mawari_romaji}_{chaku_romaji}"] = (
                    f"{surface}{mawari}{chaku}"
                )
    for chaku_romaji, chaku in _CHAKU_ROMAJI_TO_NAME.items():
        col_map[f"shogai_{chaku_romaji}"] = f"障害{chaku}"
    for surface_romaji, surface in _SURFACE_ROMAJI_TO_NAME.items():
        for jotai_romaji, jotai in _BABA_JOTAI_ROMAJI_TO_NAME.items():
            for chaku_romaji, chaku in _CHAKU_ROMAJI_TO_NAME.items():
                col_map[f"{surface_romaji}_{jotai_romaji}_{chaku_romaji}"] = (
                    f"{surface}{jotai}{chaku}"
                )
    return col_map


_KEIBAJO_COLUMN_MAP: dict[str, str] = _build_keibajo_column_map()
_KYORI_COLUMN_MAP: dict[str, str] = _build_kyori_column_map()
_BABA_COLUMN_MAP: dict[str, str] = _build_baba_column_map()


def _extract_part(raw: pd.DataFrame, col_map: dict[str, str]) -> pd.DataFrame:
    """rawデータからキーカラムと着回数カラムを抽出して日本語カラム名に変換する.

    Args:
        raw (pd.DataFrame): SHUSSOBETSUテーブルの出力（convert_codes=False）
        col_map (dict[str, str]): 着回数カラム名マップ

    Returns:
        pd.DataFrame: 日本語カラム名に変換されたDataFrame
    """
    rename_map = {**_KEY_COLUMN_MAP, **col_map}
    df = raw.rename(columns=rename_map)
    keep = [col for col in rename_map.values() if col in df.columns]
    return df[keep]


def convert_chakudosu(
    raw_keibajo: pd.DataFrame,
    raw_kyori: pd.DataFrame,
    raw_baba: pd.DataFrame,
) -> pd.DataFrame:
    """SHUSSOBETSU 3テーブルの出力を統一スキーマに変換する.

    3テーブルを血統登録番号で外部結合する。一部のテーブルにのみ存在する馬も
    行として保持する（欠損した着回数カラムはNaN）。

    Args:
        raw_keibajo (pd.DataFrame): ShussobetsuGetter.get_shussobetsu_keibajo()の出力
            （convert_codes=False）
        raw_kyori (pd.DataFrame): ShussobetsuGetter.get_shussobetsu_kyori()の出力
            （convert_codes=False）
        raw_baba (pd.DataFrame): ShussobetsuGetter.get_shussobetsu_baba()の出力
            （convert_codes=False）

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame（CHAKUDOSU_COLUMNSのカラム、
            出走頭数分の行）
    """
    parts = [
        _extract_part(raw, col_map)
        for raw, col_map in (
            (raw_keibajo, _KEIBAJO_COLUMN_MAP),
            (raw_kyori, _KYORI_COLUMN_MAP),
            (raw_baba, _BABA_COLUMN_MAP),
        )
        if not raw.empty
    ]
    if not parts:
        return apply_types(ensure_columns(pd.DataFrame(), CHAKUDOSU_COLUMNS), CHAKUDOSU_TYPES)

    key_cols = list(_KEY_COLUMN_MAP.values())
    base = (
        pd.concat([part[key_cols] for part in parts])
        .drop_duplicates("血統登録番号")
        .set_index("血統登録番号")
    )
    merged = base
    for part in parts:
        value_cols = [col for col in part.columns if col not in key_cols]
        merged = merged.join(part.set_index("血統登録番号")[value_cols], how="left")
    df = merged.reset_index()
    return apply_types(ensure_columns(df, CHAKUDOSU_COLUMNS), CHAKUDOSU_TYPES)
