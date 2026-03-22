"""ScrapingProvider.get_race_infoテスト用のfixture."""

from datetime import date
from unittest.mock import MagicMock

import pandas as pd
import pytest

from keiba_data_interface.providers.scraping_provider import ScrapingProvider


def _create_scraping_race_info(
    shiba_da: str = "芝",
    baba: str = "良",
    sayuu: str = "左",
    course: str = "A",
    uchisoto: str = "",
) -> pd.DataFrame:
    """scraping出力の典型的なレース情報DataFrameを生成する.

    Args:
        shiba_da (str): 芝ダ区分
        baba (str): 馬場状態
        sayuu (str): 左右
        course (str): コース
        uchisoto (str): 内外

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


@pytest.fixture()
def turf_race_info() -> pd.DataFrame:
    """芝レースのscraping出力を返すfixture."""
    return _create_scraping_race_info(shiba_da="芝", baba="良")


@pytest.fixture()
def dirt_race_info() -> pd.DataFrame:
    """ダートレースのscraping出力を返すfixture."""
    return _create_scraping_race_info(shiba_da="ダ", baba="重", sayuu="右")


@pytest.fixture()
def mock_scraper() -> MagicMock:
    """EntryPageScraperインスタンスのモックを返すfixture."""
    return MagicMock()


@pytest.fixture()
def mock_scraper_cls(mock_scraper: MagicMock) -> MagicMock:
    """EntryPageScraperクラスのモックを返すfixture."""
    mock_cls = MagicMock(return_value=mock_scraper)
    return mock_cls


@pytest.fixture()
def provider(mock_scraper_cls: MagicMock) -> ScrapingProvider:
    """ScrapingProviderインスタンスを返すfixture."""
    return ScrapingProvider(scraper_class=mock_scraper_cls)


@pytest.fixture()
def race_code() -> str:
    """テスト用16桁レースコードを返すfixture."""
    return "2025050206021211"
