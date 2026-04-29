"""過去成績（馬柱）取得のサンプルスクリプト.

DataInterfaceを使用して、scraping・mykeibadb両プロバイダーで
指定した馬IDの過去成績を取得して表示・比較する。
"""

import argparse

import pandas as pd

from keiba_data_interface import DataInterface


def _show_diff(df1: pd.DataFrame, df2: pd.DataFrame) -> None:
    """2つのDataFrameの差分を3走前まで表示する."""
    if list(df1.columns) != list(df2.columns):
        only_df1 = set(df1.columns) - set(df2.columns)
        only_df2 = set(df2.columns) - set(df1.columns)
        print("  カラムが一致しません")
        if only_df1:
            print(f"  scraping のみ: {only_df1}")
        if only_df2:
            print(f"  mykeibadb のみ: {only_df2}")
        return
    if len(df1) != len(df2):
        print(f"  行数が異なります（scraping: {len(df1)}, mykeibadb: {len(df2)}）")
        return
    s = df1.reset_index(drop=True)
    m = df2.reset_index(drop=True)
    any_diff = False
    for idx in range(min(3, len(s))):
        row_diffs: list[str] = []
        for col in s.columns:
            s_val = s[col].iloc[idx]
            m_val = m[col].iloc[idx]
            s_na = pd.isna(s_val)
            m_na = pd.isna(m_val)
            if s_na and m_na:
                continue
            if s_na != m_na or s_val != m_val:
                row_diffs.append(f"  {col}: {s_val} vs {m_val}")
        if row_diffs:
            any_diff = True
            print(f"-- {idx + 1}走前 --")
            for line in row_diffs:
                print(line)
    if not any_diff:
        print("  差分なし")


def main() -> None:
    """メイン処理.

    馬IDを指定してDataInterfaceで過去成績を取得し、表示・比較する。
    """
    parser = argparse.ArgumentParser(description="過去成績（馬柱）取得のサンプルスクリプト")
    parser.add_argument("--horse-id", default="2022105081", help="馬ID")
    args = parser.parse_args()
    horse_id = args.horse_id

    print(f"馬ID: {horse_id}")
    print("=" * 80)

    results: dict[str, pd.DataFrame] = {}
    for provider in ("scraping", "mykeibadb"):
        di = DataInterface(provider)
        df = di.get_past_performances(horse_id)
        results[provider] = df
        print(f"\n【過去成績 ({provider})】")
        print(f"  レース数: {len(df)}件")
        print()
        if df.empty:
            print("  戦績なし（新馬）")
        else:
            for idx, (_, row) in enumerate(df.head(3).iterrows()):
                print(f"--- {idx + 1}走前 ---")
                for col in df.columns:
                    value = row[col]
                    # if pd.notna(value):
                    #     print(f"  {col}: {value}")
                    print(f"  {col}: {value}")
                print()

    print("\n【差分】")
    _show_diff(results["scraping"], results["mykeibadb"])


if __name__ == "__main__":
    main()
