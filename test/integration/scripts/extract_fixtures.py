"""テスト用フィクスチャデータ抽出スクリプト.

keiba-scrapingのHTMLフィクスチャとmykeibadb-pythonのDBデータから
統合テスト用のrawデータをpickle形式で保存する。

pickle形式を使用する理由:
    JSONはpd.read_json時に型が変換されてしまう（例: 文字列"0000"がint 0になる）。
    mykeibadbの出力DataFrameの型を正確に保持するためpickle形式を使用する。

フォルダ構成:
    fixtures/
    ├── test_cases.json          # テストケース定義
    ├── races/                   # レースデータ
    │   └── {race_code}/        # 16桁レースコード
    │       ├── scraping_*.pkl
    │       └── mykeibadb_*.pkl
    ├── horses/                  # 馬データ
    │   └── {horse_id}/
    │       ├── scraping_past_performances.pkl
    │       └── mykeibadb_umagoto_race_joho.pkl
    └── schedules/               # スケジュール
        └── {YYYYMMDD}/
            ├── scraping_schedule.pkl
            └── mykeibadb_kaisai_schedule.pkl

使用方法:
    MYKEIBADB_HOST=host.docker.internal python test/integration/scripts/extract_fixtures.py
"""

import json
import traceback
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import yaml
from mykeibadb import OddsGetter, RaceGetter
from scraping import (
    EntryPageScraper,
    PastPerformancesScraper,
    RaceScheduleScraper,
    ResultPageScraper,
)
from scraping.odds import scrape_odds_from_netkeiba

_LIBS_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
SCRAPING_HTML_DIR = _LIBS_DIR / "keiba-scraping/test/fixtures/html"
SCRAPING_FIXTURES_DIR = _LIBS_DIR / "keiba-scraping/test/fixtures"


def _load_html(fixture_filename: str) -> str:
    """keiba-scrapingのHTMLフィクスチャを読み込む."""
    filepath = SCRAPING_HTML_DIR / fixture_filename
    raw = filepath.read_bytes()
    for enc in ("utf-8", "euc-jp", "shift-jis"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _create_entry_scraper(race_id: str) -> EntryPageScraper:
    """HTMLフィクスチャからEntryPageScraperを生成する."""
    html_text = _load_html(f"entry_{race_id}.html")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = html_text
    mock_response.encoding = "utf-8"
    mock_response.raise_for_status = MagicMock()
    with patch("scraping.entry_page.requests.get", return_value=mock_response):
        return EntryPageScraper(race_id)


def _create_result_scraper(race_id: str) -> ResultPageScraper:
    """HTMLフィクスチャからResultPageScraperを生成する."""
    html_text = _load_html(f"result_{race_id}.html")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = html_text
    mock_response.encoding = "utf-8"
    mock_response.raise_for_status = MagicMock()
    with patch("scraping.result_page.requests.get", return_value=mock_response):
        return ResultPageScraper(race_id)


def _create_past_performances_scraper(horse_id: str) -> PastPerformancesScraper:
    """HTMLフィクスチャからPastPerformancesScraperを生成する."""
    html_text = _load_html(f"past_performances_{horse_id}.html")
    mock_driver = MagicMock()
    mock_driver.page_source = html_text
    with patch("scraping.past_performances.webdriver.Chrome", return_value=mock_driver):
        return PastPerformancesScraper(horse_id)


def _create_schedule_scraper(
    year: int,
    month: int,
    day: int,
) -> RaceScheduleScraper:
    """HTMLフィクスチャからRaceScheduleScraperを生成する."""
    date_str = f"{year:04d}{month:02d}{day:02d}"
    html_text = _load_html(f"race_schedule_{date_str}.html")
    mock_driver = MagicMock()
    mock_driver.page_source = html_text
    with (
        patch("scraping.race_schedule.webdriver.Chrome", return_value=mock_driver),
        patch("scraping.race_schedule.time.sleep"),
    ):
        return RaceScheduleScraper(year, month, day)


def _save_df(df: pd.DataFrame, path: Path) -> None:
    """DataFrameをpickle形式で保存する."""
    pickle_path = path.with_suffix(".pkl")
    df.to_pickle(pickle_path)
    print(f"  保存: {pickle_path.relative_to(FIXTURES_DIR)} ({df.shape})")


def _build_race_code(race_id: str, race_date: date) -> str:
    """race_id(12桁)と日付からrace_code(16桁)を構成する.

    race_code構造: YYYY + MMDD + 競馬場(2) + 回(2) + 日目(2) + R(2)
    race_id構造:   YYYY + 競馬場(2) + 回(2) + 日目(2) + R(2)
    """
    year = race_id[:4]
    rest = race_id[4:]  # 競馬場 + 回 + 日目 + R (8桁)
    mmdd = f"{race_date.month:02d}{race_date.day:02d}"
    return year + mmdd + rest


def _has_entry_html(race_id: str) -> bool:
    """entry HTMLフィクスチャが存在するか確認する."""
    return (SCRAPING_HTML_DIR / f"entry_{race_id}.html").exists()


def _has_result_html(race_id: str) -> bool:
    """result HTMLフィクスチャが存在するか確認する."""
    return (SCRAPING_HTML_DIR / f"result_{race_id}.html").exists()


def _has_schedule_html(target_date: date) -> bool:
    """schedule HTMLフィクスチャが存在するか確認する."""
    date_str = target_date.strftime("%Y%m%d")
    return (SCRAPING_HTML_DIR / f"race_schedule_{date_str}.html").exists()


def extract_race_fixtures(
    race_id: str,
    race_name: str,
    description: str,
) -> dict[str, object] | None:
    """1レース分のフィクスチャデータを抽出する."""
    print(f"\n=== {race_name} ({race_id}) - {description} ===")

    has_entry = _has_entry_html(race_id)
    has_result = _has_result_html(race_id)

    if not has_entry and not has_result:
        print("  スキップ: entry/result HTMLフィクスチャが存在しません")
        return None

    # === 日付取得とrace_code構成 ===
    try:
        scraper: EntryPageScraper | ResultPageScraper
        if has_entry:
            scraper = _create_entry_scraper(race_id)
        else:
            scraper = _create_result_scraper(race_id)
        raw_race_info = scraper.get_race_info()
        # ここのhas_entry/has_resultは一時変数として使用し、戻り値には含めない

        race_date = raw_race_info.iloc[0]["日付"]
        if isinstance(race_date, str):
            race_date = date.fromisoformat(race_date)
        elif hasattr(race_date, "date"):
            race_date = race_date.date()

        race_code = _build_race_code(race_id, race_date)
        print(f"  race_code: {race_code}")
    except Exception as e:
        print(f"  エラー（race_code構成）: {e}")
        traceback.print_exc()
        return None

    # ディレクトリ作成
    race_dir = FIXTURES_DIR / "races" / race_code
    race_dir.mkdir(parents=True, exist_ok=True)

    # === Scraping側 ===
    print("[Scraping]")
    try:
        if has_entry:
            entry_scraper = _create_entry_scraper(race_id)
            _save_df(entry_scraper.get_race_info(), race_dir / "scraping_race_info.pkl")
            _save_df(entry_scraper.get_entry(), race_dir / "scraping_entry.pkl")
        else:
            print("  entry HTMLなし → scraping_entryをスキップ")

        if has_result:
            result_scraper = _create_result_scraper(race_id)
            if not has_entry:
                _save_df(
                    result_scraper.get_race_info(),
                    race_dir / "scraping_race_info.pkl",
                )
            _save_df(result_scraper.get_result(), race_dir / "scraping_result.pkl")
            _save_df(result_scraper.get_lap_time(), race_dir / "scraping_lap_time.pkl")
            _save_df(result_scraper.get_corner(), race_dir / "scraping_corner.pkl")

            payoff_methods = {
                "win": result_scraper.get_win_payoff,
                "show": result_scraper.get_show_payoff,
                "bracket": result_scraper.get_bracket_payoff,
                "quinella": result_scraper.get_quinella_payoff,
                "quinella_place": result_scraper.get_quinella_place_payoff,
                "exacta": result_scraper.get_exacta_payoff,
                "trio": result_scraper.get_trio_payoff,
                "trifecta": result_scraper.get_trifecta_payoff,
            }
            for name, method in payoff_methods.items():
                _save_df(method(), race_dir / f"scraping_payoff_{name}.pkl")
        else:
            print("  result HTMLなし → result系データをスキップ")

        # オッズ（netkeiba APIから取得）
        try:
            odds_df = scrape_odds_from_netkeiba(race_id)
            if not odds_df.empty:
                _save_df(odds_df, race_dir / "scraping_odds.pkl")
            else:
                print("  オッズ: 空データ（発売前 or 取得不可）")
        except Exception as e:
            print(f"  オッズ取得エラー: {e}")
    except Exception as e:
        print(f"  Scrapingエラー: {e}")
        traceback.print_exc()

    # === MykeibaDB側 ===
    print("[MykeibaDB]")
    try:
        rg = RaceGetter()
        og = OddsGetter()

        _save_df(
            rg.get_race_shosai(race_code=race_code, convert_codes=True),
            race_dir / "mykeibadb_race_shosai.pkl",
        )
        _save_df(
            rg.get_umagoto_race_joho(race_code=race_code, convert_codes=True),
            race_dir / "mykeibadb_umagoto_race_joho.pkl",
        )
        _save_df(
            rg.get_haraimodoshi(race_code=race_code, convert_codes=True),
            race_dir / "mykeibadb_haraimodoshi.pkl",
        )
        _save_df(
            og.get_odds1_tansho(race_code=race_code, convert_codes=True),
            race_dir / "mykeibadb_odds1_tansho.pkl",
        )
        _save_df(
            og.get_odds1_fukusho(race_code=race_code, convert_codes=True),
            race_dir / "mykeibadb_odds1_fukusho.pkl",
        )
    except Exception as e:
        print(f"  MykeibaDBエラー: {e}")
        traceback.print_exc()

    return {
        "race_id": race_id,
        "race_code": race_code,
        "name": race_name,
        "description": description,
    }


def extract_horse_fixtures(
    horse_id: str,
    horse_name: str,
    description: str,
) -> dict[str, object] | None:
    """1頭分のフィクスチャデータを抽出する."""
    print(f"\n=== {horse_name} ({horse_id}) - {description} ===")

    horse_dir = FIXTURES_DIR / "horses" / horse_id
    horse_dir.mkdir(parents=True, exist_ok=True)

    # Scraping
    has_html = (SCRAPING_HTML_DIR / f"past_performances_{horse_id}.html").exists()
    print("[Scraping]")
    if has_html:
        try:
            scraper = _create_past_performances_scraper(horse_id)
            _save_df(
                scraper.get_past_performances(),
                horse_dir / "scraping_past_performances.pkl",
            )
        except Exception as e:
            print(f"  Scrapingエラー: {e}")
            traceback.print_exc()
    else:
        print("  past_performances HTMLなし → スキップ")

    # MykeibaDB
    print("[MykeibaDB]")
    try:
        rg = RaceGetter()
        _save_df(
            rg.get_umagoto_race_joho(ketto_toroku_bango=horse_id, convert_codes=True),
            horse_dir / "mykeibadb_umagoto_race_joho.pkl",
        )
    except Exception as e:
        print(f"  MykeibaDBエラー: {e}")
        traceback.print_exc()

    return {
        "horse_id": horse_id,
        "name": horse_name,
        "description": description,
    }


def extract_schedule_fixtures(target_date: date) -> dict[str, object] | None:
    """スケジュールフィクスチャデータを抽出する."""
    date_str = target_date.strftime("%Y%m%d")
    print(f"\n=== スケジュール ({date_str}) ===")

    if not _has_schedule_html(target_date):
        print("  スキップ: schedule HTMLフィクスチャが存在しません")
        return None

    sched_dir = FIXTURES_DIR / "schedules" / date_str
    sched_dir.mkdir(parents=True, exist_ok=True)

    # Scraping
    print("[Scraping]")
    try:
        scraper = _create_schedule_scraper(
            target_date.year,
            target_date.month,
            target_date.day,
        )
        _save_df(scraper.get_race_schedule(), sched_dir / "scraping_schedule.pkl")
    except Exception as e:
        print(f"  Scrapingエラー: {e}")
        traceback.print_exc()

    # MykeibaDB
    print("[MykeibaDB]")
    try:
        rg = RaceGetter()
        _save_df(
            rg.get_kaisai_schedule(
                start_date=target_date,
                end_date=target_date,
                convert_codes=True,
            ),
            sched_dir / "mykeibadb_kaisai_schedule.pkl",
        )
    except Exception as e:
        print(f"  MykeibaDBエラー: {e}")
        traceback.print_exc()

    return {"date": target_date.isoformat()}


def main() -> None:
    """フィクスチャデータを一括抽出する."""
    # テストケース読み込み
    race_cases_path = SCRAPING_FIXTURES_DIR / "race_test_cases.yml"
    horse_cases_path = SCRAPING_FIXTURES_DIR / "test_horse_case.yml"

    with open(race_cases_path) as f:
        race_cases = yaml.safe_load(f)
    with open(horse_cases_path) as f:
        horse_cases = yaml.safe_load(f)

    print(f"レースケース数: {len(race_cases)}")
    print(f"馬ケース数: {len(horse_cases)}")

    # レース抽出
    race_results: list[dict[str, object]] = []
    for case in race_cases:
        race_result = extract_race_fixtures(
            race_id=case["race_id"],
            race_name=case["race_name"],
            description=case.get("description", ""),
        )
        if race_result is not None:
            race_results.append(race_result)

    # 馬抽出
    horse_results: list[dict[str, object]] = []
    for case in horse_cases:
        horse_result = extract_horse_fixtures(
            horse_id=case["horse_id"],
            horse_name=case["horse_name"],
            description=case.get("description", ""),
        )
        if horse_result is not None:
            horse_results.append(horse_result)

    # スケジュール抽出
    schedule_results: list[dict[str, object]] = []
    schedule_htmls = list(SCRAPING_HTML_DIR.glob("race_schedule_*.html"))
    for html_path in schedule_htmls:
        ds = html_path.stem.replace("race_schedule_", "")
        target_date = date(int(ds[:4]), int(ds[4:6]), int(ds[6:8]))
        schedule_result = extract_schedule_fixtures(target_date)
        if schedule_result is not None:
            schedule_results.append(schedule_result)

    # テストケース情報を保存
    test_cases: dict[str, list[dict[str, object]]] = {
        "races": race_results,
        "horses": horse_results,
        "schedules": schedule_results,
    }
    test_cases_path = FIXTURES_DIR / "test_cases.json"
    with open(test_cases_path, "w") as f:
        json.dump(test_cases, f, ensure_ascii=False, indent=2)
    print(f"\nテストケース情報を保存: {test_cases_path}")
    print(f"  レース: {len(race_results)}件")
    print(f"  馬: {len(horse_results)}件")
    print(f"  スケジュール: {len(schedule_results)}件")
    print("\n完了!")


if __name__ == "__main__":
    main()
