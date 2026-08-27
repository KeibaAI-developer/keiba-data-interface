"""MykeibaDBProvider.get_win_show_votes関数のテスト."""

from unittest.mock import MagicMock

import pandas as pd
import pytest

from keiba_data_interface.exceptions import DataNotFoundError
from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.schema.columns import WIN_SHOW_VOTES_COLUMNS

from .conftest import create_hyosu1_fukusho_df, create_hyosu1_tansho_df, create_odds1_df


def _set_returns(mock_hyosu_getter: MagicMock, mock_odds_getter: MagicMock) -> None:
    """典型データを各Getterのモックに設定する."""
    mock_hyosu_getter.get_hyosu1_tansho.return_value = create_hyosu1_tansho_df()
    mock_hyosu_getter.get_hyosu1_fukusho.return_value = create_hyosu1_fukusho_df()
    mock_odds_getter.get_odds1.return_value = create_odds1_df()


# 正常系
def test_output_columns_match_schema(
    provider: MykeibaDBProvider,
    mock_hyosu_getter: MagicMock,
    mock_odds_getter: MagicMock,
    race_code: str,
) -> None:
    """出力DataFrameのカラム構成がWIN_SHOW_VOTES_COLUMNSと一致し、馬番順で頭数分の行が返る."""
    _set_returns(mock_hyosu_getter, mock_odds_getter)

    result = provider.get_win_show_votes(race_code)

    assert list(result.columns) == WIN_SHOW_VOTES_COLUMNS
    assert result["馬番"].tolist() == [1, 3]


def test_getters_called_with_correct_args(
    provider: MykeibaDBProvider,
    mock_hyosu_getter: MagicMock,
    mock_odds_getter: MagicMock,
    race_code: str,
) -> None:
    """HyosuGetter / OddsGetterがレースコード指定・コード変換なしで呼ばれる."""
    _set_returns(mock_hyosu_getter, mock_odds_getter)

    provider.get_win_show_votes(race_code)

    mock_hyosu_getter.get_hyosu1_tansho.assert_called_once_with(
        race_code=race_code, convert_codes=False
    )
    mock_hyosu_getter.get_hyosu1_fukusho.assert_called_once_with(
        race_code=race_code, convert_codes=False
    )
    mock_odds_getter.get_odds1.assert_called_once_with(race_code=race_code, convert_codes=False)


def test_values_converted(
    provider: MykeibaDBProvider,
    mock_hyosu_getter: MagicMock,
    mock_odds_getter: MagicMock,
    race_code: str,
) -> None:
    """票数・人気・合計・データ区分・ヘッダが変換される（票数は百円単位のまま）."""
    _set_returns(mock_hyosu_getter, mock_odds_getter)

    result = provider.get_win_show_votes(race_code)

    row = result.iloc[0]
    assert row["レースコード"] == race_code
    assert row["開催年"] == "2025"
    assert row["開催回"] == 5
    assert row["レース番号"] == 11
    assert row["単勝票数"] == 1523983
    assert row["単勝票数人気"] == 2
    assert row["複勝票数"] == 856120
    assert row["複勝票数人気"] == 3
    assert row["単勝票数合計"] == 65620306
    assert row["複勝票数合計"] == 31752716
    assert row["データ区分"] == "5"
    assert result.iloc[1]["単勝票数"] == 75472


# 準正常系
def test_missing_votes_raises(
    provider: MykeibaDBProvider,
    mock_hyosu_getter: MagicMock,
    mock_odds_getter: MagicMock,
    race_code: str,
) -> None:
    """票数テーブルが空の場合DataNotFoundErrorになる（推定値で埋めない）."""
    _set_returns(mock_hyosu_getter, mock_odds_getter)
    mock_hyosu_getter.get_hyosu1_fukusho.return_value = pd.DataFrame()

    with pytest.raises(DataNotFoundError, match="票数が存在しません"):
        provider.get_win_show_votes(race_code)


def test_missing_totals_raises(
    provider: MykeibaDBProvider,
    mock_hyosu_getter: MagicMock,
    mock_odds_getter: MagicMock,
    race_code: str,
) -> None:
    """票数合計（ODDS1）が無い場合DataNotFoundErrorになる."""
    _set_returns(mock_hyosu_getter, mock_odds_getter)
    mock_odds_getter.get_odds1.return_value = pd.DataFrame()

    with pytest.raises(DataNotFoundError, match="票数が存在しません"):
        provider.get_win_show_votes(race_code)


def test_only_unregistered_rows_raises(
    provider: MykeibaDBProvider,
    mock_hyosu_getter: MagicMock,
    mock_odds_getter: MagicMock,
    race_code: str,
) -> None:
    """未登録行（票数がスペース）しか無い場合、空のDataFrameを返さずDataNotFoundErrorになる."""
    _set_returns(mock_hyosu_getter, mock_odds_getter)
    tansho = create_hyosu1_tansho_df()
    tansho["hyosu"] = "           "
    fukusho = create_hyosu1_fukusho_df()
    fukusho["hyosu"] = "           "
    mock_hyosu_getter.get_hyosu1_tansho.return_value = tansho
    mock_hyosu_getter.get_hyosu1_fukusho.return_value = fukusho

    with pytest.raises(DataNotFoundError, match="登録済みの票数が存在しません"):
        provider.get_win_show_votes(race_code)


def test_multiple_totals_rows_raises(
    provider: MykeibaDBProvider,
    mock_hyosu_getter: MagicMock,
    mock_odds_getter: MagicMock,
    race_code: str,
) -> None:
    """票数合計（ODDS1）が複数行の場合DataNotFoundErrorになる（ValueErrorを漏らさない）."""
    _set_returns(mock_hyosu_getter, mock_odds_getter)
    mock_odds_getter.get_odds1.return_value = pd.concat(
        [create_odds1_df(), create_odds1_df()], ignore_index=True
    )

    with pytest.raises(DataNotFoundError, match="1行"):
        provider.get_win_show_votes(race_code)
