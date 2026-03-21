"""convert_manyen_to_hyakuyen関数のテスト."""

import pytest

from keiba_data_interface.utils.converters import convert_manyen_to_hyakuyen


# 正常系
@pytest.mark.parametrize(
    "value, expected",
    [
        (1000, 100000),
        (500, 50000),
        (1, 100),
        (0, 0),
    ],
)
def test_convert_manyen_to_hyakuyen_normal(value: int, expected: int) -> None:
    """万円単位を正しく百円単位に変換できる."""
    assert convert_manyen_to_hyakuyen(value) == expected
