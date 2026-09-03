"""ScrapingProvider.get_expected_win_show_odds関数のテスト."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from keiba_data_interface.exceptions import DataNotFoundError
from keiba_data_interface.providers.scraping_provider import ScrapingProvider
from keiba_data_interface.schema.columns import WIN_SHOW_ODDS_COLUMNS


def _yoso_df(uma_bans: list[float] | None = None, odds: list[float] | None = None) -> pd.DataFrame:
    """予想オッズの典型データ."""
    return pd.DataFrame(
        {
            "馬番": uma_bans if uma_bans is not None else [3, 1, 2],
            "馬名": ["馬3", "馬1", "馬2"],
            "予想単勝オッズ": odds if odds is not None else [12.5, 2.5, np.nan],
        }
    )


@pytest.fixture()
def mock_yoso_func() -> Generator[MagicMock, None, None]:
    """scrape_yoso_odds_from_netkeibaをパッチしたモック関数を返すfixture.

    Yields:
        MagicMock: scrape_yoso_odds_from_netkeibaのパッチモック。
    """
    with patch(
        "keiba_data_interface.providers.scraping_provider.scrape_yoso_odds_from_netkeiba"
    ) as mock_func:
        yield mock_func


# 正常系
def test_output_matches_schema_sorted_by_uma_ban(mock_yoso_func: MagicMock, race_code: str) -> None:
    """単複オッズのスキーマで馬番順に返す."""
    mock_yoso_func.return_value = _yoso_df()

    result = ScrapingProvider().get_expected_win_show_odds(race_code)

    assert list(result.columns) == WIN_SHOW_ODDS_COLUMNS
    assert list(result["馬番"]) == [1, 2, 3]
    assert result["レースコード"].iloc[0] == race_code


def test_win_odds_and_ninki_from_expected_odds(mock_yoso_func: MagicMock, race_code: str) -> None:
    """予想単勝オッズを単勝オッズにし、単勝人気はその昇順の順位。取消（NaN）はNaN."""
    mock_yoso_func.return_value = _yoso_df()

    result = ScrapingProvider().get_expected_win_show_odds(race_code).set_index("馬番")

    assert result.loc[1, "単勝オッズ"] == 2.5
    assert result.loc[3, "単勝オッズ"] == 12.5
    assert result.loc[1, "単勝人気"] == 1
    assert result.loc[3, "単勝人気"] == 2
    assert pd.isna(result.loc[2, "単勝オッズ"])
    assert pd.isna(result.loc[2, "単勝人気"])


def test_show_columns_are_nan(mock_yoso_func: MagicMock, race_code: str) -> None:
    """複勝のカラムは予想オッズに無いためNaN."""
    mock_yoso_func.return_value = _yoso_df()

    result = ScrapingProvider().get_expected_win_show_odds(race_code)

    assert result[["複勝最低オッズ", "複勝最高オッズ", "複勝人気"]].isna().all().all()


def test_passes_race_id(mock_yoso_func: MagicMock, race_code: str) -> None:
    """12桁レースIDでスクレイパーを呼ぶ."""
    mock_yoso_func.return_value = _yoso_df()

    ScrapingProvider().get_expected_win_show_odds(race_code)

    assert mock_yoso_func.call_args.args[0] == race_code[:4] + race_code[8:]


# 準正常系
def test_empty_raises(mock_yoso_func: MagicMock, race_code: str) -> None:
    """予想オッズが0行ならDataNotFoundError."""
    mock_yoso_func.return_value = _yoso_df().iloc[0:0]

    with pytest.raises(DataNotFoundError, match=race_code):
        ScrapingProvider().get_expected_win_show_odds(race_code)


def test_missing_uma_ban_raises(mock_yoso_func: MagicMock, race_code: str) -> None:
    """枠順確定前（馬番がNaN）ならDataNotFoundError."""
    mock_yoso_func.return_value = _yoso_df(uma_bans=[np.nan, np.nan, np.nan])

    with pytest.raises(DataNotFoundError, match="枠順確定前"):
        ScrapingProvider().get_expected_win_show_odds(race_code)


def test_all_odds_missing_raises(mock_yoso_func: MagicMock, race_code: str) -> None:
    """出馬表の行はあるが予想オッズが全馬空ならDataNotFoundError."""
    mock_yoso_func.return_value = _yoso_df(odds=[np.nan, np.nan, np.nan])

    with pytest.raises(DataNotFoundError, match="予想オッズがありません"):
        ScrapingProvider().get_expected_win_show_odds(race_code)
