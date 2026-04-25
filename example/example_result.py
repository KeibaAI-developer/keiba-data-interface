"""レース結果取得のサンプルスクリプト.

DataInterfaceを使用して、scraping・mykeibadb両プロバイダーで
指定したレースコードのレース結果（馬毎）を取得して表示・比較する。
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


def _show_diff(df1: pd.DataFrame, df2: pd.DataFrame) -> None:
    """2つのDataFrameの差分を3着まで表示する."""
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
    s = df1.sort_values("確定着順").reset_index(drop=True)
    m = df2.sort_values("確定着順").reset_index(drop=True)
    any_diff = False
    for idx in range(3):
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
            print(f"-- {idx + 1}着 --")
            for line in row_diffs:
                print(line)
    if not any_diff:
        print("  差分なし")


def main() -> None:
    """メイン処理.

    レースコードを指定してDataInterfaceでレース結果を取得し、表示・比較する。
    """
    # 16桁レースコード
    race_code = "2023112605050812"

    print(f"レースコード: {race_code}")
    print("=" * 80)

    results: dict[str, pd.DataFrame] = {}
    for provider in ("scraping", "mykeibadb"):
        di = DataInterface(provider)
        df = di.get_result(race_code)
        results[provider] = df
        print(f"\n【レース結果 ({provider})】")
        print(f"  出走頭数: {len(df)}頭")
        print("  （1着の馬のデータ）")
        _show_row(df.iloc[0])

    print("\n【差分】")
    _show_diff(results["scraping"], results["mykeibadb"])


if __name__ == "__main__":
    main()
