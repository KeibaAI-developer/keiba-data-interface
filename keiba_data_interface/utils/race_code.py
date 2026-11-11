"""レースコード変換ユーティリティ.

16桁レースコード（JRA-VAN式）からnetkeibaの12桁レースIDへの変換を提供する。

16桁レースコード構造:
    年(4) + 月日(4) + 競馬場(2) + 回(2) + 日目(2) + R(2)
    例: 2025050206021211

12桁レースID構造:
    年(4) + 競馬場(2) + 回(2) + 日目(2) + R(2)
    例: 202506021211

"""

from keiba_domain import validate_race_code


def race_code_to_race_id(race_code: str) -> str:
    """16桁レースコードを12桁レースIDに変換する.

    月日部分（5〜8桁目）を除去して12桁のレースIDに変換する。

    Args:
        race_code (str): 16桁レースコード

    Returns:
        str: 12桁レースID

    Raises:
        KeibaDomainError: レースコードが半角数字16桁でない場合
    """
    validate_race_code(race_code)
    return race_code[:4] + race_code[8:]
