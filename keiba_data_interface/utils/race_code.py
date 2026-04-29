"""レースコード変換ユーティリティ.

16桁レースコード（JRA-VAN式）と12桁レースID（netkeiba式）の変換、
およびレースコードからの各要素抽出を提供する。

16桁レースコード構造:
    年(4) + 月日(4) + 競馬場(2) + 回(2) + 日目(2) + R(2)
    例: 2025050206021211

12桁レースID構造:
    年(4) + 競馬場(2) + 回(2) + 日目(2) + R(2)
    例: 202506021211

"""

from keiba_data_interface.exceptions import RaceCodeError

# 競馬場コード → 競馬場名マッピング
_KEIBAJO_CODE_TO_NAME: dict[str, str] = {
    "01": "札幌",
    "02": "函館",
    "03": "福島",
    "04": "新潟",
    "05": "東京",
    "06": "中山",
    "07": "中京",
    "08": "京都",
    "09": "阪神",
    "10": "小倉",
}


def keibajo_code_to_name(code: str) -> str:
    """競馬場コード（2桁）を競馬場名に変換する.

    Args:
        code (str): 競馬場コード（2桁、例: "06"）

    Returns:
        str: 競馬場名（例: "中山"）

    Raises:
        RaceCodeError: 未知の競馬場コードの場合
    """
    name = _KEIBAJO_CODE_TO_NAME.get(code)
    if name is None:
        raise RaceCodeError(f"未知の競馬場コードです: {code}")
    return name


# 競馬場名 → 競馬場コードマッピング（逆引き）
_KEIBAJO_NAME_TO_CODE: dict[str, str] = {v: k for k, v in _KEIBAJO_CODE_TO_NAME.items()}


def keibajo_name_to_code(name: str) -> str:
    """競馬場名を競馬場コード（2桁）に変換する.

    Args:
        name (str): 競馬場名（例: "中山"）

    Returns:
        str: 競馬場コード（2桁、例: "06"）

    Raises:
        RaceCodeError: 未知の競馬場名の場合
    """
    code = _KEIBAJO_NAME_TO_CODE.get(name)
    if code is None:
        raise RaceCodeError(f"未知の競馬場名です: {name}")
    return code


def race_code_to_race_id(race_code: str) -> str:
    """16桁レースコードを12桁レースIDに変換する.

    月日部分（5〜8桁目）を除去して12桁のレースIDに変換する。

    Args:
        race_code (str): 16桁レースコード

    Returns:
        str: 12桁レースID

    Raises:
        RaceCodeError: レースコードの形式が不正な場合
    """
    _validate_race_code(race_code)
    return race_code[:4] + race_code[8:]


def extract_race_code_parts(race_code: str) -> dict[str, str]:
    """レースコードから各要素を抽出する.

    Args:
        race_code (str): 16桁レースコード

    Returns:
        dict[str, str]: 各要素を含む辞書
            - 年: 開催年（4桁）
            - 月日: 開催月日（4桁）
            - 競馬場コード: 競馬場コード（2桁）
            - 回: 開催回（2桁）
            - 日目: 開催日目（2桁）
            - R: レース番号（2桁）

    Raises:
        RaceCodeError: レースコードの形式が不正な場合
    """
    _validate_race_code(race_code)
    return {
        "年": race_code[0:4],
        "月日": race_code[4:8],
        "競馬場コード": race_code[8:10],
        "回": race_code[10:12],
        "日目": race_code[12:14],
        "R": race_code[14:16],
    }


def _validate_race_code(race_code: str) -> None:
    """16桁レースコードのバリデーション.

    Args:
        race_code (str): 16桁レースコード

    Raises:
        RaceCodeError: 桁数が16桁でない場合、または数値以外の文字が含まれる場合
    """
    if len(race_code) != 16:
        raise RaceCodeError(
            f"レースコードは16桁である必要があります: {race_code} (長さ: {len(race_code)})"
        )
    if not race_code.isdigit():
        raise RaceCodeError(f"レースコードは数字のみで構成される必要があります: {race_code}")
