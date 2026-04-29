"""統合テスト用のアサーションヘルパー関数."""

import pandas as pd
import pytest


def get_scraping_only_columns(
    all_columns: list[str],
    scraping_columns: list[str],
) -> list[str]:
    """scraping × のカラムリストを返す.

    Args:
        all_columns (list[str]): 全カラムリスト
        scraping_columns (list[str]): scraping ○ カラムリスト

    Returns:
        list[str]: scraping × のカラムリスト
    """
    scraping_set = set(scraping_columns)
    return [c for c in all_columns if c not in scraping_set]


def assert_columns_match(
    scraping_df: pd.DataFrame,
    mykeibadb_df: pd.DataFrame,
    expected_columns: list[str],
    table_name: str,
) -> None:
    """両Providerの出力DataFrameが同一カラム構成を持つことを検証する.

    Args:
        scraping_df (pd.DataFrame): ScrapingProvider出力
        mykeibadb_df (pd.DataFrame): MykeibaDBProvider出力
        expected_columns (list[str]): 期待されるカラムリスト
        table_name (str): テーブル名（エラーメッセージ用）
    """
    scraping_cols = set(scraping_df.columns)
    mykeibadb_cols = set(mykeibadb_df.columns)
    expected_cols = set(expected_columns)

    assert scraping_cols == expected_cols, (
        f"[{table_name}] ScrapingProvider出力のカラムが期待と不一致: "
        f"不足={expected_cols - scraping_cols}, 余剰={scraping_cols - expected_cols}"
    )
    assert mykeibadb_cols == expected_cols, (
        f"[{table_name}] MykeibaDBProvider出力のカラムが期待と不一致: "
        f"不足={expected_cols - mykeibadb_cols}, 余剰={mykeibadb_cols - expected_cols}"
    )


def assert_scraping_nan_columns(
    scraping_df: pd.DataFrame,
    nan_columns: list[str],
    table_name: str,
) -> None:
    """scraping × のカラムがNaNであることを検証する.

    Args:
        scraping_df (pd.DataFrame): ScrapingProvider出力
        nan_columns (list[str]): NaNであるべきカラムリスト
        table_name (str): テーブル名（エラーメッセージ用）
    """
    for col in nan_columns:
        if col in scraping_df.columns:
            assert scraping_df[col].isna().all(), (
                f"[{table_name}] scraping×のカラム '{col}' にNaN以外の値がある: "
                f"{scraping_df[col].tolist()}"
            )


def assert_common_values_match(
    scraping_df: pd.DataFrame,
    mykeibadb_df: pd.DataFrame,
    common_columns: list[str],
    table_name: str,
    sort_by: str | None = None,
    exclude_columns: set[str] | None = None,
) -> None:
    """共通カラムの型と値が一致することを検証する.

    Args:
        scraping_df (pd.DataFrame): ScrapingProvider出力
        mykeibadb_df (pd.DataFrame): MykeibaDBProvider出力
        common_columns (list[str]): 比較対象の共通カラムリスト
        table_name (str): テーブル名（エラーメッセージ用）
        sort_by (str | None): ソートに使用するカラム名
        exclude_columns (set[str] | None): 値比較から除外するカラム（既知のデータソース差異）
    """
    s_df = scraping_df.copy()
    m_df = mykeibadb_df.copy()
    excluded = exclude_columns or set()

    if sort_by and sort_by in s_df.columns and sort_by in m_df.columns:
        s_df = s_df.sort_values(sort_by).reset_index(drop=True)
        m_df = m_df.sort_values(sort_by).reset_index(drop=True)

    assert len(s_df) == len(
        m_df
    ), f"[{table_name}] 行数が不一致: scraping={len(s_df)}, mykeibadb={len(m_df)}"

    for col in common_columns:
        if col not in s_df.columns or col not in m_df.columns:
            continue
        if col in excluded:
            continue

        s_series = s_df[col]
        m_series = m_df[col]

        # 型の互換性チェック（nullable型の考慮）
        s_dtype = str(s_series.dtype)
        m_dtype = str(m_series.dtype)
        assert s_dtype == m_dtype, (
            f"[{table_name}] カラム '{col}' の型が不一致: "
            f"scraping={s_dtype}, mykeibadb={m_dtype}"
        )

        # 値の比較（NaN同士は一致として扱う）
        for idx in range(len(s_df)):
            s_val = s_series.iloc[idx]
            m_val = m_series.iloc[idx]

            s_is_na = pd.isna(s_val)
            m_is_na = pd.isna(m_val)

            if s_is_na and m_is_na:
                continue
            if s_is_na != m_is_na:
                pytest.fail(
                    f"[{table_name}] カラム '{col}' 行{idx}: "
                    f"NaN不一致 scraping={s_val}, mykeibadb={m_val}"
                )
            # float比較は近似一致
            if isinstance(s_val, float) and isinstance(m_val, float):
                assert abs(s_val - m_val) < 0.01, (
                    f"[{table_name}] カラム '{col}' 行{idx}: "
                    f"値不一致 scraping={s_val}, mykeibadb={m_val}"
                )
            else:
                # 文字列の末尾空白を除去して比較（mykeibadbは固定長フィールドの末尾空白あり）
                s_cmp = s_val.strip() if isinstance(s_val, str) else s_val
                m_cmp = m_val.strip() if isinstance(m_val, str) else m_val
                assert s_cmp == m_cmp, (
                    f"[{table_name}] カラム '{col}' 行{idx}: "
                    f"値不一致 scraping={s_val}, mykeibadb={m_val}"
                )
