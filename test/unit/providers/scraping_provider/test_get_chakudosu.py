"""ScrapingProvider.get_chakudosu関数のテスト."""

import pytest

from keiba_data_interface.exceptions import DataNotFoundError
from keiba_data_interface.providers.scraping_provider import ScrapingProvider


# 準正常系
def test_raises_data_not_found_error() -> None:
    """get_chakudosuがDataNotFoundErrorを送出する."""
    provider = ScrapingProvider()

    with pytest.raises(DataNotFoundError, match="出走別着度数を取得できません"):
        provider.get_chakudosu("2025050206050811")
