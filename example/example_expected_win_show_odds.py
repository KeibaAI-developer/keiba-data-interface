"""予想オッズ取得のサンプルスクリプト.

scrapingプロバイダーで、馬券発売前のレースの予想オッズ（netkeibaの予想単勝オッズ）を
単複オッズのスキーマで取得して表示する。
"""

import argparse

import pandas as pd

from keiba_data_interface import DataInterface


def main() -> None:
    """メイン処理.

    レースコードを指定して予想オッズを取得し、表示する。
    """
    parser = argparse.ArgumentParser(description="予想オッズ取得のサンプルスクリプト")
    parser.add_argument("--race-code", required=True, help="16桁レースコード（発売前のレース）")
    args = parser.parse_args()

    pd.set_option("display.max_rows", None)
    pd.set_option("display.width", None)

    di = DataInterface("scraping")
    df = di.get_expected_win_show_odds(args.race_code)
    print(f"レースコード: {args.race_code}（{len(df)} 頭）")
    print(df[["馬番", "単勝オッズ", "単勝人気"]])


if __name__ == "__main__":
    main()
