"""両Provider出力一致テスト用のfixture."""

import json
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.providers.scraping_provider import ScrapingProvider

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture(path: Path) -> pd.DataFrame:
    """フィクスチャファイルをpickle形式で読み込む.

    Args:
        path (Path): フィクスチャファイルのパス（拡張子なし or .pkl）

    Returns:
        pd.DataFrame: 読み込んだDataFrame
    """
    pkl_path = path.with_suffix(".pkl")
    return pd.read_pickle(pkl_path)


def _load_fixture_optional(path: Path) -> pd.DataFrame:
    """フィクスチャファイルをpickle形式で読み込む（ファイルが存在しない場合は空のDataFrameを返す）.

    Args:
        path (Path): フィクスチャファイルのパス（拡張子なし or .pkl）

    Returns:
        pd.DataFrame: 読み込んだDataFrame。ファイルが存在しない場合は空のDataFrame
    """
    pkl_path = path.with_suffix(".pkl")
    if not pkl_path.exists():
        return pd.DataFrame()
    return pd.read_pickle(pkl_path)


def _load_test_cases() -> dict[str, list[dict[str, str]]]:
    """テストケース情報を読み込む."""
    with open(FIXTURES_DIR / "test_cases.json", encoding="utf-8") as f:
        return json.load(f)


# テストケース情報
TEST_CASES = _load_test_cases()

# テスト用レースのレースコード一覧
RACE_CODES: list[str] = [r["race_code"] for r in TEST_CASES["races"]]


class RaceFixtures:
    """1レース分のフィクスチャデータを保持するクラス.

    Attributes:
        race_code (str): 16桁レースコード
        race_name (str): レース名
        scraping (dict[str, pd.DataFrame]): scraping側のrawデータ
        mykeibadb (dict[str, pd.DataFrame]): mykeibadb側のrawデータ
    """

    def __init__(self, race_code: str, race_name: str) -> None:
        """コンストラクタ.

        Args:
            race_code (str): 16桁レースコード
            race_name (str): レース名
        """
        self.race_code = race_code
        self.race_name = race_name
        race_dir = FIXTURES_DIR / "races" / race_code

        # Scraping側
        self.scraping: dict[str, pd.DataFrame] = {
            "race_info": _load_fixture(race_dir / "scraping_race_info"),
            "entry": _load_fixture_optional(race_dir / "scraping_entry"),
            "result": _load_fixture(race_dir / "scraping_result"),
            "lap_time": _load_fixture(race_dir / "scraping_lap_time"),
            "corner": _load_fixture(race_dir / "scraping_corner"),
            "odds": _load_fixture(race_dir / "scraping_odds"),
            "payoff_win": _load_fixture(race_dir / "scraping_payoff_win"),
            "payoff_show": _load_fixture(race_dir / "scraping_payoff_show"),
            "payoff_bracket": _load_fixture(race_dir / "scraping_payoff_bracket"),
            "payoff_quinella": _load_fixture(race_dir / "scraping_payoff_quinella"),
            "payoff_quinella_place": _load_fixture(race_dir / "scraping_payoff_quinella_place"),
            "payoff_exacta": _load_fixture(race_dir / "scraping_payoff_exacta"),
            "payoff_trio": _load_fixture(race_dir / "scraping_payoff_trio"),
            "payoff_trifecta": _load_fixture(race_dir / "scraping_payoff_trifecta"),
        }

        # MykeibaDB側
        self.mykeibadb: dict[str, pd.DataFrame] = {
            "race_shosai": _load_fixture(race_dir / "mykeibadb_race_shosai"),
            "umagoto_race_joho": _load_fixture(race_dir / "mykeibadb_umagoto_race_joho"),
            "haraimodoshi": _load_fixture(race_dir / "mykeibadb_haraimodoshi"),
            "odds1_tansho": _load_fixture(race_dir / "mykeibadb_odds1_tansho"),
            "odds1_fukusho": _load_fixture(race_dir / "mykeibadb_odds1_fukusho"),
        }


class HorseFixtures:
    """1頭分のフィクスチャデータを保持するクラス.

    Attributes:
        horse_id (str): 馬ID（血統登録番号）
        horse_name (str): 馬名
        scraping (dict[str, pd.DataFrame]): scraping側のrawデータ
        mykeibadb (dict[str, pd.DataFrame]): mykeibadb側のrawデータ
    """

    def __init__(self, horse_id: str, horse_name: str) -> None:
        """コンストラクタ.

        Args:
            horse_id (str): 馬ID
            horse_name (str): 馬名
        """
        self.horse_id = horse_id
        self.horse_name = horse_name
        horse_dir = FIXTURES_DIR / "horses" / horse_id

        self.scraping: dict[str, pd.DataFrame] = {
            "past_performances": _load_fixture(horse_dir / "scraping_past_performances"),
            "horse_basic_info": _load_fixture_optional(horse_dir / "scraping_horse_basic_info"),
        }
        self.mykeibadb: dict[str, pd.DataFrame] = {
            "umagoto_race_joho": _load_fixture(horse_dir / "mykeibadb_umagoto_race_joho"),
            "kyosoba_master2": _load_fixture(horse_dir / "mykeibadb_kyosoba_master2"),
        }


class ScheduleFixtures:
    """スケジュールのフィクスチャデータを保持するクラス.

    Attributes:
        target_date (str): 対象日（YYYY-MM-DD形式）
        scraping (dict[str, pd.DataFrame]): scraping側のrawデータ
        mykeibadb (dict[str, pd.DataFrame]): mykeibadb側のrawデータ
    """

    def __init__(self, target_date: str) -> None:
        """コンストラクタ.

        Args:
            target_date (str): 対象日（YYYY-MM-DD形式）
        """
        self.target_date = target_date
        date_str = target_date.replace("-", "")
        sched_dir = FIXTURES_DIR / "schedules" / date_str

        self.scraping: dict[str, pd.DataFrame] = {
            "schedule": _load_fixture(sched_dir / "scraping_schedule"),
        }
        self.mykeibadb: dict[str, pd.DataFrame] = {
            "kaisai_schedule": _load_fixture(sched_dir / "mykeibadb_kaisai_schedule"),
        }


def _create_scraping_provider(
    fixtures: RaceFixtures,
) -> tuple[ScrapingProvider, dict[str, MagicMock]]:
    """フィクスチャデータでモックされたScrapingProviderを生成する.

    Args:
        fixtures (RaceFixtures): レースフィクスチャ

    Returns:
        tuple[ScrapingProvider, dict[str, MagicMock]]: Provider + パッチモックの辞書
    """
    mocks: dict[str, MagicMock] = {}

    # EntryPageScraper
    mock_entry_scraper = MagicMock()
    mock_entry_scraper.get_race_info.return_value = fixtures.scraping["race_info"]
    mock_entry_scraper.get_entry.return_value = fixtures.scraping["entry"]
    mocks["entry_scraper"] = mock_entry_scraper

    # ResultPageScraper
    mock_result_scraper = MagicMock()
    mock_result_scraper.get_result.return_value = fixtures.scraping["result"]
    mock_result_scraper.get_lap_time.return_value = fixtures.scraping["lap_time"]
    mock_result_scraper.get_corner.return_value = fixtures.scraping["corner"]
    mock_result_scraper.get_win_payoff.return_value = fixtures.scraping["payoff_win"]
    mock_result_scraper.get_show_payoff.return_value = fixtures.scraping["payoff_show"]
    mock_result_scraper.get_bracket_payoff.return_value = fixtures.scraping["payoff_bracket"]
    mock_result_scraper.get_quinella_payoff.return_value = fixtures.scraping["payoff_quinella"]
    mock_result_scraper.get_quinella_place_payoff.return_value = fixtures.scraping[
        "payoff_quinella_place"
    ]
    mock_result_scraper.get_exacta_payoff.return_value = fixtures.scraping["payoff_exacta"]
    mock_result_scraper.get_trio_payoff.return_value = fixtures.scraping["payoff_trio"]
    mock_result_scraper.get_trifecta_payoff.return_value = fixtures.scraping["payoff_trifecta"]
    mocks["result_scraper"] = mock_result_scraper

    return ScrapingProvider(), mocks


def _create_mykeibadb_mocks(
    fixtures: RaceFixtures,
) -> dict[str, MagicMock]:
    """MykeibaDBProvider用のモック辞書を生成する.

    Args:
        fixtures (RaceFixtures): レースフィクスチャ

    Returns:
        dict[str, MagicMock]: パッチモックの辞書
    """
    mock_race_getter = MagicMock()
    mock_race_getter.get_race_shosai.return_value = fixtures.mykeibadb["race_shosai"]
    mock_race_getter.get_umagoto_race_joho.return_value = fixtures.mykeibadb["umagoto_race_joho"]
    mock_race_getter.get_haraimodoshi.return_value = fixtures.mykeibadb["haraimodoshi"]

    mock_odds_getter = MagicMock()
    mock_odds_getter.get_odds1_tansho.return_value = fixtures.mykeibadb["odds1_tansho"]
    mock_odds_getter.get_odds1_fukusho.return_value = fixtures.mykeibadb["odds1_fukusho"]

    return {"race_getter": mock_race_getter, "odds_getter": mock_odds_getter}


@pytest.fixture(params=RACE_CODES)
def race_fixtures(request: pytest.FixtureRequest) -> RaceFixtures:
    """テスト用レースフィクスチャ.

    test_cases.jsonから選択された各レースに対してパラメータ化される。
    """
    race_code: str = request.param
    race_info = next(r for r in TEST_CASES["races"] if r["race_code"] == race_code)
    return RaceFixtures(race_code, race_info["name"])


@pytest.fixture()
def horse_fixtures() -> HorseFixtures:
    """テスト用馬フィクスチャ."""
    horse_info = TEST_CASES["horses"][0]
    return HorseFixtures(horse_info["horse_id"], horse_info["name"])


@pytest.fixture()
def schedule_fixtures() -> ScheduleFixtures:
    """テスト用スケジュールフィクスチャ."""
    sched_info = TEST_CASES["schedules"][0]
    return ScheduleFixtures(sched_info["date"])


@pytest.fixture()
def scraping_provider_with_mocks(
    race_fixtures: RaceFixtures,
) -> Generator[tuple[ScrapingProvider, RaceFixtures], None, None]:
    """モック済みScrapingProviderを返すfixture.

    Yields:
        tuple[ScrapingProvider, RaceFixtures]: ScrapingProviderとフィクスチャのペア
    """
    provider, mocks = _create_scraping_provider(race_fixtures)

    with (
        patch(
            "keiba_data_interface.providers.scraping_provider.EntryPageScraper",
            return_value=mocks["entry_scraper"],
        ),
        patch(
            "keiba_data_interface.providers.scraping_provider.ResultPageScraper",
            return_value=mocks["result_scraper"],
        ),
        patch(
            "keiba_data_interface.providers.scraping_provider.scrape_odds_from_jra",
            return_value=race_fixtures.scraping["odds"],
        ),
    ):
        yield provider, race_fixtures


@pytest.fixture()
def mykeibadb_provider_with_mocks(
    race_fixtures: RaceFixtures,
) -> Generator[tuple[MykeibaDBProvider, RaceFixtures], None, None]:
    """モック済みMykeibaDBProviderを返すfixture.

    Yields:
        tuple[MykeibaDBProvider, RaceFixtures]: MykeibaDBProviderとフィクスチャのペア
    """
    mocks = _create_mykeibadb_mocks(race_fixtures)

    with (
        patch(
            "keiba_data_interface.providers.mykeibadb_provider.RaceGetter",
            return_value=mocks["race_getter"],
        ),
        patch(
            "keiba_data_interface.providers.mykeibadb_provider.OddsGetter",
            return_value=mocks["odds_getter"],
        ),
    ):
        yield MykeibaDBProvider(), race_fixtures
