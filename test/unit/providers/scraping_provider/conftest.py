"""ScrapingProviderテスト用のfixture."""

from collections.abc import Generator
from datetime import date
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from keiba_data_interface.providers.scraping_provider import ScrapingProvider


def create_scraping_race_info(
    shiba_da: str = "芝",
    baba: str = "良",
    sayuu: str = "左",
    course: str = "A",
    uchisoto: str = "",
    race_shubetsu: str = "平地",
) -> pd.DataFrame:
    """scraping出力の典型的なレース情報DataFrameを生成する.

    Args:
        shiba_da (str): 芝ダ区分
        baba (str): 馬場状態
        sayuu (str): 左右
        course (str): コース
        uchisoto (str): 内外
        race_shubetsu (str): レース種別

    Returns:
        pd.DataFrame: scraping出力形式のレース情報
    """
    return pd.DataFrame(
        [
            {
                "レースID": "202506021211",
                "日付": date(2025, 5, 2),
                "曜日": "日",
                "レース名": "天皇賞(春)",
                "発走時刻": "15:40",
                "天候": "晴",
                "馬場": baba,
                "レース種別": race_shubetsu,
                "芝ダ": shiba_da,
                "距離": 3200,
                "左右": sayuu,
                "コース": course,
                "内外": uchisoto,
                "競馬場": "京都",
                "回": 3,
                "開催日": 4,
                "競走種別": "サラ系4歳以上",
                "競走条件": "オープン",
                "グレード": "G1",
                "競走記号": "(国際)(指)",
                "重量種別": "定量",
                "頭数": 18,
                "1着賞金": 32000,
                "2着賞金": 12800,
                "3着賞金": 8000,
                "4着賞金": 4800,
                "5着賞金": 3200,
            }
        ]
    )


def create_scraping_entry() -> pd.DataFrame:
    """scraping出力の典型的な出馬表DataFrameを生成する."""
    return pd.DataFrame(
        [
            {
                "レースID": "202506021211",
                "出走区分": "出走",
                "枠": 1,
                "馬番": 1,
                "馬名": "テスト馬1",
                "性別": "牡",
                "年齢": 4,
                "斤量": 58.0,
                "騎手": "テスト騎手1",
                "所属": "栗東",
                "厩舎": "テスト厩舎1",
                "馬体重": 480,
                "増減": 2,
                "馬ID": "2021105001",
                "騎手ID": "01234",
                "厩舎ID": "01111",
            },
            {
                "レースID": "202506021211",
                "出走区分": "出走",
                "枠": 2,
                "馬番": 2,
                "馬名": "テスト馬2",
                "性別": "牝",
                "年齢": 5,
                "斤量": 56.0,
                "騎手": "テスト騎手2",
                "所属": "美浦",
                "厩舎": "テスト厩舎2",
                "馬体重": 440,
                "増減": -4,
                "馬ID": "2020105002",
                "騎手ID": "05678",
                "厩舎ID": "02222",
            },
        ]
    )


def create_scraping_result() -> pd.DataFrame:
    """scraping出力の典型的なレース結果DataFrameを生成する."""
    return pd.DataFrame(
        [
            {
                "レースID": "202506021211",
                "異常区分": "出走",
                "着順": "1",
                "枠": 2,
                "馬番": 3,
                "馬名": "テスト馬1",
                "性別": "牡",
                "年齢": 4,
                "斤量": 58.0,
                "騎手": "テスト騎手1",
                "タイム": "3:12.5",
                "着差": "",
                "人気": "1",
                "単勝オッズ": 3.5,
                "後3F": 35.2,
                "1コーナー通過順": 3,
                "2コーナー通過順": 2,
                "3コーナー通過順": 2,
                "4コーナー通過順": 1,
                "所属": "栗東",
                "厩舎": "テスト厩舎1",
                "馬体重": 480,
                "増減": 2,
                "馬ID": "2021105001",
                "騎手ID": "01234",
                "厩舎ID": "01111",
            },
            {
                "レースID": "202506021211",
                "異常区分": "出走",
                "着順": "2",
                "枠": 1,
                "馬番": 1,
                "馬名": "テスト馬2",
                "性別": "牝",
                "年齢": 5,
                "斤量": 56.0,
                "騎手": "テスト騎手2",
                "タイム": "3:13.0",
                "着差": "クビ",
                "人気": "3",
                "単勝オッズ": 8.2,
                "後3F": 35.5,
                "1コーナー通過順": 5,
                "2コーナー通過順": 5,
                "3コーナー通過順": 4,
                "4コーナー通過順": 3,
                "所属": "美浦",
                "厩舎": "テスト厩舎2",
                "馬体重": 440,
                "増減": -4,
                "馬ID": "2020105002",
                "騎手ID": "05678",
                "厩舎ID": "02222",
            },
        ]
    )


def create_scraping_odds() -> pd.DataFrame:
    """scraping出力の典型的なオッズDataFrameを生成する."""
    return pd.DataFrame(
        [
            {
                "馬番": 1,
                "単勝オッズ": 3.5,
                "単勝人気": 1,
                "複勝最小オッズ": 1.5,
                "複勝最大オッズ": 2.0,
                "複勝人気": 1,
            },
            {
                "馬番": 2,
                "単勝オッズ": 8.2,
                "単勝人気": 3,
                "複勝最小オッズ": 2.5,
                "複勝最大オッズ": 4.0,
                "複勝人気": 3,
            },
        ]
    )


def create_scraping_lap_time() -> pd.DataFrame:
    """scraping出力の典型的なラップタイムDataFrameを生成する."""
    data: dict[str, object] = {"レースID": "202506021211", "ペース": "M"}
    # 2000mレースの場合: 100m〜2000mに値, 2100m以降はNaN
    for dist in range(100, 5001, 100):
        col = f"{dist}m"
        if dist <= 2000:
            data[col] = 12.0 + (dist % 400) / 100
        else:
            data[col] = None
    data["レース前3F"] = 35.5
    data["レース後3F"] = 34.8
    return pd.DataFrame([data])


def create_scraping_corner() -> pd.DataFrame:
    """scraping出力の典型的なコーナー通過順DataFrameを生成する."""
    return pd.DataFrame(
        [
            {
                "レースID": "202506021211",
                "1コーナー通過順": "3-1-2",
                "2コーナー通過順": "3-1-2",
                "3コーナー通過順": "1-3-2",
                "4コーナー通過順": "1-2-3",
            }
        ]
    )


def create_scraping_past_performances() -> pd.DataFrame:
    """scraping出力の典型的な過去成績DataFrameを生成する."""
    return pd.DataFrame(
        [
            {
                "レースID": "202505011201",
                "日付": date(2025, 1, 5),
                "競馬場": "中山",
                "回": 1,
                "開催日": 1,
                "R": 12,
                "レース名": "テストレース",
                "天候": "晴",
                "頭数": 16,
                "枠": 3,
                "馬番": 5,
                "単勝オッズ": 5.0,
                "人気": "2",
                "着順": "1",
                "異常区分": "出走",
                "騎手": "テスト騎手",
                "騎手ID": "01234",
                "斤量": 57.0,
                "芝ダ": "芝",
                "距離": 2000,
                "馬場": "良",
                "タイム": "2:00.5",
                "着差": 0.5,
                "1コーナー通過順": 3,
                "2コーナー通過順": 3,
                "3コーナー通過順": 2,
                "4コーナー通過順": 1,
                "レース前3F": 35.5,
                "レース後3F": 34.8,
                "後3F": 34.5,
                "馬体重": 480,
                "増減": 2,
                "勝ち馬(2着馬)": "ライバル馬",
                "賞金": 1000,
                "主催": "JRA",
                "間隔日数": 28,
            },
        ]
    )


def create_scraping_schedule() -> pd.DataFrame:
    """scraping出力の典型的な開催スケジュールDataFrameを生成する."""
    return pd.DataFrame(
        [
            {
                "レースID": "202505010101",
                "日付": date(2025, 1, 5),
                "競馬場": "中山",
                "回": 1,
                "開催日": 1,
                "R": 1,
                "レース名": "3歳未勝利",
                "芝ダ": "芝",
                "距離": 2000,
                "頭数": 16,
                "馬場": "良",
                "発走時刻": "10:00",
            },
            {
                "レースID": "202505010102",
                "日付": date(2025, 1, 5),
                "競馬場": "中山",
                "回": 1,
                "開催日": 1,
                "R": 2,
                "レース名": "3歳未勝利",
                "芝ダ": "ダ",
                "距離": 1800,
                "頭数": 14,
                "馬場": "良",
                "発走時刻": "10:30",
            },
            {
                "レースID": "202506020101",
                "日付": date(2025, 1, 5),
                "競馬場": "京都",
                "回": 2,
                "開催日": 1,
                "R": 1,
                "レース名": "3歳新馬",
                "芝ダ": "芝",
                "距離": 1600,
                "頭数": 12,
                "馬場": "良",
                "発走時刻": "10:10",
            },
        ]
    )


@pytest.fixture()
def turf_race_info() -> pd.DataFrame:
    """芝レースのscraping出力を返すfixture."""
    return create_scraping_race_info(shiba_da="芝", baba="良")


@pytest.fixture()
def dirt_race_info() -> pd.DataFrame:
    """ダートレースのscraping出力を返すfixture."""
    return create_scraping_race_info(shiba_da="ダ", baba="重", sayuu="右")


@pytest.fixture()
def mock_scraper() -> MagicMock:
    """EntryPageScraperインスタンスのモックを返すfixture."""
    return MagicMock()


@pytest.fixture()
def mock_scraper_cls(mock_scraper: MagicMock) -> Generator[MagicMock, None, None]:
    """EntryPageScraperをパッチしたモッククラスを返すfixture.

    Yields:
        MagicMock: EntryPageScraperクラスのパッチモック。
    """
    with patch(
        "keiba_data_interface.providers.scraping_provider.EntryPageScraper",
        return_value=mock_scraper,
    ) as mock_cls:
        yield mock_cls


@pytest.fixture()
def mock_result_scraper() -> MagicMock:
    """ResultPageScraperインスタンスのモックを返すfixture."""
    return MagicMock()


@pytest.fixture()
def mock_result_scraper_cls(mock_result_scraper: MagicMock) -> Generator[MagicMock, None, None]:
    """ResultPageScraperをパッチしたモッククラスを返すfixture.

    Yields:
        MagicMock: ResultPageScraperクラスのパッチモック。
    """
    with patch(
        "keiba_data_interface.providers.scraping_provider.ResultPageScraper",
        return_value=mock_result_scraper,
    ) as mock_cls:
        yield mock_cls


@pytest.fixture()
def mock_odds_func() -> Generator[MagicMock, None, None]:
    """scrape_odds_from_jraをパッチしたモック関数を返すfixture.

    Yields:
        MagicMock: scrape_odds_from_jraのパッチモック。
    """
    with patch(
        "keiba_data_interface.providers.scraping_provider.scrape_odds_from_jra"
    ) as mock_func:
        yield mock_func


@pytest.fixture()
def mock_past_scraper() -> MagicMock:
    """PastPerformancesScraperインスタンスのモックを返すfixture."""
    return MagicMock()


@pytest.fixture()
def mock_past_scraper_cls(mock_past_scraper: MagicMock) -> Generator[MagicMock, None, None]:
    """PastPerformancesScraperをパッチしたモッククラスを返すfixture.

    Yields:
        MagicMock: PastPerformancesScraperクラスのパッチモック。
    """
    with patch(
        "keiba_data_interface.providers.scraping_provider.PastPerformancesScraper",
        return_value=mock_past_scraper,
    ) as mock_cls:
        yield mock_cls


@pytest.fixture()
def mock_schedule_scraper() -> MagicMock:
    """RaceScheduleScraperインスタンスのモックを返すfixture."""
    return MagicMock()


@pytest.fixture()
def mock_schedule_scraper_cls(mock_schedule_scraper: MagicMock) -> Generator[MagicMock, None, None]:
    """RaceScheduleScraperをパッチしたモッククラスを返すfixture.

    Yields:
        MagicMock: RaceScheduleScraperクラスのパッチモック。
    """
    with patch(
        "keiba_data_interface.providers.scraping_provider.RaceScheduleScraper",
        return_value=mock_schedule_scraper,
    ) as mock_cls:
        yield mock_cls


@pytest.fixture()
def provider(mock_scraper_cls: MagicMock) -> ScrapingProvider:
    """ScrapingProvider（EntryPageScraper用メソッド向け）を返すfixture."""
    return ScrapingProvider()


@pytest.fixture()
def provider_full(
    mock_scraper_cls: MagicMock,
    mock_result_scraper_cls: MagicMock,
    mock_odds_func: MagicMock,
    mock_past_scraper_cls: MagicMock,
    mock_schedule_scraper_cls: MagicMock,
) -> ScrapingProvider:
    """全モックをパッチ済みのScrapingProviderを返すfixture."""
    return ScrapingProvider()


@pytest.fixture()
def race_code() -> str:
    """テスト用16桁レースコードを返すfixture."""
    return "2025050206021211"
