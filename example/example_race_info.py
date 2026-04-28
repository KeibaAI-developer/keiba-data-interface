"""レース基本情報取得のサンプルスクリプト.

DataInterfaceを使用して、scraping・mykeibadb両プロバイダーで
指定したレースコードのレース基本情報を取得して表示・比較する。
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
    if len(df1) != len(df2):
        print(f"  行数が異なります（scraping: {len(df1)}, mykeibadb: {len(df2)}）")
        return
    diff = df1.reset_index(drop=True).compare(
        df2.reset_index(drop=True), result_names=("scraping", "mykeibadb")
    )
    if diff.empty:
        print("  差分なし")
    else:
        for col in diff.columns.get_level_values(0).unique():
            scraping_val = diff[col]["scraping"].iloc[0]
            mykeibadb_val = diff[col]["mykeibadb"].iloc[0]
            print(f"  {col}: {scraping_val} vs {mykeibadb_val}")


def main() -> None:
    """メイン処理.

    レースコードを指定してDataInterfaceでレース基本情報を取得し、表示・比較する。
    """
    # 16桁レースコード（年4+月日4+競馬場2+回2+日目2+R2）
    race_code = "2025060105021211"

    print(f"レースコード: {race_code}")
    print("=" * 80)

    results: dict[str, pd.DataFrame] = {}
    for provider in ("scraping", "mykeibadb"):
        di = DataInterface(provider)
        df = di.get_race_basic_info(race_code)
        results[provider] = df
        print(f"\n【レース基本情報 ({provider})】")
        for col in df.columns:
            value = df.at[0, col]
            # if pd.notna(value):
            #     print(f"  {col}: {value}")
            print(f"  {col}: {value}")
    print("\n【差分】")
    _show_diff(results["scraping"], results["mykeibadb"])


if __name__ == "__main__":
    main()
