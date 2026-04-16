"""scraping変換で共有されるヘルパー関数と定数."""

import re

import pandas as pd

from keiba_data_interface.utils.converters import convert_manyen_to_hyakuyen, split_zogen

# 異常区分変換マッピング（scraping出力 → JRA-VANコード）
# 降着(7)は着差テキストのパターン検出で判定するため別処理
IJO_KUBUN_TO_CODE: dict[str, str] = {
    "出走": "0",
    "取消": "1",
    "除外": "3",
    "中止": "4",
    "失格": "5",
    "降着": "7",
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

# グレード文字列 → グレードコード変換マッピング（scraping出力 → JRA-VANコード）
# CODE_TABLE.md GRADE_CODE を参照
GRADE_TO_CODE: dict[str, str] = {
    "G1": "A",  # GI（平地競走）
    "G2": "B",  # GII（平地競走）
    "G3": "C",  # GIII（平地競走）
    "JG1": "F",  # J・GI（障害競走）
    "JG2": "G",  # J・GII（障害競走）
    "JG3": "H",  # J・GIII（障害競走）
    "L": "L",  # リステッド
    "OP": "E",  # 特別競走（重賞以外の特別競走）
    "": "_",  # 一般競走
}

# 馬場状態文字列 → 馬場状態コード変換マッピング（scraping出力 → JRA-VANコード）
# CODE_TABLE.md BABAJOTAI_CODE を参照
BABAJOTAI_TO_CODE: dict[str, str] = {
    "良": "1",
    "稍": "2",  # 稍重
    "重": "3",
    "不": "4",  # 不良
}
# 曜日文字列 → 曜日コード変換マッピング（scraping出力 → JRA-VANコード）
# CODE_TABLE.md YOBI_CODE を参照
YOBI_TO_CODE: dict[str, str] = {
    "土": "1",
    "日": "2",
    "祝": "3",
    "月": "4",
    "火": "5",
    "水": "6",
    "木": "7",
    "金": "8",
}

# 重量種別文字列 → 重量種別コード変換マッピング（scraping出力 → JRA-VANコード）
# CODE_TABLE.md JURYO_SHUBETSU_CODE を参照
JURYO_SHUBETSU_TO_CODE: dict[str, str] = {
    "ハンデ": "1",
    "別定": "2",
    "馬齢": "3",
    "定量": "4",
}

# 天候文字列 → 天候コード変換マッピング（scraping出力 → JRA-VANコード）
# CODE_TABLE.md TENKO_CODE を参照
TENKO_TO_CODE: dict[str, str] = {
    "晴": "1",
    "曇": "2",
    "雨": "3",
    "小雨": "4",
    "雪": "5",
    "小雪": "6",
}

# investigate_kyoso_kigo.py の調査結果に基づく
KYOSO_KIGO_TO_CODE: dict[str, str] = {
    "": "000",  # 記号なし
    # 性別制限なし (第1バイト=0)
    "(指)": "001",
    "[指]": "003",
    "(特指)": "004",
    # 牝 (第2バイト=2)
    "牝(指)": "021",
    "牝[指]": "023",
    "牝(特指)": "024",
    # 牡・牝 (第2バイト=4)
    "牡・牝(指)": "041",
    # (混合) (第1バイト=A)
    "(混)(指)": "A01",
    "(混)・見習騎手": "A02",
    "(混)[指]": "A03",
    "(混)(特指)": "A04",
    "(混) 牝": "A20",
    "(混) 牝(指)": "A21",
    "(混) 牝[指]": "A23",
    "(混) 牝(特指)": "A24",
    "(混) 牡・牝(指)": "A41",
    # (父) (第1バイト=B)
    "(父)[指]": "B03",
    "(父)(特指)": "B04",
    # (市) (第1バイト=C)
    "(市)[指]": "C03",
    # 九州産馬 (第1バイト=M)
    "九州産馬(指)": "M01",
    "九州産馬[指]": "M03",
    # (国際) (第1バイト=N)
    "(国際)": "N00",
    "(国際)(指)": "N01",
    "(国際)[指]": "N03",
    "(国際)(特指)": "N04",
    "(国際) 牝": "N20",
    "(国際) 牝(指)": "N21",
    "(国際) 牝[指]": "N23",
    "(国際) 牝(特指)": "N24",
    "(国際) 牡・牝": "N44",  # netkeibaでは(特指)が省略される
    "(国際) 牡・牝(指)": "N41",
}

# 競走種別文字列 → 競走種別コード変換マッピング（scraping出力 → JRA-VANコード）
# CODE_TABLE.md KYOSO_SHUBETSU_CODE を参照
KYOSO_SHUBETSU_TO_CODE: dict[str, str] = {
    "サラ系２歳": "11",
    "サラ系３歳": "12",
    "サラ系３歳以上": "13",
    "サラ系４歳以上": "14",
    "障害３歳以上": "18",
    "障害４歳以上": "19",
}

# 所属文字列 → 東西所属コード変換マッピング（scraping出力 → JRA-VANコード）
TOZAI_SHOZOKU_TO_CODE: dict[str, str] = {
    "美浦": "1",
    "栗東": "2",
    "地方": "3",
    "海外": "4",
}

# scraping着差文字列 → 着差コード変換マッピング
# 着差コード: 1バイト目=整数部(数字/英字), 2バイト目=分子, 3バイト目=分母, 未使用の桁はアンダーバー
CHAKUSA_TO_CODE: dict[str, str] = {
    "1/2": "_12",
    "3/4": "_34",
    "1": "1__",
    "1.1/2": "112",
    "1.1/4": "114",
    "1.3/4": "134",
    "2": "2__",
    "2.1/2": "212",
    "3": "3__",
    "3.1/2": "312",
    "4": "4__",
    "5": "5__",
    "6": "6__",
    "7": "7__",
    "8": "8__",
    "9": "9__",
    "10": "Z__",
    "アタマ": "A__",
    "同着": "D__",
    "ハナ": "H__",
    "クビ": "K__",
    "大": "T__",
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
    converted["競馬場コード"] = parts["競馬場コード"]
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
        if fugo is not None:
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


def convert_chakusa_to_code(chakusa: str) -> str:
    """scraping出力の着差文字列を着差コードに変換する.

    CHAKUSA_TO_CODEマッピングに該当しない場合は元の値をそのまま返す。

    Args:
        chakusa (str): scraping出力の着差文字列（例: '1/2', '1.1/4', 'クビ', '大'）

    Returns:
        str: 着差コード（例: '_12', '114', 'K__', 'T__'）
    """
    return CHAKUSA_TO_CODE.get(chakusa, chakusa)
