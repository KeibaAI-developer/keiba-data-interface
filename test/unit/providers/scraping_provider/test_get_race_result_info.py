"""ScrapingProvider.get_race_result_info関数のテスト."""

from unittest.mock import MagicMock

import pandas as pd

from keiba_data_interface.providers.scraping_provider import ScrapingProvider
from keiba_data_interface.schema.columns import RACE_RESULT_INFO_COLUMNS


# 正常系
def test_output_columns_match_schema(
    provider_full: ScrapingProvider,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """出力DataFrameのカラム構成がRACE_RESULT_INFO_COLUMNSと一致する."""
    from .conftest import create_scraping_corner, create_scraping_lap_time

    mock_result_scraper.get_lap_time.return_value = create_scraping_lap_time()
    mock_result_scraper.get_corner.return_value = create_scraping_corner()

    result = provider_full.get_race_result_info(race_code)

    assert list(result.columns) == RACE_RESULT_INFO_COLUMNS


def test_output_is_single_row(
    provider_full: ScrapingProvider,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """出力DataFrameが1行である."""
    from .conftest import create_scraping_corner, create_scraping_lap_time

    mock_result_scraper.get_lap_time.return_value = create_scraping_lap_time()
    mock_result_scraper.get_corner.return_value = create_scraping_corner()

    result = provider_full.get_race_result_info(race_code)

    assert len(result) == 1


def test_lap_time_stored_correctly(
    provider_full: ScrapingProvider,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """ラップタイムが100m刻みカラムに正しく格納される."""
    from .conftest import create_scraping_corner, create_scraping_lap_time

    mock_result_scraper.get_lap_time.return_value = create_scraping_lap_time()
    mock_result_scraper.get_corner.return_value = create_scraping_corner()

    result = provider_full.get_race_result_info(race_code)

    row = result.iloc[0]
    # 2000mレース: 100m〜2000mに値がある
    assert pd.notna(row["ラップ100m"])
    assert pd.notna(row["ラップ2000m"])
    # 2100m以降はNaN
    assert pd.isna(row["ラップ2100m"])
    assert pd.isna(row["ラップ5000m"])


def test_lap_time_beyond_distance_is_nan(
    provider_full: ScrapingProvider,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """レース距離を超えるラップタイムカラムはNaN."""
    from .conftest import create_scraping_corner, create_scraping_lap_time

    mock_result_scraper.get_lap_time.return_value = create_scraping_lap_time()
    mock_result_scraper.get_corner.return_value = create_scraping_corner()

    result = provider_full.get_race_result_info(race_code)

    row = result.iloc[0]
    assert pd.isna(row["ラップ3000m"])
    assert pd.isna(row["ラップ5000m"])


def test_harlon_from_lap(
    provider_full: ScrapingProvider,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """前3ハロン・後3ハロンがラップタイムから格納される."""
    from .conftest import create_scraping_corner, create_scraping_lap_time

    mock_result_scraper.get_lap_time.return_value = create_scraping_lap_time()
    mock_result_scraper.get_corner.return_value = create_scraping_corner()

    result = provider_full.get_race_result_info(race_code)

    row = result.iloc[0]
    assert row["前3ハロン"] == 35.5
    assert row["後3ハロン"] == 34.8


def test_corner_passing_order(
    provider_full: ScrapingProvider,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """コーナー通過順が正しく格納される."""
    from .conftest import create_scraping_corner, create_scraping_lap_time

    mock_result_scraper.get_lap_time.return_value = create_scraping_lap_time()
    mock_result_scraper.get_corner.return_value = create_scraping_corner()

    result = provider_full.get_race_result_info(race_code)

    row = result.iloc[0]
    assert row["1コーナー通過順"] == "3-1-2"
    assert row["2コーナー通過順"] == "3-1-2"
    assert row["3コーナー通過順"] == "1-3-2"
    assert row["4コーナー通過順"] == "1-2-3"


def test_race_code_stored(
    provider_full: ScrapingProvider,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """レースコードが格納される."""
    from .conftest import create_scraping_corner, create_scraping_lap_time

    mock_result_scraper.get_lap_time.return_value = create_scraping_lap_time()
    mock_result_scraper.get_corner.return_value = create_scraping_corner()

    result = provider_full.get_race_result_info(race_code)

    assert result.iloc[0]["レースコード"] == race_code


def test_missing_columns_filled_with_nan(
    provider_full: ScrapingProvider,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """不足カラムがNaN埋めされる."""
    from .conftest import create_scraping_corner, create_scraping_lap_time

    mock_result_scraper.get_lap_time.return_value = create_scraping_lap_time()
    mock_result_scraper.get_corner.return_value = create_scraping_corner()

    result = provider_full.get_race_result_info(race_code)

    row = result.iloc[0]
    assert pd.isna(row["前4ハロン"])
    assert pd.isna(row["後4ハロン"])
    assert pd.isna(row["障害マイルタイム"])
    assert pd.isna(row["1コーナー周回数"])
    assert pd.isna(row["レコード更新区分"])
