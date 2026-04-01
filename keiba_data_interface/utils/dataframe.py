"""DataFrame整形ユーティリティ.

DataFrameのカラム調整や型変換を提供する。
"""

import pandas as pd
from pandas.api.types import pandas_dtype


def ensure_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """指定カラムリストに合わせてDataFrameのカラムを調整する.

    不足カラムはNaN埋め、余分なカラムは削除し、カラム順序を統一する。
    入力DataFrameは変更しない。

    Args:
        df (pd.DataFrame): 入力DataFrame
        columns (list[str]): 期待するカラムリスト

    Returns:
        pd.DataFrame: カラムが調整された新しいDataFrame
    """
    result = df.copy()
    missing = [col for col in columns if col not in result.columns]
    if missing:
        missing_df = pd.DataFrame({col: pd.NA for col in missing}, index=result.index)
        result = pd.concat([result, missing_df], axis=1)
    return result[columns].copy()


def apply_types(df: pd.DataFrame, type_dict: dict[str, str]) -> pd.DataFrame:
    """型定義辞書に基づいてDataFrameの型を変換する.

    入力DataFrameは変更しない。
    数値型への変換時、空白のみの文字列はNAに変換してから型変換する。

    Args:
        df (pd.DataFrame): 入力DataFrame
        type_dict (dict[str, str]): カラム名 → pandas型文字列の辞書

    Returns:
        pd.DataFrame: 型変換された新しいDataFrame
    """
    result = df.copy()
    for col, dtype in type_dict.items():
        if col in result.columns:
            target_dtype = pandas_dtype(dtype)
            is_numeric = pd.api.types.is_numeric_dtype(target_dtype)
            if is_numeric and result[col].dtype == object:
                result[col] = result[col].map(
                    lambda v: pd.NA if isinstance(v, str) and len(v) > 0 and v.strip() == "" else v
                )
            result[col] = result[col].astype(target_dtype)
    return result
