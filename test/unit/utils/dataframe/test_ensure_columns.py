"""ensure_columns関数のテスト."""

import pandas as pd

from keiba_data_interface.utils.dataframe import ensure_columns


# 正常系
def test_ensure_columns_missing_columns_filled_with_na() -> None:
    """不足カラムがNaNで埋められる."""
    df = pd.DataFrame({"A": [1], "B": [2]})
    result = ensure_columns(df, ["A", "B", "C"])
    assert list(result.columns) == ["A", "B", "C"]
    assert pd.isna(result["C"].iloc[0])


def test_ensure_columns_extra_columns_removed() -> None:
    """余分なカラムが削除される."""
    df = pd.DataFrame({"A": [1], "B": [2], "C": [3]})
    result = ensure_columns(df, ["A", "B"])
    assert list(result.columns) == ["A", "B"]
    assert "C" not in result.columns


def test_ensure_columns_order_unified() -> None:
    """カラム順序が指定リスト通りに統一される."""
    df = pd.DataFrame({"C": [3], "A": [1], "B": [2]})
    result = ensure_columns(df, ["A", "B", "C"])
    assert list(result.columns) == ["A", "B", "C"]


def test_ensure_columns_all_match() -> None:
    """カラムが完全に一致する場合そのまま返される."""
    df = pd.DataFrame({"A": [1], "B": [2]})
    result = ensure_columns(df, ["A", "B"])
    assert list(result.columns) == ["A", "B"]
    assert result["A"].iloc[0] == 1
    assert result["B"].iloc[0] == 2


def test_ensure_columns_mixed() -> None:
    """不足カラムのNaN埋めと余分カラムの除去が同時に行われる."""
    df = pd.DataFrame({"A": [1], "B": [2], "D": [4]})
    result = ensure_columns(df, ["A", "C"])
    assert list(result.columns) == ["A", "C"]
    assert result["A"].iloc[0] == 1
    assert pd.isna(result["C"].iloc[0])
    assert "B" not in result.columns
    assert "D" not in result.columns


def test_ensure_columns_empty_dataframe() -> None:
    """空のDataFrameに対してカラムが追加される."""
    df = pd.DataFrame()
    result = ensure_columns(df, ["A", "B"])
    assert list(result.columns) == ["A", "B"]
    assert len(result) == 0


def test_ensure_columns_does_not_modify_input() -> None:
    """入力DataFrameが変更されない."""
    df = pd.DataFrame({"A": [1], "B": [2]})
    original_columns = list(df.columns)
    ensure_columns(df, ["A", "B", "C"])
    assert list(df.columns) == original_columns
    assert "C" not in df.columns
