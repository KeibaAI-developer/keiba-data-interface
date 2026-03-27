"""MykeibaDBProvider.get_race_info関数のテスト."""

from unittest.mock import MagicMock

import pytest

from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.schema.columns import RACE_INFO_COLUMNS

from .conftest import create_race_shosai_df


# 正常系
def test_output_columns_match_schema(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """出力DataFrameのカラム構成がRACE_INFO_COLUMNSと一致する."""
    mock_race_getter.get_race_shosai.return_value = create_race_shosai_df()

    result = provider.get_race_info(race_code)

    assert list(result.columns) == RACE_INFO_COLUMNS


def test_output_is_single_row(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """出力DataFrameが1行である."""
    mock_race_getter.get_race_shosai.return_value = create_race_shosai_df()

    result = provider.get_race_info(race_code)

    assert len(result) == 1


def test_race_getter_called_with_correct_args(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """RaceGetter.get_race_shosai()が正しい引数で呼ばれる."""
    mock_race_getter.get_race_shosai.return_value = create_race_shosai_df()

    provider.get_race_info(race_code)

    mock_race_getter.get_race_shosai.assert_called_once_with(
        race_code=race_code, convert_codes=True
    )


def test_race_code_preserved(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """レースコードがそのまま格納される."""
    mock_race_getter.get_race_shosai.return_value = create_race_shosai_df()

    result = provider.get_race_info(race_code)

    assert result.iloc[0]["レースコード"] == race_code


def test_hasso_jikoku_converted(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """発走時刻が"HHMM"から"HH:MM"に変換される."""
    mock_race_getter.get_race_shosai.return_value = create_race_shosai_df(hasso_jikoku="1540")

    result = provider.get_race_info(race_code)

    assert result.iloc[0]["発走時刻"] == "15:40"


@pytest.mark.parametrize(
    "hasso_jikoku, expected",
    [
        ("0930", "09:30"),
        ("1200", "12:00"),
        ("1610", "16:10"),
    ],
)
def test_hasso_jikoku_various_times(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
    hasso_jikoku: str,
    expected: str,
) -> None:
    """さまざまな発走時刻が正しく変換される."""
    mock_race_getter.get_race_shosai.return_value = create_race_shosai_df(hasso_jikoku=hasso_jikoku)

    result = provider.get_race_info(race_code)

    assert result.iloc[0]["発走時刻"] == expected


def test_code_converted_columns_renamed(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """コード変換済みカラムが正しくリネームされる."""
    mock_race_getter.get_race_shosai.return_value = create_race_shosai_df()

    result = provider.get_race_info(race_code)

    row = result.iloc[0]
    assert row["競馬場"] == "中山"
    assert row["曜日"] == "日"
    assert row["グレード"] == "GI"
    assert row["競走種別"] == "サラ系３歳以上"
    assert row["競走記号"] == "(国際)(指定)"
    assert row["重量種別"] == "定量"
    assert row["トラック"] == "芝・右"
    assert row["天候"] == "晴"
    assert row["芝馬場状態"] == "良"


def test_direct_rename_columns(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """直接リネームされるカラムが正しく変換される."""
    mock_race_getter.get_race_shosai.return_value = create_race_shosai_df()

    result = provider.get_race_info(race_code)

    row = result.iloc[0]
    assert row["開催年"] == "2025"
    assert row["開催月日"] == "0502"
    assert row["開催回"] == 5
    assert row["開催日目"] == 8
    assert row["レース番号"] == 11
    assert row["競走名本題"] == "有馬記念"
    assert row["競走名カッコ内"] == "グランプリ"
    assert row["距離"] == 2500
    assert row["出走頭数"] == 16
    assert row["本賞金1着"] == 50000000


def test_prize_columns(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """賞金カラムがそのまま百円単位で格納される."""
    mock_race_getter.get_race_shosai.return_value = create_race_shosai_df()

    result = provider.get_race_info(race_code)

    row = result.iloc[0]
    assert row["本賞金1着"] == 50000000
    assert row["本賞金2着"] == 20000000
    assert row["本賞金3着"] == 12500000
    assert row["本賞金4着"] == 7500000
    assert row["本賞金5着"] == 5000000
