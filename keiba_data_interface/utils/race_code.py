"""レースコード変換ユーティリティ.

16桁レースコード（JRA-VAN式）と12桁レースID（netkeiba式）の相互変換、
およびレースコードからの各要素抽出を提供する。

16桁レースコード構造:
    年(4) + 月日(4) + 競馬場(2) + 回(2) + 日目(2) + R(2)
    例: 2025050206021211

12桁レースID構造:
    年(4) + 競馬場(2) + 回(2) + 日目(2) + R(2)
    例: 202506021211

14桁開催コード構造:
    年(4) + 月日(4) + 競馬場(2) + 回(2) + 日目(2)
    例: 20250502060212
"""

from keiba_data_interface.exceptions import RaceCodeError


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


def race_code_to_kaisai_code(race_code: str) -> str:
    """16桁レースコードから開催コードを導出する.

    レース番号部分（末尾2桁）を除去して14桁の開催コードに変換する。

    Args:
        race_code (str): 16桁レースコード

    Returns:
        str: 14桁開催コード

    Raises:
        RaceCodeError: レースコードの形式が不正な場合
    """
    _validate_race_code(race_code)
    return race_code[:14]


def extract_race_code_parts(race_code: str) -> dict[str, str]:
    """レースコードから各要素を抽出する.

    Args:
        race_code (str): 16桁レースコード

    Returns:
        dict[str, str]: 各要素を含む辞書
            - 年: 開催年（4桁）
            - 月日: 開催月日（4桁）
            - 競馬場: 競馬場コード（2桁）
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
        "競馬場": race_code[8:10],
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
