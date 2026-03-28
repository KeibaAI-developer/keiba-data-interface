"""MykeibaDBProvider.get_race_result_info関数のテスト."""

from unittest.mock import MagicMock

import pandas as pd
import pytest

from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.schema.columns import RACE_RESULT_INFO_COLUMNS

from .conftest import create_race_shosai_with_result_info_df


# 正常系
def test_output_columns_match_schema(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """出力DataFrameのカラム構成がRACE_RESULT_INFO_COLUMNSと一致する."""
    mock_race_getter.get_race_shosai.return_value = create_race_shosai_with_result_info_df()

    result = provider.get_race_result_info(race_code)

    assert list(result.columns) == RACE_RESULT_INFO_COLUMNS


def test_output_is_single_row(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """出力DataFrameが1行である."""
    mock_race_getter.get_race_shosai.return_value = create_race_shosai_with_result_info_df()

    result = provider.get_race_result_info(race_code)

    assert len(result) == 1


def test_race_getter_called_with_correct_args(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """RaceGetter.get_race_shosai()が正しい引数で呼ばれる."""
    mock_race_getter.get_race_shosai.return_value = create_race_shosai_with_result_info_df()

    provider.get_race_result_info(race_code)

    mock_race_getter.get_race_shosai.assert_called_once_with(
        race_code=race_code, convert_codes=True
    )


def test_race_code_preserved(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """レースコードがそのまま格納される."""
    mock_race_getter.get_race_shosai.return_value = create_race_shosai_with_result_info_df()

    result = provider.get_race_result_info(race_code)

    assert result.iloc[0]["レースコード"] == race_code


def test_lap_times_converted_2000m(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """2000mレースのラップタイムが偶数200mカラムに正しく配置される."""
    mock_race_getter.get_race_shosai.return_value = create_race_shosai_with_result_info_df(
        kyori=2000
    )

    result = provider.get_race_result_info(race_code)

    row = result.iloc[0]
    # LAP_TIME1=129 → ラップ200m = 12.9
    assert row["ラップ200m"] == 12.9
    # LAP_TIME2=118 → ラップ400m = 11.8
    assert row["ラップ400m"] == 11.8
    # LAP_TIME10=116 → ラップ2000m = 11.6
    assert row["ラップ2000m"] == 11.6


def test_lap_times_odd_columns_nan_2000m(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """2000mレースの奇数カラム（100m, 300m, ...）がNaNである."""
    mock_race_getter.get_race_shosai.return_value = create_race_shosai_with_result_info_df(
        kyori=2000
    )

    result = provider.get_race_result_info(race_code)

    row = result.iloc[0]
    assert pd.isna(row["ラップ100m"])
    assert pd.isna(row["ラップ300m"])
    assert pd.isna(row["ラップ500m"])
    assert pd.isna(row["ラップ1900m"])


def test_lap_times_beyond_distance_nan(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """レース距離を超えるラップカラムがNaNである."""
    mock_race_getter.get_race_shosai.return_value = create_race_shosai_with_result_info_df(
        kyori=2000
    )

    result = provider.get_race_result_info(race_code)

    row = result.iloc[0]
    assert pd.isna(row["ラップ2100m"])
    assert pd.isna(row["ラップ2200m"])
    assert pd.isna(row["ラップ5000m"])


def test_lap_times_converted_2500m(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """2500mレースのラップタイムが正しく展開される（先頭100m + 200m刻み）."""
    mock_race_getter.get_race_shosai.return_value = create_race_shosai_with_result_info_df(
        kyori=2500
    )

    result = provider.get_race_result_info(race_code)

    row = result.iloc[0]
    # LAP_TIME1=73 → ラップ100m = 7.3（先頭100m区間）
    assert row["ラップ100m"] == 7.3
    # LAP_TIME2=118 → ラップ300m = 11.8
    assert row["ラップ300m"] == 11.8
    # LAP_TIME13=121 → ラップ2500m = 12.1
    assert row["ラップ2500m"] == 12.1
    # 偶数カラム（200m, 400m, ...）はNaN
    assert pd.isna(row["ラップ200m"])
    assert pd.isna(row["ラップ400m"])


def test_harlon_times_converted(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """ハロンタイムが0.1秒から秒に変換される."""
    mock_race_getter.get_race_shosai.return_value = create_race_shosai_with_result_info_df()

    result = provider.get_race_result_info(race_code)

    row = result.iloc[0]
    assert row["前3ハロン"] == 36.6
    assert row["前4ハロン"] == 48.7
    assert row["後3ハロン"] == 35.3
    assert row["後4ハロン"] == 47.4


def test_corner_info_copied(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """コーナー情報が正しくコピーされる."""
    mock_race_getter.get_race_shosai.return_value = create_race_shosai_with_result_info_df()

    result = provider.get_race_result_info(race_code)

    row = result.iloc[0]
    assert row["1コーナー"] == "3コーナー奥"
    assert row["1コーナー周回数"] == 1
    assert row["1コーナー通過順"] == "5-3(1,8)-2-4-6"
    assert row["4コーナー"] == "4コーナー"
    assert row["4コーナー通過順"] == "1-3-5-8-2-4-6"


def test_record_koshin_kubun_copied(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """レコード更新区分が正しくコピーされる."""
    mock_race_getter.get_race_shosai.return_value = create_race_shosai_with_result_info_df()

    result = provider.get_race_result_info(race_code)

    assert result.iloc[0]["レコード更新区分"] == "1"


# 準正常系
def test_empty_dataframe_raises_error(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """空のDataFrameでValueErrorが発生する."""
    mock_race_getter.get_race_shosai.return_value = pd.DataFrame()

    with pytest.raises(ValueError):
        provider.get_race_result_info(race_code)


def test_multiple_rows_raises_error(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """複数行のDataFrameでValueErrorが発生する."""
    raw = create_race_shosai_with_result_info_df()
    multi_row = pd.concat([raw, raw], ignore_index=True)
    mock_race_getter.get_race_shosai.return_value = multi_row

    with pytest.raises(ValueError):
        provider.get_race_result_info(race_code)
