"""単複オッズ取得のサンプルスクリプト.

DataInterfaceを使用して、scraping・mykeibadb両プロバイダーで
指定したレースコードの単複オッズを取得して表示・比較する。
"""

import pandas as pd

from keiba_data_interface import DataInterface


def _show_row(row: pd.Series) -> None:
    """1行分のデータを表示する."""
    for col in row.index:
        value = row[col]
        # if pd.notna(value):
        #     print(f"  {col}: {value}")
        print(f"  {col}: {value}")


def show_diff(df1: pd.DataFrame, df2: pd.DataFrame) -> None:
    """2つのDataFrameの差分を馬番3まで表示する."""
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
    any_diff = False
    for idx in range(min(3, len(df1))):
        umaban = df1["馬番"].iloc[idx]
        row_diffs: list[str] = []
        for col in df1.columns:
            s_val = df1[col].iloc[idx]
            m_val = df2[col].iloc[idx]
            s_na = pd.isna(s_val)
            m_na = pd.isna(m_val)
            if s_na and m_na:
                continue
            if s_na != m_na or s_val != m_val:
                row_diffs.append(f"  {col}: {s_val} vs {m_val}")
        if row_diffs:
            any_diff = True
            print(f"-- 馬番 {umaban} --")
            for line in row_diffs:
                print(line)
    if not any_diff:
        print("  差分なし")


def main() -> None:
    """メイン処理.

    レースコードを指定してDataInterfaceで単複オッズを取得し、表示・比較する。
    """
    # 16桁レースコード
    race_code = "2023112605050812"

    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)

    print(f"レースコード: {race_code}")
    print("=" * 80)

    results: dict[str, pd.DataFrame] = {}
    for provider in ("scraping", "mykeibadb"):
        di = DataInterface(provider)
        df = di.get_win_show_odds(race_code)
        results[provider] = df
        print(f"\n【単複オッズ ({provider})】")
        print(f"  頭数: {len(df)}")
        print("  （馬番1のデータ）")
        df_sorted = df.sort_values("馬番").reset_index(drop=True)
        _show_row(df_sorted.iloc[0])

    print("\n【差分】")
    show_diff(results["scraping"], results["mykeibadb"])


if __name__ == "__main__":
    main()
