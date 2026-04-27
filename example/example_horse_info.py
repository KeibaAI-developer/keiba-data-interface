"""競走馬情報取得のサンプルスクリプト.

DataInterfaceを使用して、scraping・mykeibadb両プロバイダーで
指定した馬IDの競走馬情報を取得して表示・比較する。
"""

import pandas as pd

from keiba_data_interface import DataInterface


def _show_diff(df1: pd.DataFrame, df2: pd.DataFrame) -> None:
    """2つのDataFrameの差分を表示する."""
    if list(df1.columns) != list(df2.columns):
        only_df1 = set(df1.columns) - set(df2.columns)
        only_df2 = set(df2.columns) - set(df1.columns)
        print("  カラムが一致しません")
        if only_df1:
            print(f"  scraping のみ: {only_df1}")
        if only_df2:
            print(f"  mykeibadb のみ: {only_df2}")
        return
    if df1.empty or df2.empty:
        print("  データなし")
        return
    row1 = df1.iloc[0]
    row2 = df2.iloc[0]
    any_diff = False
    for col in df1.columns:
        s_val = row1[col]
        m_val = row2[col]
        s_na = pd.isna(s_val)
        m_na = pd.isna(m_val)
        if s_na and m_na:
            continue
        if s_na != m_na or s_val != m_val:
            if not any_diff:
                any_diff = True
            print(f"  {col}: {s_val} vs {m_val}")
    if not any_diff:
        print("  差分なし")


def main() -> None:
    """メイン処理.

    馬IDを指定してDataInterfaceで競走馬情報を取得し、表示・比較する。
    """
    horse_id = "2022105081"

    print(f"馬ID: {horse_id}")
    print("=" * 80)

    results: dict[str, pd.DataFrame] = {}
    for provider in ("scraping", "mykeibadb"):
        di = DataInterface(provider)
        df = di.get_horse_info(horse_id)
        results[provider] = df
        print(f"\n【競走馬情報 ({provider})】")
        if df.empty:
            print("  データなし")
        else:
            for col in df.columns:
                value = df.iloc[0][col]
                print(f"  {col}: {value}")

    print("\n【差分】")
    _show_diff(results["scraping"], results["mykeibadb"])


if __name__ == "__main__":
    main()
