"""ScrapingProvider.get_past_performances関数のテスト."""

from unittest.mock import MagicMock

import pandas as pd

from keiba_data_interface.providers.scraping_provider import ScrapingProvider
from keiba_data_interface.schema.columns import HORSE_RACE_INFO_COLUMNS


# 正常系
def test_output_columns_match_schema(
    provider_full: ScrapingProvider,
    mock_past_scraper: MagicMock,
) -> None:
    """出力DataFrameのカラム構成がHORSE_RACE_INFO_COLUMNSと一致する."""
    from .conftest import _create_scraping_past_performances

    mock_past_scraper.get_past_performances.return_value = _create_scraping_past_performances()

    result = provider_full.get_past_performances("2021105001")

    assert list(result.columns) == HORSE_RACE_INFO_COLUMNS


def test_empty_past_performances(
    provider_full: ScrapingProvider,
    mock_past_scraper: MagicMock,
) -> None:
    """新馬（0行）の場合に空DataFrameが返される."""
    mock_past_scraper.get_past_performances.return_value = pd.DataFrame()

    result = provider_full.get_past_performances("2021105001")

    assert len(result) == 0
    assert list(result.columns) == HORSE_RACE_INFO_COLUMNS


def test_date_split(
    provider_full: ScrapingProvider,
    mock_past_scraper: MagicMock,
) -> None:
    """日付が開催年と開催月日に正しく分割される."""
    from .conftest import _create_scraping_past_performances

    mock_past_scraper.get_past_performances.return_value = _create_scraping_past_performances()

    result = provider_full.get_past_performances("2021105001")

    row = result.iloc[0]
    assert row["開催年"] == "2025"
    assert row["開催月日"] == "0105"


def test_prize_money_conversion(
    provider_full: ScrapingProvider,
    mock_past_scraper: MagicMock,
) -> None:
    """賞金の万円→百円単位変換が正しい."""
    from .conftest import _create_scraping_past_performances

    mock_past_scraper.get_past_performances.return_value = _create_scraping_past_performances()

    result = provider_full.get_past_performances("2021105001")

    row = result.iloc[0]
    # 1000万円 → 100000 百円
    assert row["獲得本賞金"] == 100000


def test_opponent_name(
    provider_full: ScrapingProvider,
    mock_past_scraper: MagicMock,
) -> None:
    """勝ち馬(2着馬)が相手1馬名に格納される."""
    from .conftest import _create_scraping_past_performances

    mock_past_scraper.get_past_performances.return_value = _create_scraping_past_performances()

    result = provider_full.get_past_performances("2021105001")

    row = result.iloc[0]
    assert row["相手1馬名"] == "ライバル馬"


def test_result_columns_mapped(
    provider_full: ScrapingProvider,
    mock_past_scraper: MagicMock,
) -> None:
    """結果カラムが正しくマッピングされる."""
    from .conftest import _create_scraping_past_performances

    mock_past_scraper.get_past_performances.return_value = _create_scraping_past_performances()

    result = provider_full.get_past_performances("2021105001")

    row = result.iloc[0]
    assert row["確定着順"] == 1
    assert row["走破タイム"] == "2:00.5"
    assert row["後3ハロン"] == 34.5
    assert row["異常区分コード"] == "0"


def test_zogen_split(
    provider_full: ScrapingProvider,
    mock_past_scraper: MagicMock,
) -> None:
    """増減が増減符号と増減差に正しく分離される."""
    from .conftest import _create_scraping_past_performances

    mock_past_scraper.get_past_performances.return_value = _create_scraping_past_performances()

    result = provider_full.get_past_performances("2021105001")

    row = result.iloc[0]
    assert row["増減符号"] == "+"
    assert row["増減差"] == 2


def test_horse_id_stored(
    provider_full: ScrapingProvider,
    mock_past_scraper: MagicMock,
) -> None:
    """血統登録番号が全行に格納される."""
    from .conftest import _create_scraping_past_performances

    mock_past_scraper.get_past_performances.return_value = _create_scraping_past_performances()

    result = provider_full.get_past_performances("2021105001")

    assert result.iloc[0]["血統登録番号"] == "2021105001"


def test_race_code_derived(
    provider_full: ScrapingProvider,
    mock_past_scraper: MagicMock,
) -> None:
    """レースIDと日付からレースコードが正しく構築される."""
    from .conftest import _create_scraping_past_performances

    mock_past_scraper.get_past_performances.return_value = _create_scraping_past_performances()

    result = provider_full.get_past_performances("2021105001")

    # レースID=202505011201, 日付=2025-01-05 → レースコード=2025010505011201
    assert result.iloc[0]["レースコード"] == "2025010505011201"
