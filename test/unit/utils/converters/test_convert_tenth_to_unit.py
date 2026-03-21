"""convert_tenth_to_unit関数のテスト."""

from keiba_data_interface.utils.converters import convert_tenth_to_unit


# 正常系
def test_convert_tenth_to_unit_normal_560() -> None:
    """560を0.1単位で56.0に変換できる."""
    assert convert_tenth_to_unit(560) == 56.0


def test_convert_tenth_to_unit_normal_38() -> None:
    """38を0.1単位で3.8に変換できる."""
    assert convert_tenth_to_unit(38) == 3.8


def test_convert_tenth_to_unit_normal_346() -> None:
    """346を0.1単位で34.6に変換できる."""
    assert convert_tenth_to_unit(346) == 34.6


def test_convert_tenth_to_unit_zero() -> None:
    """0を0.0に変換できる."""
    assert convert_tenth_to_unit(0) == 0.0


def test_convert_tenth_to_unit_negative() -> None:
    """負値を正しく変換できる."""
    assert convert_tenth_to_unit(-10) == -1.0
