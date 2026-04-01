"""scraping変換で共有されるヘルパー関数と定数."""

import re

import pandas as pd

from keiba_data_interface.utils.converters import convert_manyen_to_hyakuyen, split_zogen
from keiba_data_interface.utils.race_code import keibajo_code_to_name

# 異常区分変換マッピング（scraping出力 → JRA-VANコード）
# 降着(7)は着差テキストのパターン検出で判定するため別処理
IJO_KUBUN_TO_CODE: dict[str, str] = {
    "出走": "0",
    "取消": "1",
    "除外": "3",
    "中止": "4",
    "失格": "5",
}

# 出走区分 → 異常区分コード変換マッピング（get_entry用: JRA-VANコード）
# レース前に確定できるもののみ: 出走=0, 出走取消=1, 競走除外=3
SHUTSUSO_TO_IJO_CODE: dict[str, str] = {
    "出走": "0",
    "取消": "1",
    "除外": "3",
}

# 性別文字列 → 性別コード変換マッピング（scraping出力 → JRA-VANコード）
SEIBETSU_TO_CODE: dict[str, str] = {
    "牡": "1",
    "牝": "2",
    "セ": "3",
}

# 所属文字列 → 東西所属コード変換マッピング（scraping出力 → JRA-VANコード）
TOZAI_SHOZOKU_TO_CODE: dict[str, str] = {
    "美浦": "1",
    "栗東": "2",
    "地方": "3",
    "海外": "4",
}


def build_prize_map(raw_race_info: pd.DataFrame) -> dict[int, int]:
    """レース情報から着順→獲得本賞金(百円単位)のマッピングを構築する.

    Args:
        raw_race_info (pd.DataFrame): EntryPageScraper.get_race_info()の出力

    Returns:
        dict[int, int]: 着順をキー、獲得本賞金(百円単位)を値とするマッピング
    """
    prize_map: dict[int, int] = {}
    if len(raw_race_info) == 0:
        return prize_map
    row = raw_race_info.iloc[0]
    for i in range(1, 6):
        col = f"{i}着賞金"
        if col in row.index and pd.notna(row[col]):
            prize_map[i] = convert_manyen_to_hyakuyen(int(row[col]))
    return prize_map


def set_header_columns(converted: dict[str, object], race_code: str, parts: dict[str, str]) -> None:
    """レースコードからヘッダカラムを設定する.

    Args:
        converted (dict[str, object]): 変換先の辞書（この辞書にヘッダカラムを追加する）
        race_code (str): 16桁レースコード
        parts (dict[str, str]): extract_race_code_parts()の戻り値
    """
    converted["レースコード"] = race_code
    converted["開催年"] = parts["年"]
    converted["開催月日"] = parts["月日"]
    converted["競馬場"] = keibajo_code_to_name(parts["競馬場"])
    converted["開催回"] = int(parts["回"])
    converted["開催日目"] = int(parts["日目"])
    converted["レース番号"] = int(parts["R"])


def set_zogen(converted: dict[str, object], zogen: int | float | None) -> None:
    """増減符号と増減差を設定する.

    Args:
        converted (dict[str, object]): 変換先の辞書（この辞書に増減符号・増減差を追加する）
        zogen (int | float | None): 増減値。NaNまたはNoneの場合は何も設定しない
    """
    if pd.notna(zogen):
        fugo, sa = split_zogen(int(zogen))
        converted["増減符号"] = fugo
        converted["増減差"] = sa


def set_ijo_kubun(
    converted: dict[str, object],
    ijo_kubun: str | None,
    chakusa: str | None,
) -> bool:
    """異常区分コードを設定し、降着かどうかを返す.

    Args:
        converted (dict[str, object]): 変換先の辞書（この辞書に異常区分コードを追加する）
        ijo_kubun (str | None): scraping出力の異常区分
        chakusa (str | None): scraping出力の着差（降着判定に使用）

    Returns:
        bool: 降着の場合True
    """
    is_kokaku = (
        pd.notna(chakusa)
        and isinstance(chakusa, str)
        and re.search(r"\d+位降着", chakusa) is not None
    )
    if is_kokaku:
        converted["異常区分コード"] = "7"
    elif pd.notna(ijo_kubun) and str(ijo_kubun) in IJO_KUBUN_TO_CODE:
        converted["異常区分コード"] = IJO_KUBUN_TO_CODE[str(ijo_kubun)]
    elif pd.notna(ijo_kubun) and str(ijo_kubun):
        converted["異常区分コード"] = str(ijo_kubun)
    else:
        converted["異常区分コード"] = "0"
    return is_kokaku


def parse_time_to_seconds(time_str: str) -> float:
    """走破タイム文字列("M:SS.S")を秒に変換する.

    Args:
        time_str (str): "M:SS.S"形式の走破タイム

    Returns:
        float: 秒単位の走破タイム

    Raises:
        ValueError: 走破タイム形式が不正な場合
    """
    m = re.match(r"(\d+):(\d+)\.(\d)", time_str)
    if not m:
        raise ValueError(f"走破タイム形式が不正です: {time_str}")
    minutes = int(m.group(1))
    seconds = int(m.group(2))
    tenths = int(m.group(3))
    return minutes * 60 + seconds + tenths / 10
