"""convert_hhmm_to_display関数のテスト."""

import pandas as pd
import pytest

from keiba_data_interface.utils.converters import convert_hhmm_to_display


# 正常系
@pytest.mark.parametrize(
    "value, expected",
    [
        ("1540", "15:40"),
        ("0900", "09:00"),
        ("1200", "12:00"),
        ("2359", "23:59"),
        ("0000", "00:00"),
    ],
)
def test_convert_hhmm_to_display_normal(value: str, expected: str) -> None:
    """HHMM形式の発走時刻を正しく表示形式に変換できる."""
    assert convert_hhmm_to_display(value) == expected


# 準正常系
def test_convert_hhmm_to_display_non_digit() -> None:
    """数値以外の文字列でValueErrorが発生する."""
    with pytest.raises(ValueError, match="数字のみ"):
        convert_hhmm_to_display("15:4")


def test_convert_hhmm_to_display_too_short() -> None:
    """3桁の入力でValueErrorが発生する."""
    with pytest.raises(ValueError, match="4桁"):
        convert_hhmm_to_display("154")


def test_convert_hhmm_to_display_too_long() -> None:
    """5桁の入力でValueErrorが発生する."""
    with pytest.raises(ValueError, match="4桁"):
        convert_hhmm_to_display("15400")


def test_convert_hhmm_to_display_empty_string() -> None:
    """空文字列でValueErrorが発生する."""
    with pytest.raises(ValueError, match="空文字列"):
        convert_hhmm_to_display("")


@pytest.mark.parametrize(
    "nan_value",
    [
        float("nan"),
        pd.NA,
        None,
    ],
)
def test_convert_hhmm_to_display_nan_values(nan_value: object) -> None:
    """NaN系欠損値でTypeErrorが発生する."""
    with pytest.raises(TypeError, match="文字列"):
        convert_hhmm_to_display(nan_value)  # type: ignore[arg-type]
