"""apply_types関数のテスト."""

import pandas as pd
import pytest

from keiba_data_interface.utils.dataframe import apply_types


# 正常系
def test_apply_types_int64() -> None:
    """Int64型への変換が正しく行われる."""
    df = pd.DataFrame({"A": [1, 2, 3]})
    result = apply_types(df, {"A": "Int64"})
    assert result["A"].dtype == pd.Int64Dtype()


def test_apply_types_float64() -> None:
    """Float64型への変換が正しく行われる."""
    df = pd.DataFrame({"A": [1, 2, 3]})
    result = apply_types(df, {"A": "Float64"})
    assert result["A"].dtype == pd.Float64Dtype()


def test_apply_types_object() -> None:
    """object型への変換が正しく行われる."""
    df = pd.DataFrame({"A": [1, 2, 3]})
    result = apply_types(df, {"A": "object"})
    assert result["A"].dtype == object


def test_apply_types_multiple_columns() -> None:
    """複数カラムの型変換が正しく行われる."""
    df = pd.DataFrame({"A": [1, 2], "B": ["x", "y"], "C": [1.5, 2.5]})
    result = apply_types(df, {"A": "Int64", "B": "object", "C": "Float64"})
    assert result["A"].dtype == pd.Int64Dtype()
    assert result["B"].dtype == object
    assert result["C"].dtype == pd.Float64Dtype()


def test_apply_types_missing_column_ignored() -> None:
    """型定義辞書にあるがDataFrameに存在しないカラムは無視される."""
    df = pd.DataFrame({"A": [1, 2]})
    result = apply_types(df, {"A": "Int64", "B": "Float64"})
    assert result["A"].dtype == pd.Int64Dtype()
    assert "B" not in result.columns


def test_apply_types_with_na() -> None:
    """NaN値を含むカラムのnullable Int64型への変換が正しく行われる."""
    df = pd.DataFrame({"A": [1, None, 3]})
    result = apply_types(df, {"A": "Int64"})
    assert result["A"].dtype == pd.Int64Dtype()
    assert pd.isna(result["A"].iloc[1])


def test_apply_types_does_not_modify_input() -> None:
    """入力DataFrameが変更されない."""
    df = pd.DataFrame({"A": [1, 2, 3]})
    original_dtype = df["A"].dtype
    apply_types(df, {"A": "Float64"})
    assert df["A"].dtype == original_dtype


# 空文字列・空白文字列・NAの変換挙動
@pytest.mark.parametrize(
    "value",
    ["", " ", "  \t"],
    ids=["empty_string", "single_space", "tab_and_spaces"],
)
def test_apply_types_whitespace_string_becomes_na_for_numeric(value: str) -> None:
    """数値型変換時に空文字列・空白のみ文字列はNAに変換される."""
    df = pd.DataFrame({"A": [value]})
    result = apply_types(df, {"A": "Int64"})
    assert result["A"].dtype == pd.Int64Dtype()
    assert pd.isna(result["A"].iloc[0])


@pytest.mark.parametrize(
    "value",
    ["", " ", "  \t"],
    ids=["empty_string", "single_space", "tab_and_spaces"],
)
def test_apply_types_whitespace_string_for_float_becomes_na(value: str) -> None:
    """Float64型変換時に空文字列・空白のみ文字列はNAに変換される."""
    df = pd.DataFrame({"A": [value]})
    result = apply_types(df, {"A": "Float64"})
    assert result["A"].dtype == pd.Float64Dtype()
    assert pd.isna(result["A"].iloc[0])


def test_apply_types_mixed_valid_and_whitespace_for_numeric() -> None:
    """数値と空文字列・空白が混在する場合、空文字列・空白はNAになり数値は保持される."""
    df = pd.DataFrame({"A": ["1", "", " ", "3"]})
    result = apply_types(df, {"A": "Int64"})
    assert result["A"].dtype == pd.Int64Dtype()
    assert result["A"].iloc[0] == 1
    assert pd.isna(result["A"].iloc[1])
    assert pd.isna(result["A"].iloc[2])
    assert result["A"].iloc[3] == 3


def test_apply_types_na_input_becomes_na_for_numeric() -> None:
    """NAを含む数値型カラムはNAが保持される."""
    df = pd.DataFrame({"A": pd.array([1, pd.NA, 3], dtype="Int64")})
    result = apply_types(df, {"A": "Int64"})
    assert result["A"].dtype == pd.Int64Dtype()
    assert result["A"].iloc[0] == 1
    assert pd.isna(result["A"].iloc[1])
    assert result["A"].iloc[2] == 3


def test_apply_types_whitespace_string_not_converted_for_object_type() -> None:
    """object型変換時は空文字列・空白のみ文字列はそのまま保持される."""
    df = pd.DataFrame({"A": ["", " ", "hello"]})
    result = apply_types(df, {"A": "object"})
    assert result["A"].iloc[0] == ""
    assert result["A"].iloc[1] == " "
