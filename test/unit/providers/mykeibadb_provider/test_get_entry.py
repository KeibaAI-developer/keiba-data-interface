"""MykeibaDBProvider.get_entry関数のテスト."""

from unittest.mock import MagicMock

import pandas as pd

from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.schema.columns import RACE_INFO_BY_HORSE_COLUMNS

from .conftest import create_umagoto_race_joho_df


# 正常系
def test_output_columns_match_schema(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """出力DataFrameのカラム構成がHORSE_RACE_INFO_COLUMNSと一致する."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    result = provider.get_entry(race_code)

    assert list(result.columns) == RACE_INFO_BY_HORSE_COLUMNS


def test_output_row_count(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """出力DataFrameの行数が入力と一致する."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    result = provider.get_entry(race_code)

    assert len(result) == 2


def test_race_getter_called_with_correct_args(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """RaceGetter.get_umagoto_race_joho()が正しい引数で呼ばれる."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    provider.get_entry(race_code)

    mock_race_getter.get_umagoto_race_joho.assert_called_once_with(
        race_code=race_code, convert_codes=False
    )


def test_futan_juryo_converted(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """負担重量が0.1kg単位からkg単位に変換される."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    result = provider.get_entry(race_code)

    assert result.iloc[0]["負担重量"] == 58.0
    assert result.iloc[1]["負担重量"] == 56.0


def test_tansho_odds_converted(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """単勝オッズが0.1倍単位から倍単位に変換される."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    result = provider.get_entry(race_code)

    assert result.iloc[0]["単勝オッズ"] == 3.8
    assert result.iloc[1]["単勝オッズ"] == 12.5


def test_kohan_3f_is_nan_in_entry(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """後3ハロンはget_entryでは取得できないためNaNになる."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    result = provider.get_entry(race_code)

    assert pd.isna(result.iloc[0]["後3ハロン"])
    assert pd.isna(result.iloc[1]["後3ハロン"])


def test_kohan_4f_is_nan_in_entry(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """後4ハロンはget_entryでは取得できないためNaNになる."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    result = provider.get_entry(race_code)

    assert pd.isna(result.iloc[0]["後4ハロン"])
    assert pd.isna(result.iloc[1]["後4ハロン"])


def test_code_converted_columns_renamed(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """コード変換済みカラムが正しくリネームされる."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    result = provider.get_entry(race_code)

    row = result.iloc[0]
    assert row["競馬場コード"] == "06"
    assert row["品種コード"] == "1"
    assert row["性別コード"] == "1"
    assert row["所属コード"] == "2"
    assert row["異常区分コード"] == "0"
    assert row["脚質判定コード"] == "4"


def test_direct_rename_columns(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """直接リネームされるカラムが正しく変換される."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    result = provider.get_entry(race_code)

    row = result.iloc[0]
    assert row["レースコード"] == "2025050206050811"
    assert row["開催年"] == "2025"
    assert row["開催月日"] == "0502"
    assert row["開催回"] == 5
    assert row["開催日目"] == 8
    assert row["レース番号"] == 11
    assert row["枠番"] == 1
    assert row["馬番"] == 1
    assert row["血統登録番号"] == "2021105001"
    assert row["馬名"] == "テスト馬1"
    assert row["馬齢"] == 4
    assert row["調教師コード"] == "01159"
    assert row["調教師名略称"] == "テスト調教師1"
    assert row["馬主コード"] == "226800"
    assert row["馬主名"] == "テスト馬主1"
    assert row["騎手コード"] == "05473"
    assert row["騎手名略称"] == "テスト騎手1"
    assert row["馬体重"] == 502
    assert row["増減符号"] == "+"
    assert row["増減差"] == 2


def test_second_horse_data(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """2頭目のデータが正しく変換される."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    result = provider.get_entry(race_code)

    row = result.iloc[1]
    assert row["枠番"] == 2
    assert row["馬番"] == 3
    assert row["血統登録番号"] == "2021105002"
    assert row["馬名"] == "テスト馬2"
    assert row["性別コード"] == "2"
    assert row["所属コード"] == "1"
    assert row["負担重量"] == 56.0


def test_kakutei_chakujun_zero_to_nan(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """確定着順て0のDB値（出走取消等）はNaNに変換される."""
    raw = create_umagoto_race_joho_df()
    raw.at[0, "kakutei_chakujun"] = 0
    mock_race_getter.get_umagoto_race_joho.return_value = raw

    result = provider.get_entry(race_code)

    assert pd.isna(result.iloc[0]["確定着順"])
