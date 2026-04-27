"""MykeibaDBProvider.get_horse_info関数のテスト."""

from unittest.mock import MagicMock

import pandas as pd

from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.schema.columns import HORSE_INFO_COLUMNS

from .conftest import create_kyosoba_master2_df


# 正常系
def test_output_columns_match_schema(
    provider: MykeibaDBProvider,
    mock_master_getter: MagicMock,
) -> None:
    """出力DataFrameのカラム構成がHORSE_INFO_COLUMNSと一致する."""
    mock_master_getter.get_kyosoba_master2.return_value = create_kyosoba_master2_df()

    result = provider.get_horse_info("2022105081")

    assert list(result.columns) == HORSE_INFO_COLUMNS


def test_output_row_count(
    provider: MykeibaDBProvider,
    mock_master_getter: MagicMock,
) -> None:
    """出力DataFrameの行数が1行である."""
    mock_master_getter.get_kyosoba_master2.return_value = create_kyosoba_master2_df()

    result = provider.get_horse_info("2022105081")

    assert len(result) == 1


def test_master_getter_called_with_horse_id(
    provider: MykeibaDBProvider,
    mock_master_getter: MagicMock,
) -> None:
    """MasterGetter.get_kyosoba_master2()が馬IDで呼ばれる."""
    mock_master_getter.get_kyosoba_master2.return_value = create_kyosoba_master2_df()

    provider.get_horse_info("2022105081")

    mock_master_getter.get_kyosoba_master2.assert_called_once_with(
        ketto_toroku_bango="2022105081", convert_codes=False
    )


def test_column_mapping(
    provider: MykeibaDBProvider,
    mock_master_getter: MagicMock,
) -> None:
    """カラムマッピングが正しく適用される."""
    mock_master_getter.get_kyosoba_master2.return_value = create_kyosoba_master2_df()

    result = provider.get_horse_info("2022105081")

    row = result.iloc[0]
    assert row["血統登録番号"] == "2022105081"
    assert row["馬名"] == "ミュージアムマイル"
    assert row["馬名半角ｶﾅ"] == "ﾐｭｰｼﾞｱﾑﾏｲﾙ"
    assert row["性別コード"] == "1"
    assert row["生年月日"] == "20220110"
    assert row["東西所属コード"] == "2"
    assert row["調教師コード"] == "01159"


def test_ketto_columns_mapped(
    provider: MykeibaDBProvider,
    mock_master_getter: MagicMock,
) -> None:
    """血統情報カラムが正しくマッピングされる."""
    mock_master_getter.get_kyosoba_master2.return_value = create_kyosoba_master2_df()

    result = provider.get_horse_info("2022105081")

    row = result.iloc[0]
    assert row["父繁殖登録番号"] == "1120002395"
    assert row["父馬名"] == "リオンディーズ"
    assert row["母馬名"] == "サンタフェトレイル"


def test_chaku_columns_mapped(
    provider: MykeibaDBProvider,
    mock_master_getter: MagicMock,
) -> None:
    """着回数カラムが正しくマッピングされる."""
    mock_master_getter.get_kyosoba_master2.return_value = create_kyosoba_master2_df()

    result = provider.get_horse_info("2022105081")

    row = result.iloc[0]
    assert row["総合1着"] == 5
    assert row["総合2着"] == 2
    assert row["中央合計1着"] == 5
    assert row["芝右1着"] == 5


def test_empty_dataframe_returns_empty(
    provider: MykeibaDBProvider,
    mock_master_getter: MagicMock,
) -> None:
    """空データの場合は空DataFrameが返る."""
    mock_master_getter.get_kyosoba_master2.return_value = pd.DataFrame()

    result = provider.get_horse_info("9999999999")

    assert len(result) == 0
    assert list(result.columns) == HORSE_INFO_COLUMNS
