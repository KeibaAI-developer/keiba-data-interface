"""単複票数取得のサンプルスクリプト.

DataInterface（mykeibadbプロバイダー）で指定したレースコードの単勝・複勝の票数を取得し、
票数から複勝支持率（複勝票数 ÷ 複勝票数合計）を計算して表示する。

Usage:
    python example/example_win_show_votes.py [--race_code <race_code>]
"""

import argparse

from keiba_data_interface import DataInterface


def main() -> None:
    """単複票数を取得して表示する."""
    parser = argparse.ArgumentParser(description="単複票数を取得して表示する")
    parser.add_argument("--race_code", default="2025122806050811", help="16桁レースコード")
    args = parser.parse_args()

    di = DataInterface(provider="mykeibadb")
    df = di.get_win_show_votes(args.race_code)

    print(f"レースコード: {args.race_code}（データ区分: {df['データ区分'].iloc[0]}）")
    print(f"複勝票数合計: {int(df['複勝票数合計'].iloc[0])}（百円単位）")
    df["複勝支持率"] = df["複勝票数"] / df["複勝票数合計"]
    columns = ["馬番", "単勝票数", "単勝票数人気", "複勝票数", "複勝票数人気", "複勝支持率"]
    print(df[columns].to_string(index=False))


if __name__ == "__main__":
    main()
