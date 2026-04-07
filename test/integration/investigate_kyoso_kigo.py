"""競走記号コードとnetkeiba表記の対応調査スクリプト.

mykeibadbのRACE_SHOSAIテーブルから各KYOSO_KIGO_CODEに該当するレースコードを1件ずつ取得し、
keiba-scrapingのEntryPageScraperで競走記号のnetkeiba表記を取得して対応表を出力する。
"""

import sys
import time

import pandas as pd
from mykeibadb.getters import RaceGetter
from scraping.config import ScrapingConfig
from scraping.entry_page import EntryPageScraper
from scraping.exceptions import ScrapingError

from keiba_data_interface.utils.race_code import race_code_to_race_id

# CODE_TABLE.md KYOSO_KIGO_CODE の全コード一覧
ALL_KYOSO_KIGO_CODES: list[str] = [
    "000",
    "001",
    "002",
    "003",
    "004",
    "020",
    "021",
    "023",
    "024",
    "030",
    "031",
    "033",
    "034",
    "040",
    "041",
    "043",
    "044",
    "A00",
    "A01",
    "A02",
    "A03",
    "A04",
    "A10",
    "A11",
    "A13",
    "A14",
    "A20",
    "A21",
    "A23",
    "A24",
    "A30",
    "A31",
    "A33",
    "A34",
    "A40",
    "A41",
    "B00",
    "B01",
    "B03",
    "B04",
    "C00",
    "C01",
    "C03",
    "C04",
    "D00",
    "D01",
    "D03",
    "E00",
    "E01",
    "E03",
    "F00",
    "F01",
    "F03",
    "F04",
    "G00",
    "G01",
    "G03",
    "H00",
    "H01",
    "I00",
    "I01",
    "I03",
    "J00",
    "J01",
    "K00",
    "K01",
    "K03",
    "L00",
    "L01",
    "L03",
    "M00",
    "M01",
    "M03",
    "M04",
    "N00",
    "N01",
    "N03",
    "N04",
    "N20",
    "N21",
    "N23",
    "N24",
    "N30",
    "N31",
    "N40",
    "N41",
    "N44",
]

REQUEST_INTERVAL = 1.0  # netkeiba リクエスト間隔（秒）
OUTPUT_PATH = "test/integration/report/kyoso_kigo_code_mapping.md"


def _fetch_race_codes_by_kigo_code(getter: RaceGetter) -> dict[str, str | None]:
    """各競走記号コードに該当するレースコードを1件ずつ取得する.

    Args:
        getter (RaceGetter): mykeibadbのRaceGetter

    Returns:
        dict[str, str | None]: コード→レースコード（該当なしはNone）
    """
    result: dict[str, str | None] = {}
    conn_mgr = getter.connection_manager
    for code in ALL_KYOSO_KIGO_CODES:
        rows = conn_mgr.execute_query(
            "SELECT RACE_CODE FROM RACE_SHOSAI"
            " WHERE KYOSO_KIGO_CODE = %s"
            " ORDER BY RACE_CODE DESC LIMIT 1",
            (code,),
        )
        result[code] = str(rows[0][0]) if rows else None
    return result


def _fetch_scraping_kigo(race_code: str, config: ScrapingConfig) -> str | None:
    """scrapingで競走記号を取得する.

    Args:
        race_code (str): 16桁レースコード
        config (ScrapingConfig): scraping設定

    Returns:
        str | None: 競走記号文字列（取得失敗時はNone）
    """
    race_id = race_code_to_race_id(race_code)
    try:
        scraper = EntryPageScraper(race_id, config)
        df = scraper.get_race_info()
        val = df.iloc[0].get("競走記号")
        if pd.notna(val):
            return str(val)
        return ""
    except ScrapingError as e:
        print(f"  スクレイピングエラー ({race_code}): {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  予期しないエラー ({race_code}): {e}", file=sys.stderr)
        return None


def main() -> None:
    """メイン処理."""
    print("mykeibadbから各競走記号コードのレースコードを取得中...")
    getter = RaceGetter()
    code_to_race_code = _fetch_race_codes_by_kigo_code(getter)

    found_count = sum(1 for v in code_to_race_code.values() if v is not None)
    print(f"  {found_count}/{len(ALL_KYOSO_KIGO_CODES)} コードにレースが存在")

    print("netkeibaから競走記号を取得中...")
    config = ScrapingConfig()
    rows: list[dict[str, str]] = []

    for code in ALL_KYOSO_KIGO_CODES:
        race_code = code_to_race_code[code]
        if race_code is None:
            rows.append(
                {
                    "競走記号コード": code,
                    "レースコード": "(該当なし)",
                    "netkeiba競走記号": "(該当なし)",
                }
            )
            continue

        scraping_kigo = _fetch_scraping_kigo(race_code, config)
        rows.append(
            {
                "競走記号コード": code,
                "レースコード": race_code,
                "netkeiba競走記号": scraping_kigo if scraping_kigo is not None else "(取得失敗)",
            }
        )
        print(f"  {code}: {scraping_kigo!r}")
        time.sleep(REQUEST_INTERVAL)

    # マークダウン出力
    lines = [
        "# 競走記号コード対応表",
        "",
        "mykeibadb KYOSO_KIGO_CODE と netkeiba 出馬表ページの競走記号表記の対応。",
        "",
        "| 競走記号コード | レースコード | netkeiba競走記号 |",
        "|------|------|------|",
    ]
    for row in rows:
        lines.append(
            f"| {row['競走記号コード']} | {row['レースコード']}" f" | {row['netkeiba競走記号']} |"
        )

    output = "\n".join(lines) + "\n"
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"\n出力: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
