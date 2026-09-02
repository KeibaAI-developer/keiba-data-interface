"""レース時刻表取得のサンプルスクリプト.

DataInterfaceを使用して、scraping・mykeibadb両プロバイダーで
指定した日付のレース時刻表を取得して表示する。
"""

import argparse

from keiba_data_interface import DataInterface


def main() -> None:
    """メイン処理.

    日付を指定してDataInterfaceでレース時刻表を取得し、表示する。
    """
    parser = argparse.ArgumentParser(description="レース時刻表取得のサンプルスクリプト")
    parser.add_argument("--date", default="20250406", help="日付（YYYYMMDD形式）")
    args = parser.parse_args()

    print(f"対象日: {args.date}")
    print("=" * 80)

    for provider in ("scraping", "mykeibadb"):
        di = DataInterface(provider)
        df = di.get_race_schedule(args.date)
        print(f"\n【レース時刻表 ({provider})】")
        print(f"  レース数: {len(df)}件")
        if df.empty:
            print("  開催なし")
        else:
            print(df.to_string(index=False))


if __name__ == "__main__":
    main()
