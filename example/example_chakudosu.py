"""出走別着度数取得のサンプルスクリプト.

DataInterfaceを使用して、mykeibadbプロバイダーで指定レースの
出走別着度数を取得して表示する。
scrapingプロバイダーではDataNotFoundErrorが送出されることも確認する。
"""

import argparse

from keiba_data_interface import DataInterface
from keiba_data_interface.exceptions import DataNotFoundError


def main() -> None:
    """メイン処理.

    レースコードを指定してDataInterfaceで出走別着度数を取得し、表示する。
    """
    parser = argparse.ArgumentParser(description="出走別着度数取得のサンプルスクリプト")
    parser.add_argument("--race-code", default="2025122806050811", help="16桁レースコード")
    args = parser.parse_args()
    race_code = args.race_code

    print(f"レースコード: {race_code}")
    print("=" * 80)

    di = DataInterface("mykeibadb")
    df = di.get_chakudosu(race_code)
    print(f"\n【出走別着度数 (mykeibadb)】 {len(df)}頭 × {len(df.columns)}カラム")
    if df.empty:
        print("  データなし")
    else:
        for _, row in df.iterrows():
            nonzero = {
                col: row[col]
                for col in df.columns[3:]
                if row[col] is not None and row.notna()[col] and row[col] > 0
            }
            print(f"\n  {row['馬名']} ({row['血統登録番号']})")
            for col, value in nonzero.items():
                print(f"    {col}: {value}")

    print("\n【scrapingプロバイダーの確認】")
    di_scraping = DataInterface("scraping")
    try:
        di_scraping.get_chakudosu(race_code)
    except DataNotFoundError as e:
        print(f"  DataNotFoundError: {e}")


if __name__ == "__main__":
    main()
