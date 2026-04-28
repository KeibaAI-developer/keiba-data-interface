"""ScrapingProvider.get_horse_master関数のテスト."""

from datetime import date
from unittest.mock import MagicMock

import pandas as pd
import pytest

from keiba_data_interface.providers.scraping_provider import ScrapingProvider
from keiba_data_interface.schema.columns import HORSE_MASTER_COLUMNS


def _create_chuo_past_performances() -> pd.DataFrame:
    """中央レース1戦（芝良・1着）の過去成績データを生成する."""
    return pd.DataFrame(
        [
            {
                "レースID": "202505011201",
                "日付": date(2025, 1, 5),
                "競馬場": "中山",
                "回": 1,
                "開催日": 1,
                "R": 12,
                "レース名": "テストレース",
                "天候": "晴",
                "頭数": 16,
                "枠": 3,
                "馬番": 5,
                "単勝オッズ": 5.0,
                "人気": "2",
                "着順": "1",
                "異常区分": "出走",
                "騎手": "テスト騎手",
                "騎手ID": "01234",
                "斤量": 57.0,
                "芝ダ": "芝",
                "距離": 2000,
                "馬場": "良",
                "タイム": "2:00.5",
                "着差": 0.5,
                "1コーナー通過順": 3,
                "2コーナー通過順": 3,
                "3コーナー通過順": 2,
                "4コーナー通過順": 1,
                "レース前3F": 35.5,
                "レース後3F": 34.8,
                "後3F": 34.5,
                "馬体重": 480,
                "増減": 2,
                "勝ち馬(2着馬)": "ライバル馬",
                "賞金": 1000,
                "主催": "中央",
                "間隔日数": 28,
            },
        ]
    )


# 正常系
def test_output_columns_match_schema(
    provider_full: ScrapingProvider,
    mock_past_scraper: MagicMock,
) -> None:
    """出力DataFrameのカラム構成がHORSE_MASTER_COLUMNSと一致する."""
    mock_past_scraper.get_past_performances.return_value = _create_chuo_past_performances()

    result = provider_full.get_horse_master("2021105001")

    assert list(result.columns) == HORSE_MASTER_COLUMNS


def test_output_row_count(
    provider_full: ScrapingProvider,
    mock_past_scraper: MagicMock,
) -> None:
    """出力DataFrameの行数が1行である."""
    mock_past_scraper.get_past_performances.return_value = pd.DataFrame()

    result = provider_full.get_horse_master("2021105001")

    assert len(result) == 1


def test_horse_id_stored(
    provider_full: ScrapingProvider,
    mock_past_scraper: MagicMock,
) -> None:
    """血統登録番号（馬ID）が格納される."""
    mock_past_scraper.get_past_performances.return_value = pd.DataFrame()

    result = provider_full.get_horse_master("2021105001")

    assert result.iloc[0]["血統登録番号"] == "2021105001"


def test_basic_info_columns_from_horse_basic_info(
    provider_full: ScrapingProvider,
    mock_past_scraper: MagicMock,
) -> None:
    """horse_basic_infoから基本情報が設定される."""
    mock_past_scraper.get_past_performances.return_value = pd.DataFrame()

    result = provider_full.get_horse_master("2021105001")

    row = result.iloc[0]
    assert row["馬名"] == "テスト馬"
    assert row["性別コード"] == "1"  # 牡 → 1
    assert row["調教師コード"] == "01234"
    assert row["調教師名略称"] == "テスト調教師"
    assert row["生産者名"] == "テスト牧場"
    assert row["産地名"] == "安平町"
    assert row["馬主名"] == "テスト馬主"


def test_seisansha_code_appended(
    provider_full: ScrapingProvider,
    mock_past_scraper: MagicMock,
) -> None:
    """生産者コードに'00'が付加される."""
    mock_past_scraper.get_past_performances.return_value = pd.DataFrame()

    result = provider_full.get_horse_master("2021105001")

    assert result.iloc[0]["生産者コード"] == "65432100"


def test_ketto_columns_from_horse_basic_info(
    provider_full: ScrapingProvider,
    mock_past_scraper: MagicMock,
) -> None:
    """horse_basic_infoから血統情報が設定される."""
    mock_past_scraper.get_past_performances.return_value = pd.DataFrame()

    result = provider_full.get_horse_master("2021105001")

    row = result.iloc[0]
    assert row["父馬名"] == "テスト父"
    assert row["母馬名"] == "テスト母"
    assert row["母父馬名"] == "テスト母父"


def test_empty_horse_basic_info_does_not_raise(
    provider_full: ScrapingProvider,
    mock_past_scraper: MagicMock,
) -> None:
    """horse_basic_infoが空DataFrameでも正常に動作する."""
    mock_past_scraper.get_past_performances.return_value = pd.DataFrame()
    mock_past_scraper.get_horse_basic_info.return_value = pd.DataFrame()

    result = provider_full.get_horse_master("2021105001")

    assert list(result.columns) == HORSE_MASTER_COLUMNS
    assert len(result) == 1


def test_chaku_count_from_past_performances(
    provider_full: ScrapingProvider,
    mock_past_scraper: MagicMock,
) -> None:
    """過去成績から着回数が算出される."""
    mock_past_scraper.get_past_performances.return_value = _create_chuo_past_performances()

    result = provider_full.get_horse_master("2021105001")

    row = result.iloc[0]
    assert row["総合1着"] == 1
    assert row["中央合計1着"] == 1
    assert row["芝良1着"] == 1


def test_empty_past_performances_chaku_zero(
    provider_full: ScrapingProvider,
    mock_past_scraper: MagicMock,
) -> None:
    """過去成績が空の場合は着回数が0になる."""
    mock_past_scraper.get_past_performances.return_value = pd.DataFrame()

    result = provider_full.get_horse_master("2021105001")

    row = result.iloc[0]
    assert row["総合1着"] == 0
    assert row["中央合計1着"] == 0


def test_direction_chaku_count_from_keibajo(
    provider_full: ScrapingProvider,
    mock_past_scraper: MagicMock,
) -> None:
    """競馬場から方向別着回数が算出される（中山=右回りなので芝右に加算）."""
    mock_past_scraper.get_past_performances.return_value = _create_chuo_past_performances()

    result = provider_full.get_horse_master("2021105001")

    row = result.iloc[0]
    assert row["芝右1着"] == 1
    assert row["芝左1着"] == 0


@pytest.mark.parametrize(
    "shozoku, expected_code",
    [
        ("美浦", "1"),
        ("栗東", "2"),
        ("浦和", "3"),
        ("", None),
    ],
    ids=["miho", "ritto", "urawa_chiho", "empty"],
)
def test_tozai_shozoku_code(
    provider_full: ScrapingProvider,
    mock_past_scraper: MagicMock,
    shozoku: str,
    expected_code: str,
) -> None:
    """所属から東西所属コードが設定される."""
    from .conftest import create_scraping_horse_basic_info

    mock_past_scraper.get_past_performances.return_value = pd.DataFrame()
    mock_past_scraper.get_horse_basic_info.return_value = create_scraping_horse_basic_info(
        shozoku=shozoku
    )

    result = provider_full.get_horse_master("2021105001")

    if expected_code is None:
        assert pd.isna(result.iloc[0]["東西所属コード"])
    else:
        assert result.iloc[0]["東西所属コード"] == expected_code


def test_seisansha_code_kaigai_zero(
    provider_full: ScrapingProvider,
    mock_past_scraper: MagicMock,
) -> None:
    """所属が海外の場合、生産者コードは'00000000'になる."""
    from .conftest import create_scraping_horse_basic_info

    mock_past_scraper.get_past_performances.return_value = pd.DataFrame()
    mock_past_scraper.get_horse_basic_info.return_value = create_scraping_horse_basic_info(
        shozoku="海外"
    )

    result = provider_full.get_horse_master("2021190001")

    assert result.iloc[0]["生産者コード"] == "00000000"
