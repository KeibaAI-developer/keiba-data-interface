"""MykeibaDBProvider.get_chakudosu関数のテスト."""

from unittest.mock import MagicMock

import pandas as pd

from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.schema.columns import CHAKUDOSU_COLUMNS

from .conftest import (
    RACE_CODE,
    create_shussobetsu_baba_df,
    create_shussobetsu_keibajo_df,
    create_shussobetsu_kyori_df,
)


def _setup_mock(mock_shussobetsu_getter: MagicMock) -> None:
    """ShussobetsuGetterモックに3テーブルの典型データを設定する."""
    mock_shussobetsu_getter.get_shussobetsu_keibajo.return_value = (
        create_shussobetsu_keibajo_df()
    )
    mock_shussobetsu_getter.get_shussobetsu_kyori.return_value = create_shussobetsu_kyori_df()
    mock_shussobetsu_getter.get_shussobetsu_baba.return_value = create_shussobetsu_baba_df()


# 正常系
def test_output_columns_match_schema(
    provider: MykeibaDBProvider,
    mock_shussobetsu_getter: MagicMock,
    race_code: str,
) -> None:
    """出力DataFrameのカラム構成がCHAKUDOSU_COLUMNSと一致する."""
    _setup_mock(mock_shussobetsu_getter)

    result = provider.get_chakudosu(race_code)

    assert list(result.columns) == CHAKUDOSU_COLUMNS


def test_output_row_count(
    provider: MykeibaDBProvider,
    mock_shussobetsu_getter: MagicMock,
    race_code: str,
) -> None:
    """出力DataFrameの行数が出走頭数分である."""
    _setup_mock(mock_shussobetsu_getter)

    result = provider.get_chakudosu(race_code)

    assert len(result) == 2


def test_sorted_by_ketto_toroku_bango(
    provider: MykeibaDBProvider,
    mock_shussobetsu_getter: MagicMock,
    race_code: str,
) -> None:
    """出力DataFrameが血統登録番号昇順である."""
    _setup_mock(mock_shussobetsu_getter)

    result = provider.get_chakudosu(race_code)

    assert list(result["血統登録番号"]) == ["2021105001", "2021105002"]


def test_getter_called_with_race_code(
    provider: MykeibaDBProvider,
    mock_shussobetsu_getter: MagicMock,
    race_code: str,
) -> None:
    """ShussobetsuGetterの3メソッドがレースコードで呼ばれる."""
    _setup_mock(mock_shussobetsu_getter)

    provider.get_chakudosu(race_code)

    mock_shussobetsu_getter.get_shussobetsu_keibajo.assert_called_once_with(
        race_code=race_code, convert_codes=False
    )
    mock_shussobetsu_getter.get_shussobetsu_kyori.assert_called_once_with(
        race_code=race_code, convert_codes=False
    )
    mock_shussobetsu_getter.get_shussobetsu_baba.assert_called_once_with(
        race_code=race_code, convert_codes=False
    )


def test_key_columns_mapped(
    provider: MykeibaDBProvider,
    mock_shussobetsu_getter: MagicMock,
    race_code: str,
) -> None:
    """キーカラムが正しくマッピングされる."""
    _setup_mock(mock_shussobetsu_getter)

    result = provider.get_chakudosu(race_code)

    row = result.iloc[0]
    assert row["レースコード"] == RACE_CODE
    assert row["血統登録番号"] == "2021105001"
    assert row["馬名"] == "テスト馬1"


def test_keibajo_columns_mapped(
    provider: MykeibaDBProvider,
    mock_shussobetsu_getter: MagicMock,
    race_code: str,
) -> None:
    """競馬場別着回数カラムが正しくマッピングされる."""
    _setup_mock(mock_shussobetsu_getter)

    result = provider.get_chakudosu(race_code)

    row1 = result.iloc[0]
    assert row1["中山芝1着"] == 2
    assert row1["中山芝4着"] == 1
    assert row1["東京芝2着"] == 1
    assert row1["東京芝着外"] == 1
    assert row1["札幌芝1着"] == 0
    row2 = result.iloc[1]
    assert row2["京都ダ1着"] == 1
    assert row2["京都ダ3着"] == 2


def test_kyori_columns_mapped(
    provider: MykeibaDBProvider,
    mock_shussobetsu_getter: MagicMock,
    race_code: str,
) -> None:
    """距離別着回数カラムが正しくマッピングされる."""
    _setup_mock(mock_shussobetsu_getter)

    result = provider.get_chakudosu(race_code)

    row1 = result.iloc[0]
    assert row1["芝1801-20001着"] == 2
    assert row1["芝2201-24002着"] == 1
    row2 = result.iloc[1]
    assert row2["ダ1601-18001着"] == 1
    assert row2["ダ1801-20003着"] == 2


def test_baba_columns_mapped(
    provider: MykeibaDBProvider,
    mock_shussobetsu_getter: MagicMock,
    race_code: str,
) -> None:
    """馬場別・馬場状態別着回数カラムが正しくマッピングされる."""
    _setup_mock(mock_shussobetsu_getter)

    result = provider.get_chakudosu(race_code)

    row1 = result.iloc[0]
    assert row1["芝右1着"] == 2
    assert row1["芝左2着"] == 1
    assert row1["芝良1着"] == 2
    assert row1["芝稍4着"] == 1
    row2 = result.iloc[1]
    assert row2["ダ右1着"] == 1
    assert row2["ダ良1着"] == 1
    assert row2["ダ良3着"] == 2


def test_missing_horse_in_one_table_kept_with_nan(
    provider: MykeibaDBProvider,
    mock_shussobetsu_getter: MagicMock,
    race_code: str,
) -> None:
    """一部のテーブルにのみ存在する馬も行として保持され欠損カラムはNaNになる."""
    keibajo_df = create_shussobetsu_keibajo_df()
    kyori_df = create_shussobetsu_kyori_df().iloc[[0]]
    baba_df = create_shussobetsu_baba_df()
    mock_shussobetsu_getter.get_shussobetsu_keibajo.return_value = keibajo_df
    mock_shussobetsu_getter.get_shussobetsu_kyori.return_value = kyori_df
    mock_shussobetsu_getter.get_shussobetsu_baba.return_value = baba_df

    result = provider.get_chakudosu(race_code)

    assert len(result) == 2
    row2 = result[result["血統登録番号"] == "2021105002"].iloc[0]
    assert pd.isna(row2["ダ1601-18001着"])
    assert row2["京都ダ1着"] == 1


# 準正常系
def test_empty_dataframe_returns_empty(
    provider: MykeibaDBProvider,
    mock_shussobetsu_getter: MagicMock,
    race_code: str,
) -> None:
    """空データの場合は空DataFrameが返る."""
    mock_shussobetsu_getter.get_shussobetsu_keibajo.return_value = pd.DataFrame()
    mock_shussobetsu_getter.get_shussobetsu_kyori.return_value = pd.DataFrame()
    mock_shussobetsu_getter.get_shussobetsu_baba.return_value = pd.DataFrame()

    result = provider.get_chakudosu(race_code)

    assert len(result) == 0
    assert list(result.columns) == CHAKUDOSU_COLUMNS
