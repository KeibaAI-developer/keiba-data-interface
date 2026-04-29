"""recalculate_ninkijun関数のテスト."""

import pandas as pd
import pytest

from keiba_data_interface.utils.dataframe import recalculate_ninkijun


# 正常系
def test_recalculate_ninkijun_basic_ranking() -> None:
    """単勝オッズの昇順で人気順が割り振られる."""
    df = pd.DataFrame(
        {
            "単勝オッズ": pd.array([2.5, 1.5, 3.0], dtype="Float64"),
            "単勝人気順": pd.array([pd.NA, pd.NA, pd.NA], dtype="Int64"),
        }
    )
    result = recalculate_ninkijun(df)
    assert result["単勝人気順"].iloc[0] == 2  # オッズ2.5 → 2番人気
    assert result["単勝人気順"].iloc[1] == 1  # オッズ1.5 → 1番人気
    assert result["単勝人気順"].iloc[2] == 3  # オッズ3.0 → 3番人気


def test_recalculate_ninkijun_same_odds_same_rank() -> None:
    """同一オッズの馬には同じ人気順が付与される."""
    df = pd.DataFrame(
        {
            "単勝オッズ": pd.array([2.0, 2.0, 3.0], dtype="Float64"),
            "単勝人気順": pd.array([pd.NA, pd.NA, pd.NA], dtype="Int64"),
        }
    )
    result = recalculate_ninkijun(df)
    assert result["単勝人気順"].iloc[0] == 1  # オッズ2.0 → 1番人気（同率）
    assert result["単勝人気順"].iloc[1] == 1  # オッズ2.0 → 1番人気（同率）
    assert result["単勝人気順"].iloc[2] == 3  # オッズ3.0 → 3番人気（2位は欠番）


@pytest.mark.parametrize(
    "odds_value",
    [pd.NA, float("nan")],
    ids=["pd.NA", "float_nan"],
)
def test_recalculate_ninkijun_nan_odds_becomes_na_rank(odds_value: object) -> None:
    """単勝オッズがNaNの馬は単勝人気順もNAになる."""
    df = pd.DataFrame(
        {
            "単勝オッズ": pd.array([1.5, odds_value], dtype="Float64"),
            "単勝人気順": pd.array([pd.NA, pd.NA], dtype="Int64"),
        }
    )
    result = recalculate_ninkijun(df)
    assert result["単勝人気順"].iloc[0] == 1
    assert pd.isna(result["単勝人気順"].iloc[1])


def test_recalculate_ninkijun_all_nan_odds() -> None:
    """全馬の単勝オッズがNaNの場合、全馬の単勝人気順がNAになる."""
    df = pd.DataFrame(
        {
            "単勝オッズ": pd.array([pd.NA, pd.NA, pd.NA], dtype="Float64"),
            "単勝人気順": pd.array([1, 2, 3], dtype="Int64"),
        }
    )
    result = recalculate_ninkijun(df)
    assert pd.isna(result["単勝人気順"].iloc[0])
    assert pd.isna(result["単勝人気順"].iloc[1])
    assert pd.isna(result["単勝人気順"].iloc[2])


def test_recalculate_ninkijun_mixed_nan_and_valid_odds() -> None:
    """NaNと有効オッズが混在する場合、有効オッズのみでランク付けされる."""
    df = pd.DataFrame(
        {
            "単勝オッズ": pd.array([3.0, pd.NA, 1.0], dtype="Float64"),
            "単勝人気順": pd.array([pd.NA, pd.NA, pd.NA], dtype="Int64"),
        }
    )
    result = recalculate_ninkijun(df)
    assert result["単勝人気順"].iloc[0] == 2  # オッズ3.0 → 2番人気（有効馬中）
    assert pd.isna(result["単勝人気順"].iloc[1])  # NaN → NA
    assert result["単勝人気順"].iloc[2] == 1  # オッズ1.0 → 1番人気（有効馬中）


def test_recalculate_ninkijun_does_not_modify_input() -> None:
    """入力DataFrameが変更されない."""
    df = pd.DataFrame(
        {
            "単勝オッズ": pd.array([2.0, 1.0], dtype="Float64"),
            "単勝人気順": pd.array([99, 99], dtype="Int64"),
        }
    )
    recalculate_ninkijun(df)
    assert df["単勝人気順"].iloc[0] == 99
    assert df["単勝人気順"].iloc[1] == 99


@pytest.mark.parametrize(
    "columns",
    [
        {"単勝人気順": pd.array([pd.NA], dtype="Int64")},
        {"単勝オッズ": pd.array([1.5], dtype="Float64")},
        {},
    ],
    ids=["missing_odds", "missing_rank", "both_missing"],
)
def test_recalculate_ninkijun_missing_required_column_returns_copy(
    columns: dict[str, object],
) -> None:
    """必要なカラムが不足している場合、元のDataFrameのコピーをそのまま返す."""
    df = pd.DataFrame(columns)
    result = recalculate_ninkijun(df)
    assert list(result.columns) == list(df.columns)
    assert result is not df
