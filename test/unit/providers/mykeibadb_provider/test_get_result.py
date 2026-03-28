"""MykeibaDBProvider.get_result関数のテスト."""

from unittest.mock import MagicMock

import pandas as pd

from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.schema.columns import HORSE_RACE_INFO_COLUMNS

from .conftest import create_umagoto_race_joho_df


# 正常系
def test_output_columns_match_schema(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """出力DataFrameのカラム構成がHORSE_RACE_INFO_COLUMNSと一致する."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    result = provider.get_result(race_code)

    assert list(result.columns) == HORSE_RACE_INFO_COLUMNS


def test_output_row_count(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """出力DataFrameの行数が入力と一致する."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    result = provider.get_result(race_code)

    assert len(result) == 2


def test_race_getter_called_with_correct_args(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """RaceGetter.get_umagoto_race_joho()が正しい引数で呼ばれる."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    provider.get_result(race_code)

    mock_race_getter.get_umagoto_race_joho.assert_called_once_with(
        race_code=race_code, convert_codes=True
    )


def test_soha_time_converted(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """走破タイムが"MSSS"から"M:SS.S"に変換される."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    result = provider.get_result(race_code)

    assert result.iloc[0]["走破タイム"] == "2:31.5"
    assert result.iloc[1]["走破タイム"] == "2:31.6"


def test_soha_time_zero_not_converted(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """走破タイムが"0000"の場合は変換されない."""
    raw = create_umagoto_race_joho_df()
    raw.at[0, "soha_time"] = "0000"
    mock_race_getter.get_umagoto_race_joho.return_value = raw

    result = provider.get_result(race_code)

    # "0000"はintに変換すると0となり、変換条件(int > 0)を満たさないため変換されない
    assert result.iloc[0]["走破タイム"] == "0000"


def test_soha_time_nan_preserved(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """走破タイムがNaNの場合はそのまま保持される."""
    raw = create_umagoto_race_joho_df()
    raw.at[0, "soha_time"] = pd.NA
    mock_race_getter.get_umagoto_race_joho.return_value = raw

    result = provider.get_result(race_code)

    assert pd.isna(result.iloc[0]["走破タイム"])


def test_futan_juryo_converted(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """負担重量の変換がget_entryと同様に行われる."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    result = provider.get_result(race_code)

    assert result.iloc[0]["負担重量"] == 58.0
    assert result.iloc[1]["負担重量"] == 56.0


def test_tansho_odds_converted(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """単勝オッズの変換がget_entryと同様に行われる."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    result = provider.get_result(race_code)

    assert result.iloc[0]["単勝オッズ"] == 3.8
    assert result.iloc[1]["単勝オッズ"] == 12.5


def test_kohan_3f_converted(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """後3ハロンの変換がget_entryと同様に行われる."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    result = provider.get_result(race_code)

    assert result.iloc[0]["後3ハロン"] == 34.6
    assert result.iloc[1]["後3ハロン"] == 34.8


def test_result_specific_columns(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """結果固有のカラム（着順・コーナー順位等）が正しく変換される."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    result = provider.get_result(race_code)

    row = result.iloc[0]
    assert row["確定着順"] == 1
    assert row["1コーナー順位"] == 11
    assert row["4コーナー順位"] == 3
    assert row["単勝人気順"] == 3
    assert row["獲得本賞金"] == 50000000
