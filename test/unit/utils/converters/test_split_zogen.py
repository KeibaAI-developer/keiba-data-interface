"""split_zogen関数のテスト."""

import pytest

from keiba_data_interface.utils.converters import split_zogen


# 正常系
@pytest.mark.parametrize(
    "value, expected_sign, expected_diff",
    [
        (2, "+", 2),
        (10, "+", 10),
        (-4, "-", 4),
        (-1, "-", 1),
        (0, "", 0),
    ],
)
def test_split_zogen_normal(value: int, expected_sign: str, expected_diff: int) -> None:
    """増減値を正しく符号と差に分離できる."""
    sign, diff = split_zogen(value)
    assert sign == expected_sign
    assert diff == expected_diff
