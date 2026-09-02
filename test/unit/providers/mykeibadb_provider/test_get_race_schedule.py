"""MykeibaDBProvider.get_race_schedule関数のテスト."""

from datetime import date
from unittest.mock import MagicMock

import pandas as pd

from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.schema.columns import RACE_SCHEDULE_COLUMNS


def create_race_shosai_schedule_df() -> pd.DataFrame:
    """mykeibadb RACE_SHOSAI出力の時刻表向けデータを生成する.

    東京2レース（うち1レースは中止）と中山1レースを、レースコード順と異なる並びで返す。
    """
    return pd.DataFrame(
        [
            {
                "data_kubun": "2",
                "race_code": "2025050206050801",
                "keibajo_code": "06",
                "race_bango": 1,
                "hasso_jikoku": "1000",
                "kyosomei_hondai": "3歳未勝利",
            },
            {
                "data_kubun": "2",
                "race_code": "2025050205050802",
                "keibajo_code": "05",
                "race_bango": 2,
                "hasso_jikoku": "1035",
                "kyosomei_hondai": "3歳新馬",
            },
            {
                "data_kubun": "9",
                "race_code": "2025050205050803",
                "keibajo_code": "05",
                "race_bango": 3,
                "hasso_jikoku": "1105",
                "kyosomei_hondai": "4歳以上1勝クラス",
            },
            {
                "data_kubun": "2",
                "race_code": "2025050205050801",
                "keibajo_code": "05",
                "race_bango": 1,
                "hasso_jikoku": "",
                "kyosomei_hondai": "3歳未勝利",
            },
        ]
    )


# 正常系
def test_output_columns_match_schema(
    provider: MykeibaDBProvider, mock_race_getter: MagicMock
) -> None:
    """出力DataFrameのカラム構成がRACE_SCHEDULE_COLUMNSと一致する."""
    mock_race_getter.get_race_shosai.return_value = create_race_shosai_schedule_df()

    result = provider.get_race_schedule("20250502")

    assert list(result.columns) == RACE_SCHEDULE_COLUMNS


def test_race_getter_called_with_target_date(
    provider: MykeibaDBProvider, mock_race_getter: MagicMock
) -> None:
    """RaceGetter.get_race_shosai()が対象日を開始日・終了日にして呼ばれる."""
    mock_race_getter.get_race_shosai.return_value = create_race_shosai_schedule_df()

    provider.get_race_schedule("20250502")

    mock_race_getter.get_race_shosai.assert_called_once_with(
        start_date=date(2025, 5, 2), end_date=date(2025, 5, 2), convert_codes=False
    )


def test_cancelled_race_excluded(provider: MykeibaDBProvider, mock_race_getter: MagicMock) -> None:
    """データ区分が9（レース中止）のレースは含まれない."""
    mock_race_getter.get_race_shosai.return_value = create_race_shosai_schedule_df()

    result = provider.get_race_schedule("20250502")

    assert "2025050205050803" not in result["レースコード"].tolist()
    assert len(result) == 3


def test_sorted_by_race_code(provider: MykeibaDBProvider, mock_race_getter: MagicMock) -> None:
    """レースコード昇順に並ぶ."""
    mock_race_getter.get_race_shosai.return_value = create_race_shosai_schedule_df()

    result = provider.get_race_schedule("20250502")

    assert result["レースコード"].tolist() == [
        "2025050205050801",
        "2025050205050802",
        "2025050206050801",
    ]


def test_values_converted(provider: MykeibaDBProvider, mock_race_getter: MagicMock) -> None:
    """競馬場コード・レース番号・発走時刻・競走名が統一スキーマの値になる."""
    mock_race_getter.get_race_shosai.return_value = create_race_shosai_schedule_df()

    result = provider.get_race_schedule("20250502")

    row = result.iloc[1]
    assert row["競馬場コード"] == "05"
    assert row["レース番号"] == 2
    assert row["発走時刻"] == "10:35"
    assert row["競走名"] == "3歳新馬"


def test_missing_start_time_is_na(provider: MykeibaDBProvider, mock_race_getter: MagicMock) -> None:
    """発走時刻が未設定（空文字）のレースは欠損になる."""
    mock_race_getter.get_race_shosai.return_value = create_race_shosai_schedule_df()

    result = provider.get_race_schedule("20250502")

    assert pd.isna(result.iloc[0]["発走時刻"])


def test_empty_schedule(provider: MykeibaDBProvider, mock_race_getter: MagicMock) -> None:
    """開催が無い日は0行のDataFrameが返る（カラムはスキーマと一致）."""
    mock_race_getter.get_race_shosai.return_value = pd.DataFrame()

    result = provider.get_race_schedule("20250101")

    assert len(result) == 0
    assert list(result.columns) == RACE_SCHEDULE_COLUMNS
