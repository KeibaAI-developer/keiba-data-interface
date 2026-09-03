"""出馬表ページの再利用のテスト."""

from unittest.mock import MagicMock, patch

import pytest

from keiba_data_interface.providers.scraping_provider import ScrapingProvider

from .conftest import create_scraping_entry, create_scraping_race_info, create_scraping_result

_MONOTONIC = "keiba_data_interface.providers.scraping_provider.time.monotonic"


@pytest.fixture()
def prepared_scraper(mock_scraper: MagicMock) -> MagicMock:
    """レース情報と出馬表を返す EntryPageScraper のモック."""
    mock_scraper.get_race_info.return_value = create_scraping_race_info()
    mock_scraper.get_entry.return_value = create_scraping_entry()
    return mock_scraper


# 正常系
def test_reuses_page_within_seconds(
    provider: ScrapingProvider,
    mock_scraper_cls: MagicMock,
    prepared_scraper: MagicMock,
    race_code: str,
) -> None:
    """同じレースのレース基本情報と出馬表を続けて取ると、ページは 1 回だけ取得する."""
    provider.get_race_basic_info(race_code)
    provider.get_entry(race_code)

    assert mock_scraper_cls.call_count == 1


def test_result_reuses_page(
    provider_full: ScrapingProvider,
    mock_scraper_cls: MagicMock,
    prepared_scraper: MagicMock,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """レース結果の賞金情報も直近の出馬表ページを使う."""
    mock_result_scraper.get_result.return_value = create_scraping_result()

    provider_full.get_entry(race_code)
    provider_full.get_result(race_code)

    assert mock_scraper_cls.call_count == 1


def test_fetches_again_after_seconds(
    mock_scraper_cls: MagicMock, prepared_scraper: MagicMock, race_code: str
) -> None:
    """再利用する秒数を過ぎていれば取得し直す."""
    provider = ScrapingProvider(entry_page_reuse_seconds=60.0)
    with patch(_MONOTONIC, side_effect=[100.0, 170.0, 170.0]):
        provider.get_race_basic_info(race_code)
        provider.get_entry(race_code)

    assert mock_scraper_cls.call_count == 2


def test_fetches_again_for_other_race(
    provider: ScrapingProvider, mock_scraper_cls: MagicMock, prepared_scraper: MagicMock
) -> None:
    """別のレースは取得し直す."""
    provider.get_entry("2025050206021211")
    provider.get_entry("2025050206021212")

    assert mock_scraper_cls.call_count == 2


def test_zero_seconds_disables_reuse(
    mock_scraper_cls: MagicMock, prepared_scraper: MagicMock, race_code: str
) -> None:
    """再利用する秒数が 0 なら毎回取得する."""
    provider = ScrapingProvider(entry_page_reuse_seconds=0)

    provider.get_race_basic_info(race_code)
    provider.get_entry(race_code)

    assert mock_scraper_cls.call_count == 2


# 準正常系
def test_negative_seconds_raises() -> None:
    """再利用する秒数が負なら ValueError."""
    with pytest.raises(ValueError, match="entry_page_reuse_seconds"):
        ScrapingProvider(entry_page_reuse_seconds=-1)
