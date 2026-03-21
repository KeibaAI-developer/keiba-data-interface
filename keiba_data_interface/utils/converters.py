"""データ変換ユーティリティ.

mykeibadb/scrapingの生値を統一スキーマの表示形式に変換する関数を提供する。
"""


def convert_time_msss_to_display(value: str) -> str:
    """走破タイムをMSSS形式から表示形式に変換する.

    Args:
        value (str): MSSS形式の走破タイム（例: "2315"）

    Returns:
        str: "M:SS.S"形式の走破タイム（例: "2:31.5"）

    Raises:
        TypeError: 入力が文字列でない場合（NaN、pd.NA等）
        ValueError: 入力が空文字列、数値文字列でない場合、または桁数が不正な場合
    """
    if not isinstance(value, str):
        raise TypeError(f"走破タイムは文字列である必要があります: {type(value).__name__}")
    if not value:
        raise ValueError("走破タイムに空文字列は指定できません")
    if not value.isdigit():
        raise ValueError(f"走破タイムは数字のみで構成される必要があります: {value}")
    if len(value) < 3 or len(value) > 4:
        raise ValueError(f"走破タイムは3〜4桁である必要があります: {value} (長さ: {len(value)})")
    minutes = int(value[:-3]) if len(value) == 4 else 0
    seconds_tenths = value[-3:]
    seconds = int(seconds_tenths[:2])
    tenths = int(seconds_tenths[2])
    return f"{minutes}:{seconds:02d}.{tenths}"


def convert_hhmm_to_display(value: str) -> str:
    """発走時刻をHHMM形式から表示形式に変換する.

    Args:
        value (str): HHMM形式の発走時刻（例: "1540"）

    Returns:
        str: "HH:MM"形式の発走時刻（例: "15:40"）

    Raises:
        TypeError: 入力が文字列でない場合（NaN、pd.NA等）
        ValueError: 入力が空文字列、数値文字列でない場合、または4桁でない場合
    """
    if not isinstance(value, str):
        raise TypeError(f"発走時刻は文字列である必要があります: {type(value).__name__}")
    if not value:
        raise ValueError("発走時刻に空文字列は指定できません")
    if not value.isdigit():
        raise ValueError(f"発走時刻は数字のみで構成される必要があります: {value}")
    if len(value) != 4:
        raise ValueError(f"発走時刻は4桁である必要があります: {value} (長さ: {len(value)})")
    return f"{value[:2]}:{value[2:]}"


def convert_tenth_to_unit(value: int, unit: float) -> float:
    """0.1単位の整数値を実単位に変換する.

    負担重量、オッズ、ハロンタイム等の0.1単位整数値を実数に変換する。

    Args:
        value (int): 0.1単位の整数値（例: 560）
        unit (float): 変換単位（例: 0.1）

    Returns:
        float: 実単位の値（例: 56.0）
    """
    return round(value * unit, 1)


def convert_manyen_to_hyakuyen(value: int) -> int:
    """万円単位を百円単位に変換する.

    賞金の万円単位を百円単位に変換する。

    Args:
        value (int): 万円単位の値（例: 1000）

    Returns:
        int: 百円単位の値（例: 100000）
    """
    return value * 100


def split_zogen(value: int) -> tuple[str, int]:
    """増減値を増減符号と増減差に分離する.

    符号付き整数を増減符号文字列と増減差（絶対値）に分離する。

    Args:
        value (int): 増減値（例: 2, -4, 0）

    Returns:
        str: 増減符号（"+", "-", " "）
        int: 増減差（絶対値）
    """
    if value > 0:
        return "+", value
    elif value < 0:
        return "-", abs(value)
    else:
        return " ", 0
