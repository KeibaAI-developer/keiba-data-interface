"""convert_tenth_to_unit関数のテスト."""

import pytest

from keiba_data_interface.utils.converters import convert_tenth_to_unit


# 正常系
@pytest.mark.parametrize(
    "value, unit, expected",
    [
        (560, 0.1, 56.0),
        (38, 0.1, 3.8),
        (346, 0.1, 34.6),
        (122, 0.1, 12.2),
        (0, 0.1, 0.0),
    ],
)
def test_convert_tenth_to_unit_normal(value: int, unit: float, expected: float) -> None:
    """0.1単位の整数値を正しく実単位に変換できる."""
    assert convert_tenth_to_unit(value, unit) == expected


def test_convert_tenth_to_unit_negative() -> None:
    """負値を正しく変換できる."""
    assert convert_tenth_to_unit(-10, 0.1) == -1.0
