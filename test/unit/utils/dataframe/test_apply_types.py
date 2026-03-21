"""apply_types関数のテスト."""

import pandas as pd

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
