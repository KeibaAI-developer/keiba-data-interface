"""ScrapingProvider.get_win_show_odds関数のテスト."""

from unittest.mock import MagicMock

import pandas as pd

from keiba_data_interface.providers.scraping_provider import ScrapingProvider
from keiba_data_interface.schema.columns import ODDS_COLUMNS


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

    assert list(result.columns) == ODDS_COLUMNS


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
