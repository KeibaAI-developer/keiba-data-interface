"""MykeibaDBProvider.get_payoff関数のテスト."""

from unittest.mock import MagicMock

import pandas as pd
import pytest

from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.schema.columns import PAYOFF_COLUMNS

from .conftest import create_haraimodoshi_df


# 正常系
def test_output_columns_match_schema(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """出力DataFrameのカラム構成がPAYOFF_COLUMNSと一致する."""
    mock_race_getter.get_haraimodoshi.return_value = create_haraimodoshi_df()

    result = provider.get_payoff(race_code)

    assert list(result.columns) == PAYOFF_COLUMNS


def test_output_is_single_row(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """出力DataFrameが1行である."""
    mock_race_getter.get_haraimodoshi.return_value = create_haraimodoshi_df()

    result = provider.get_payoff(race_code)

    assert len(result) == 1


def test_race_getter_called_with_correct_args(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """RaceGetter.get_haraimodoshi()が正しい引数で呼ばれる."""
    mock_race_getter.get_haraimodoshi.return_value = create_haraimodoshi_df()

    provider.get_payoff(race_code)

    mock_race_getter.get_haraimodoshi.assert_called_once_with(
        race_code=race_code, convert_codes=False
    )


def test_header_columns_renamed(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """ヘッダカラムが日本語にリネームされる."""
    mock_race_getter.get_haraimodoshi.return_value = create_haraimodoshi_df()

    result = provider.get_payoff(race_code)

    row = result.iloc[0]
    assert row["レースコード"] == race_code
    assert row["開催年"] == "2025"
    assert row["開催月日"] == "0502"
    assert row["競馬場コード"] == "06"
    assert row["開催回"] == 5
    assert row["開催日目"] == 8
    assert row["レース番号"] == 11


def test_tansho_payoff_renamed(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """単勝払戻カラムがリネームされる."""
    mock_race_getter.get_haraimodoshi.return_value = create_haraimodoshi_df()

    result = provider.get_payoff(race_code)

    row = result.iloc[0]
    assert row["単勝1馬番"] == 5
    assert row["単勝1払戻金"] == 380
    assert row["単勝1人気順"] == 1


def test_fukusho_payoff_renamed(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """複勝払戻カラムがリネームされる."""
    mock_race_getter.get_haraimodoshi.return_value = create_haraimodoshi_df()

    result = provider.get_payoff(race_code)

    row = result.iloc[0]
    assert row["複勝1馬番"] == 5
    assert row["複勝1払戻金"] == 150
    assert row["複勝2馬番"] == 3
    assert row["複勝2払戻金"] == 450
    assert row["複勝3馬番"] == 8
    assert row["複勝3払戻金"] == 210


def test_umaren_payoff_renamed(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """馬連払戻カラムがリネームされる."""
    mock_race_getter.get_haraimodoshi.return_value = create_haraimodoshi_df()

    result = provider.get_payoff(race_code)

    row = result.iloc[0]
    assert row["馬連1組番1"] == 3
    assert row["馬連1組番2"] == 5
    assert row["馬連1払戻金"] == 2530
    assert row["馬連1人気順"] == 7


def test_sanrentan_payoff_renamed(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """3連単払戻カラムがリネームされる."""
    mock_race_getter.get_haraimodoshi.return_value = create_haraimodoshi_df()

    result = provider.get_payoff(race_code)

    row = result.iloc[0]
    assert row["3連単1組番1"] == 5
    assert row["3連単1組番2"] == 3
    assert row["3連単1組番3"] == 8
    assert row["3連単1払戻金"] == 45680
    assert row["3連単1人気順"] == 42


def test_flags_renamed(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """フラグカラムがリネームされる."""
    mock_race_getter.get_haraimodoshi.return_value = create_haraimodoshi_df()

    result = provider.get_payoff(race_code)

    row = result.iloc[0]
    assert row["不成立フラグ単勝"] == "0"
    assert row["特払フラグ馬単"] == "0"
    assert row["返還フラグ3連単"] == "0"


def test_missing_payoff_columns_nan(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """データがない組のカラムはNaNである."""
    mock_race_getter.get_haraimodoshi.return_value = create_haraimodoshi_df()

    result = provider.get_payoff(race_code)

    row = result.iloc[0]
    # 単勝2は同着なしでNaN
    assert pd.isna(row["単勝2馬番"])
    assert pd.isna(row["単勝2払戻金"])


# 準正常系
def test_empty_dataframe_raises_error(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """空のDataFrameでValueErrorが発生する."""
    mock_race_getter.get_haraimodoshi.return_value = pd.DataFrame()

    with pytest.raises(ValueError):
        provider.get_payoff(race_code)


def test_multiple_rows_raises_error(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """複数行のDataFrameでValueErrorが発生する."""
    raw = create_haraimodoshi_df()
    multi_row = pd.concat([raw, raw], ignore_index=True)
    mock_race_getter.get_haraimodoshi.return_value = multi_row

    with pytest.raises(ValueError):
        provider.get_payoff(race_code)
