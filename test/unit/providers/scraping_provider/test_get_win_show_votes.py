"""ScrapingProvider.get_win_show_votes関数のテスト."""

import pytest

from keiba_data_interface.exceptions import DataNotFoundError
from keiba_data_interface.providers.scraping_provider import ScrapingProvider


# 準正常系
def test_raises_data_not_found_error(provider_full: ScrapingProvider, race_code: str) -> None:
    """scrapingプロバイダーは票数を取得できないためDataNotFoundErrorになる."""
    with pytest.raises(DataNotFoundError, match="票数"):
        provider_full.get_win_show_votes(race_code)
