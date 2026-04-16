"""MykeibaDBProvider.get_win_show_odds関数のテスト."""

from unittest.mock import MagicMock

import pandas as pd

from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.schema.columns import ODDS_COLUMNS

from .conftest import create_odds1_fukusho_df, create_odds1_tansho_df


# 正常系
def test_output_columns_match_schema(
    provider: MykeibaDBProvider,
    mock_odds_getter: MagicMock,
    race_code: str,
) -> None:
    """出力DataFrameのカラム構成がODDS_COLUMNSと一致する."""
    mock_odds_getter.get_odds1_tansho.return_value = create_odds1_tansho_df()
    mock_odds_getter.get_odds1_fukusho.return_value = create_odds1_fukusho_df()

    result = provider.get_win_show_odds(race_code)

    assert list(result.columns) == ODDS_COLUMNS


def test_output_row_count(
    provider: MykeibaDBProvider,
    mock_odds_getter: MagicMock,
    race_code: str,
) -> None:
    """出力DataFrameの行数が馬番数と一致する."""
    mock_odds_getter.get_odds1_tansho.return_value = create_odds1_tansho_df()
    mock_odds_getter.get_odds1_fukusho.return_value = create_odds1_fukusho_df()

    result = provider.get_win_show_odds(race_code)

    assert len(result) == 2


def test_odds_getter_called_with_correct_args(
    provider: MykeibaDBProvider,
    mock_odds_getter: MagicMock,
    race_code: str,
) -> None:
    """OddsGetter.get_odds1_tansho/fukushoが正しい引数で呼ばれる."""
    mock_odds_getter.get_odds1_tansho.return_value = create_odds1_tansho_df()
    mock_odds_getter.get_odds1_fukusho.return_value = create_odds1_fukusho_df()

    provider.get_win_show_odds(race_code)

    mock_odds_getter.get_odds1_tansho.assert_called_once_with(
        race_code=race_code, convert_codes=True
    )
    mock_odds_getter.get_odds1_fukusho.assert_called_once_with(
        race_code=race_code, convert_codes=True
    )


def test_tansho_odds_converted(
    provider: MykeibaDBProvider,
    mock_odds_getter: MagicMock,
    race_code: str,
) -> None:
    """単勝オッズが0.1倍→倍に変換される."""
    mock_odds_getter.get_odds1_tansho.return_value = create_odds1_tansho_df()
    mock_odds_getter.get_odds1_fukusho.return_value = create_odds1_fukusho_df()

    result = provider.get_win_show_odds(race_code)

    assert result.iloc[0]["単勝オッズ"] == 3.8
    assert result.iloc[1]["単勝オッズ"] == 12.5


def test_fukusho_odds_converted(
    provider: MykeibaDBProvider,
    mock_odds_getter: MagicMock,
    race_code: str,
) -> None:
    """複勝オッズが0.1倍→倍に変換される."""
    mock_odds_getter.get_odds1_tansho.return_value = create_odds1_tansho_df()
    mock_odds_getter.get_odds1_fukusho.return_value = create_odds1_fukusho_df()

    result = provider.get_win_show_odds(race_code)

    assert result.iloc[0]["複勝最低オッズ"] == 1.5
    assert result.iloc[0]["複勝最高オッズ"] == 2.2
    assert result.iloc[1]["複勝最低オッズ"] == 4.5
    assert result.iloc[1]["複勝最高オッズ"] == 7.8


def test_ninki_columns(
    provider: MykeibaDBProvider,
    mock_odds_getter: MagicMock,
    race_code: str,
) -> None:
    """単勝人気・複勝人気が正しく格納される."""
    mock_odds_getter.get_odds1_tansho.return_value = create_odds1_tansho_df()
    mock_odds_getter.get_odds1_fukusho.return_value = create_odds1_fukusho_df()

    result = provider.get_win_show_odds(race_code)

    assert result.iloc[0]["単勝人気"] == 3
    assert result.iloc[0]["複勝人気"] == 2
    assert result.iloc[1]["単勝人気"] == 8
    assert result.iloc[1]["複勝人気"] == 7


def test_header_columns(
    provider: MykeibaDBProvider,
    mock_odds_getter: MagicMock,
    race_code: str,
) -> None:
    """ヘッダカラム（レースコード等）が正しく格納される."""
    mock_odds_getter.get_odds1_tansho.return_value = create_odds1_tansho_df()
    mock_odds_getter.get_odds1_fukusho.return_value = create_odds1_fukusho_df()

    result = provider.get_win_show_odds(race_code)

    row = result.iloc[0]
    assert row["レースコード"] == race_code
    assert row["開催年"] == "2025"
    assert row["開催月日"] == "0502"
    assert row["競馬場コード"] == "06"
    assert row["開催回"] == 5
    assert row["開催日目"] == 8
    assert row["レース番号"] == 11


def test_umaban_values(
    provider: MykeibaDBProvider,
    mock_odds_getter: MagicMock,
    race_code: str,
) -> None:
    """馬番が正しく格納される."""
    mock_odds_getter.get_odds1_tansho.return_value = create_odds1_tansho_df()
    mock_odds_getter.get_odds1_fukusho.return_value = create_odds1_fukusho_df()

    result = provider.get_win_show_odds(race_code)

    assert result.iloc[0]["馬番"] == 1
    assert result.iloc[1]["馬番"] == 3


def test_odds_zero_becomes_na(
    provider: MykeibaDBProvider,
    mock_odds_getter: MagicMock,
    race_code: str,
) -> None:
    """オッズが0の場合はNAになる（出走取消馬等）."""
    tansho = create_odds1_tansho_df()
    tansho.at[0, "odds"] = 0
    fukusho = create_odds1_fukusho_df()
    fukusho.at[0, "odds_saitei"] = 0
    fukusho.at[0, "odds_saikou"] = 0
    mock_odds_getter.get_odds1_tansho.return_value = tansho
    mock_odds_getter.get_odds1_fukusho.return_value = fukusho

    result = provider.get_win_show_odds(race_code)

    assert pd.isna(result.iloc[0]["単勝オッズ"])
    assert pd.isna(result.iloc[0]["複勝最低オッズ"])
    assert pd.isna(result.iloc[0]["複勝最高オッズ"])


def test_both_empty_returns_empty_schema(
    provider: MykeibaDBProvider,
    mock_odds_getter: MagicMock,
    race_code: str,
) -> None:
    """単勝・複勝両方空の場合スキーマカラム付き空DataFrameが返る."""
    mock_odds_getter.get_odds1_tansho.return_value = pd.DataFrame()
    mock_odds_getter.get_odds1_fukusho.return_value = pd.DataFrame()

    result = provider.get_win_show_odds(race_code)

    assert len(result) == 0
    assert list(result.columns) == ODDS_COLUMNS


def test_tansho_empty_returns_fukusho_only(
    provider: MykeibaDBProvider,
    mock_odds_getter: MagicMock,
    race_code: str,
) -> None:
    """単勝が空で複勝にデータがある場合、複勝のみから組み立てる."""
    mock_odds_getter.get_odds1_tansho.return_value = pd.DataFrame()
    mock_odds_getter.get_odds1_fukusho.return_value = create_odds1_fukusho_df()

    result = provider.get_win_show_odds(race_code)

    assert len(result) == 2
    assert list(result.columns) == ODDS_COLUMNS
    assert result.iloc[0]["馬番"] == 1
    assert result.iloc[0]["複勝最低オッズ"] == 1.5
    assert pd.isna(result.iloc[0]["単勝オッズ"])


def test_fukusho_empty_returns_tansho_only(
    provider: MykeibaDBProvider,
    mock_odds_getter: MagicMock,
    race_code: str,
) -> None:
    """複勝が空で単勝にデータがある場合、単勝のみから組み立てる."""
    mock_odds_getter.get_odds1_tansho.return_value = create_odds1_tansho_df()
    mock_odds_getter.get_odds1_fukusho.return_value = pd.DataFrame()

    result = provider.get_win_show_odds(race_code)

    assert len(result) == 2
    assert list(result.columns) == ODDS_COLUMNS
    assert result.iloc[0]["馬番"] == 1
    assert result.iloc[0]["単勝オッズ"] == 3.8
    assert pd.isna(result.iloc[0]["複勝最低オッズ"])
