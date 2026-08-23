"""ScrapingProvider.get_race_basic_info_bulk関数のテスト."""

import pytest

from keiba_data_interface.exceptions import DataNotFoundError
from keiba_data_interface.providers.scraping_provider import ScrapingProvider


# 異常系
@pytest.mark.parametrize(
    "race_codes",
    [
        [],
        ["2025050206050811"],
        ["2025050206050811", "2025050206050812"],
    ],
)
def test_raises_data_not_found_error(
    provider: ScrapingProvider, race_codes: list[str]
) -> None:
    """常にDataNotFoundErrorを送出する.

    netkeibaには複数レースをまとめて取得する手段がなく、レース数ぶんのページ
    スクレイピングになるため実装していない。
    """
    with pytest.raises(DataNotFoundError, match="一括取得に対応していません"):
        provider.get_race_basic_info_bulk(race_codes)
