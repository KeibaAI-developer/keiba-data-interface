"""ScrapingProvider.get_chakudosu関数のテスト."""

from unittest.mock import MagicMock

import pandas as pd

from keiba_data_interface.providers.scraping_provider import ScrapingProvider
from keiba_data_interface.schema.columns import CHAKUDOSU_COLUMNS

from .conftest import create_scraping_entry, create_scraping_past_performances

RACE_CODE = "2025050206050811"


# 正常系
def test_output_columns_match_schema(
    provider_full: ScrapingProvider,
    mock_scraper: MagicMock,
    mock_past_scraper: MagicMock,
) -> None:
    """出力DataFrameのカラム構成がCHAKUDOSU_COLUMNSと一致する."""
    mock_scraper.get_entry.return_value = create_scraping_entry()
    mock_past_scraper.get_past_performances.return_value = create_scraping_past_performances()

    result = provider_full.get_chakudosu(RACE_CODE)

    assert list(result.columns) == CHAKUDOSU_COLUMNS


def test_output_row_count_matches_entry(
    provider_full: ScrapingProvider,
    mock_scraper: MagicMock,
    mock_past_scraper: MagicMock,
) -> None:
    """出力DataFrameの行数が出走頭数分である."""
    mock_scraper.get_entry.return_value = create_scraping_entry()
    mock_past_scraper.get_past_performances.return_value = create_scraping_past_performances()

    result = provider_full.get_chakudosu(RACE_CODE)

    assert len(result) == 2


def test_sorted_by_ketto_toroku_bango(
    provider_full: ScrapingProvider,
    mock_scraper: MagicMock,
    mock_past_scraper: MagicMock,
) -> None:
    """出力DataFrameが血統登録番号昇順である."""
    mock_scraper.get_entry.return_value = create_scraping_entry()
    mock_past_scraper.get_past_performances.return_value = create_scraping_past_performances()

    result = provider_full.get_chakudosu(RACE_CODE)

    assert list(result["血統登録番号"]) == ["2020105002", "2021105001"]


def test_key_columns_mapped_from_entry(
    provider_full: ScrapingProvider,
    mock_scraper: MagicMock,
    mock_past_scraper: MagicMock,
) -> None:
    """レースコード・血統登録番号・馬名が出馬表から正しくマッピングされる."""
    mock_scraper.get_entry.return_value = create_scraping_entry()
    mock_past_scraper.get_past_performances.return_value = create_scraping_past_performances()

    result = provider_full.get_chakudosu(RACE_CODE)

    row = result[result["血統登録番号"] == "2021105001"].iloc[0]
    assert row["レースコード"] == RACE_CODE
    assert row["馬名"] == "テスト馬1"


def test_past_performances_aggregated(
    provider_full: ScrapingProvider,
    mock_scraper: MagicMock,
    mock_past_scraper: MagicMock,
) -> None:
    """各馬の馬柱から条件別着回数が集計される."""
    mock_scraper.get_entry.return_value = create_scraping_entry()
    mock_past_scraper.get_past_performances.return_value = create_scraping_past_performances()

    result = provider_full.get_chakudosu(RACE_CODE)

    # create_scraping_past_performancesは2025-01-05・中山・芝・2000m・良・着順1
    row = result[result["血統登録番号"] == "2021105001"].iloc[0]
    assert row["中山芝1着"] == 1
    assert row["芝1801-20001着"] == 1


# 準正常系
def test_new_horse_columns_are_zero(
    provider_full: ScrapingProvider,
    mock_scraper: MagicMock,
    mock_past_scraper: MagicMock,
) -> None:
    """中央出走歴のない馬は着回数カラムがすべて0になる."""
    mock_scraper.get_entry.return_value = create_scraping_entry()
    mock_past_scraper.get_past_performances.return_value = pd.DataFrame()

    result = provider_full.get_chakudosu(RACE_CODE)

    row = result.iloc[0]
    assert row["中山芝1着"] == 0
