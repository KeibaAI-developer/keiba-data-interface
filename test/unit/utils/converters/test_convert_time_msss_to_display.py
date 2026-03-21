"""convert_time_msss_to_display関数のテスト."""

import pandas as pd
import pytest

from keiba_data_interface.utils.converters import convert_time_msss_to_display


# 正常系
@pytest.mark.parametrize(
    "value, expected",
    [
        ("2315", "2:31.5"),
        ("1000", "1:00.0"),
        ("1599", "1:59.9"),
        ("0590", "0:59.0"),
        ("590", "0:59.0"),
    ],
)
def test_convert_time_msss_to_display_normal(value: str, expected: str) -> None:
    """MSSS形式の走破タイムを正しく表示形式に変換できる."""
    assert convert_time_msss_to_display(value) == expected


def test_convert_time_msss_to_display_3digit() -> None:
    """3桁（分が0）の走破タイムを正しく変換できる."""
    assert convert_time_msss_to_display("315") == "0:31.5"


# 準正常系
def test_convert_time_msss_to_display_non_digit() -> None:
    """数値以外の文字列でValueErrorが発生する."""
    with pytest.raises(ValueError, match="数字のみ"):
        convert_time_msss_to_display("ab15")


def test_convert_time_msss_to_display_too_short() -> None:
    """2桁の入力でValueErrorが発生する."""
    with pytest.raises(ValueError, match="3〜4桁"):
        convert_time_msss_to_display("15")


def test_convert_time_msss_to_display_too_long() -> None:
    """5桁の入力でValueErrorが発生する."""
    with pytest.raises(ValueError, match="3〜4桁"):
        convert_time_msss_to_display("12345")


def test_convert_time_msss_to_display_empty_string() -> None:
    """空文字列でValueErrorが発生する."""
    with pytest.raises(ValueError, match="空文字列"):
        convert_time_msss_to_display("")


@pytest.mark.parametrize(
    "nan_value",
    [
        float("nan"),
        pd.NA,
        None,
    ],
)
def test_convert_time_msss_to_display_nan_values(nan_value: object) -> None:
    """NaN系欠損値でTypeErrorが発生する."""
    with pytest.raises(TypeError, match="文字列"):
        convert_time_msss_to_display(nan_value)  # type: ignore[arg-type]
