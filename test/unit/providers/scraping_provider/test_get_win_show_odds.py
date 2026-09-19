"""ScrapingProvider.get_win_show_odds関数のテスト."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from scraping.exceptions import PageNotFoundError

from keiba_data_interface.exceptions import DataNotFoundError
from keiba_data_interface.odds_source import OddsSource
from keiba_data_interface.providers.scraping_provider import ScrapingProvider
from keiba_data_interface.schema.columns import WIN_SHOW_ODDS_COLUMNS

_NETKEIBA_FUNC = "keiba_data_interface.providers.scraping_provider.scrape_odds_from_netkeiba"


# 正常系
def test_output_columns_match_schema(
    provider_full: ScrapingProvider,
    mock_odds_func: MagicMock,
    race_code: str,
) -> None:
    """出力DataFrameのカラム構成がODDS_COLUMNSと一致する."""
    from .conftest import create_scraping_odds

    mock_odds_func.return_value = create_scraping_odds()

    result = provider_full.get_win_show_odds(race_code)

    assert list(result.columns) == WIN_SHOW_ODDS_COLUMNS


def test_output_row_count(
    provider_full: ScrapingProvider,
    mock_odds_func: MagicMock,
    race_code: str,
) -> None:
    """出力DataFrameの行数が入力と一致する."""
    from .conftest import create_scraping_odds

    mock_odds_func.return_value = create_scraping_odds()

    result = provider_full.get_win_show_odds(race_code)

    assert len(result) == 2


def test_header_columns_from_race_code(
    provider_full: ScrapingProvider,
    mock_odds_func: MagicMock,
    race_code: str,
) -> None:
    """ヘッダカラムがレースコードから正しく導出される."""
    from .conftest import create_scraping_odds

    mock_odds_func.return_value = create_scraping_odds()

    result = provider_full.get_win_show_odds(race_code)

    row = result.iloc[0]
    assert row["レースコード"] == race_code
    assert row["開催年"] == "2025"
    assert row["開催月日"] == "0502"
    assert row["競馬場コード"] == "06"
    assert row["開催回"] == 2
    assert row["開催日目"] == 12
    assert row["レース番号"] == 11


def test_odds_rename(
    provider_full: ScrapingProvider,
    mock_odds_func: MagicMock,
    race_code: str,
) -> None:
    """複勝最小/最大オッズが複勝最低/最高オッズにリネームされる."""
    from .conftest import create_scraping_odds

    mock_odds_func.return_value = create_scraping_odds()

    result = provider_full.get_win_show_odds(race_code)

    row = result.iloc[0]
    assert row["複勝最低オッズ"] == 1.5
    assert row["複勝最高オッズ"] == 2.0


def test_odds_values(
    provider_full: ScrapingProvider,
    mock_odds_func: MagicMock,
    race_code: str,
) -> None:
    """オッズ値が正しくマッピングされる."""
    from .conftest import create_scraping_odds

    mock_odds_func.return_value = create_scraping_odds()

    result = provider_full.get_win_show_odds(race_code)

    row = result.iloc[0]
    assert row["単勝オッズ"] == 3.5
    assert row["単勝人気"] == 1
    assert row["複勝人気"] == 1
    assert row["馬番"] == 1


def test_torikeshi_odds_nan(
    provider_full: ScrapingProvider,
    mock_odds_func: MagicMock,
    race_code: str,
) -> None:
    """出走取消馬のオッズがNaNになる."""
    from .conftest import create_scraping_odds

    odds = create_scraping_odds()
    odds.loc[1, "単勝オッズ"] = None
    odds.loc[1, "単勝人気"] = None
    odds.loc[1, "複勝最小オッズ"] = None
    odds.loc[1, "複勝最大オッズ"] = None
    odds.loc[1, "複勝人気"] = None
    mock_odds_func.return_value = odds

    result = provider_full.get_win_show_odds(race_code)

    row = result.iloc[1]
    assert pd.isna(row["単勝オッズ"])
    assert pd.isna(row["単勝人気"])
    assert pd.isna(row["複勝最低オッズ"])
    assert pd.isna(row["複勝最高オッズ"])
    assert pd.isna(row["複勝人気"])


def test_default_odds_source_is_jra() -> None:
    """取得元の既定は JRA."""
    assert ScrapingProvider().odds_source is OddsSource.JRA


def test_netkeiba_source_uses_netkeiba_only(
    mock_odds_func: MagicMock, mock_scraper_cls: MagicMock, race_code: str
) -> None:
    """取得元が netkeiba なら netkeiba だけを使い、JRA は呼ばない."""
    from .conftest import create_scraping_odds

    provider = ScrapingProvider(odds_source=OddsSource.NETKEIBA)
    with patch(_NETKEIBA_FUNC, return_value=create_scraping_odds()) as mock_netkeiba:
        result = provider.get_win_show_odds(race_code)

    mock_netkeiba.assert_called_once()
    mock_odds_func.assert_not_called()
    assert list(result.columns) == WIN_SHOW_ODDS_COLUMNS


# 準正常系
def test_jra_page_not_found_raises_without_fallback(
    provider_full: ScrapingProvider, mock_odds_func: MagicMock, race_code: str
) -> None:
    """JRA に該当開催が無ければ DataNotFoundError にし、netkeiba へは切り替えない."""
    mock_odds_func.side_effect = PageNotFoundError("not found")

    with (
        patch(_NETKEIBA_FUNC) as mock_netkeiba,
        pytest.raises(DataNotFoundError, match=race_code),
    ):
        provider_full.get_win_show_odds(race_code)

    mock_netkeiba.assert_not_called()


def test_invalid_odds_source_raises() -> None:
    """OddsSource 以外の取得元は ValueError."""
    with pytest.raises(ValueError, match="odds_source"):
        ScrapingProvider(odds_source="jra")  # type: ignore[arg-type]


def test_netkeiba_empty_raises(
    mock_odds_func: MagicMock, mock_scraper_cls: MagicMock, race_code: str
) -> None:
    """netkeibaのオッズが0行（発売前）ならDataNotFoundError."""
    provider = ScrapingProvider(odds_source=OddsSource.NETKEIBA)
    with (
        patch(_NETKEIBA_FUNC, return_value=pd.DataFrame(columns=["馬番", "単勝オッズ"])),
        pytest.raises(DataNotFoundError, match="発売前"),
    ):
        provider.get_win_show_odds(race_code)
