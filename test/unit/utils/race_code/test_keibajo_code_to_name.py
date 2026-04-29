"""keibajo_code_to_name関数のテスト."""

import pytest

from keiba_data_interface.utils.race_code import RaceCodeError, keibajo_code_to_name


# 正常系
@pytest.mark.parametrize(
    "code, expected",
    [
        ("01", "札幌"),
        ("02", "函館"),
        ("03", "福島"),
        ("04", "新潟"),
        ("05", "東京"),
        ("06", "中山"),
        ("07", "中京"),
        ("08", "京都"),
        ("09", "阪神"),
        ("10", "小倉"),
    ],
)
def test_keibajo_code_to_name_normal(code: str, expected: str) -> None:
    """全10場の競馬場コードが正しく競馬場名に変換される."""
    assert keibajo_code_to_name(code) == expected


# 準正常系
def test_unknown_code_raises_race_code_error() -> None:
    """未知の競馬場コードでRaceCodeErrorが発生する."""
    with pytest.raises(RaceCodeError, match="未知の競馬場コード"):
        keibajo_code_to_name("99")
