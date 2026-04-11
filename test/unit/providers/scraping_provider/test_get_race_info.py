"""ScrapingProvider.get_race_info関数のテスト."""

from unittest.mock import MagicMock

import pandas as pd

from keiba_data_interface.providers.scraping_provider import ScrapingProvider
from keiba_data_interface.schema.columns import RACE_INFO_COLUMNS


# 正常系
def test_output_columns_match_schema(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    turf_race_info: pd.DataFrame,
    race_code: str,
) -> None:
    """出力DataFrameのカラム構成がRACE_INFO_COLUMNSと一致する."""
    mock_scraper.get_race_info.return_value = turf_race_info

    result = provider.get_race_info(race_code)

    assert list(result.columns) == RACE_INFO_COLUMNS


def test_output_is_single_row(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    turf_race_info: pd.DataFrame,
    race_code: str,
) -> None:
    """出力DataFrameが1行である."""
    mock_scraper.get_race_info.return_value = turf_race_info

    result = provider.get_race_info(race_code)

    assert len(result) == 1


def test_race_code_is_16_digits(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    turf_race_info: pd.DataFrame,
    race_code: str,
) -> None:
    """レースコードに引数の16桁がそのまま格納される."""
    mock_scraper.get_race_info.return_value = turf_race_info

    result = provider.get_race_info(race_code)

    assert result.iloc[0]["レースコード"] == race_code


def test_race_id_converted_to_12_digits(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    mock_scraper_cls: MagicMock,
    turf_race_info: pd.DataFrame,
    race_code: str,
) -> None:
    """EntryPageScraperに12桁レースIDが渡される."""
    mock_scraper.get_race_info.return_value = turf_race_info

    provider.get_race_info(race_code)

    mock_scraper_cls.assert_called_once_with("202506021211")


def test_date_split_to_year_and_monthday(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    turf_race_info: pd.DataFrame,
    race_code: str,
) -> None:
    """日付が開催年と開催月日に正しく分割される."""
    mock_scraper.get_race_info.return_value = turf_race_info

    result = provider.get_race_info(race_code)

    row = result.iloc[0]
    assert row["開催年"] == "2025"
    assert row["開催月日"] == "0502"


def test_direct_mapping_columns(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    turf_race_info: pd.DataFrame,
    race_code: str,
) -> None:
    """そのままマッピングされるカラムが正しく変換される."""
    mock_scraper.get_race_info.return_value = turf_race_info

    result = provider.get_race_info(race_code)

    row = result.iloc[0]
    assert row["競馬場"] == "京都"
    assert row["開催回"] == 3
    assert row["開催日目"] == 4
    assert row["レース番号"] == 11
    assert row["曜日"] == "日"
    assert row["競走名本題"] == "天皇賞(春)"
    assert row["発走時刻"] == "15:40"
    assert row["天候"] == "晴"
    assert row["距離"] == 3200
    assert row["競走種別コード"] == "14"
    assert row["競走条件名称"] == "オープン"
    assert row["グレードコード"] == "A"
    assert row["競走記号コード"] == "N01"
    assert row["重量種別"] == "定量"
    assert row["登録頭数"] == 18


def test_race_shubetsu_mapping(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    turf_race_info: pd.DataFrame,
    race_code: str,
) -> None:
    """レース種別がそのままマッピングされる."""
    mock_scraper.get_race_info.return_value = turf_race_info

    result = provider.get_race_info(race_code)

    assert result.iloc[0]["レース種別"] == "平地"


def test_shiba_da_mapping(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    turf_race_info: pd.DataFrame,
    race_code: str,
) -> None:
    """芝ダがそのままマッピングされる."""
    mock_scraper.get_race_info.return_value = turf_race_info

    result = provider.get_race_info(race_code)

    assert result.iloc[0]["芝ダ"] == "芝"


def test_sayuu_mapping(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    turf_race_info: pd.DataFrame,
    race_code: str,
) -> None:
    """左右がそのままマッピングされる."""
    mock_scraper.get_race_info.return_value = turf_race_info

    result = provider.get_race_info(race_code)

    assert result.iloc[0]["左右"] == "左"


def test_uchisoto_mapping(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    race_code: str,
) -> None:
    """内外がそのままマッピングされる."""
    from .conftest import create_scraping_race_info

    mock_scraper.get_race_info.return_value = create_scraping_race_info(uchisoto="外")

    result = provider.get_race_info(race_code)

    assert result.iloc[0]["内外"] == "外"


def test_uchisoto_empty_becomes_nan(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    turf_race_info: pd.DataFrame,
    race_code: str,
) -> None:
    """内外が空文字の場合NaNになる."""
    mock_scraper.get_race_info.return_value = turf_race_info

    result = provider.get_race_info(race_code)

    assert pd.isna(result.iloc[0]["内外"])


def test_steeplechase_shiba_da_and_race_shubetsu(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    race_code: str,
) -> None:
    """障害レースの芝ダが芝、レース種別が障害となる."""
    from .conftest import create_scraping_race_info

    mock_scraper.get_race_info.return_value = create_scraping_race_info(
        shiba_da="芝", race_shubetsu="障害"
    )

    result = provider.get_race_info(race_code)

    assert result.iloc[0]["芝ダ"] == "芝"
    assert result.iloc[0]["レース種別"] == "障害"


def test_track_code_is_nan_for_scraping(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    turf_race_info: pd.DataFrame,
    race_code: str,
) -> None:
    """scrapingではトラックコードはNaNになる."""
    mock_scraper.get_race_info.return_value = turf_race_info

    result = provider.get_race_info(race_code)

    assert pd.isna(result.iloc[0]["トラックコード"])


def test_course_division_concatenation(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    race_code: str,
) -> None:
    """コースがコース区分カラムになる."""
    from .conftest import create_scraping_race_info

    mock_scraper.get_race_info.return_value = create_scraping_race_info(course="B", uchisoto="内")

    result = provider.get_race_info(race_code)

    assert result.iloc[0]["コース区分"] == "B"


def test_prize_money_conversion(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    turf_race_info: pd.DataFrame,
    race_code: str,
) -> None:
    """賞金が万円単位から百円単位に正しく変換される."""
    mock_scraper.get_race_info.return_value = turf_race_info

    result = provider.get_race_info(race_code)

    row = result.iloc[0]
    assert row["本賞金1着"] == 3200000
    assert row["本賞金2着"] == 1280000
    assert row["本賞金3着"] == 800000
    assert row["本賞金4着"] == 480000
    assert row["本賞金5着"] == 320000


def test_turf_race_baba_assignment(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    turf_race_info: pd.DataFrame,
    race_code: str,
) -> None:
    """芝レースで馬場状態が芝馬場状態に格納される."""
    mock_scraper.get_race_info.return_value = turf_race_info

    result = provider.get_race_info(race_code)

    row = result.iloc[0]
    assert row["芝馬場状態コード"] == "1"
    assert pd.isna(row["ダート馬場状態コード"])


def test_dirt_race_baba_assignment(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    dirt_race_info: pd.DataFrame,
    race_code: str,
) -> None:
    """ダートレースで馬場状態がダート馬場状態に格納される."""
    mock_scraper.get_race_info.return_value = dirt_race_info

    result = provider.get_race_info(race_code)

    row = result.iloc[0]
    assert pd.isna(row["芝馬場状態コード"])
    assert row["ダート馬場状態コード"] == "3"


def test_missing_columns_filled_with_nan(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    turf_race_info: pd.DataFrame,
    race_code: str,
) -> None:
    """不足カラムがNaN埋めされる."""
    mock_scraper.get_race_info.return_value = turf_race_info

    result = provider.get_race_info(race_code)

    row = result.iloc[0]
    # scrapingでは取得できないカラムはNaNになる
    assert pd.isna(row["特別競走番号"])
    assert pd.isna(row["競走名副題"])
    assert pd.isna(row["競走名カッコ内"])
    assert pd.isna(row["変更前距離"])
    assert pd.isna(row["本賞金6着"])
    assert pd.isna(row["出走頭数"])
    assert pd.isna(row["入線頭数"])


def test_steeplechase_baba_assignment(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    race_code: str,
) -> None:
    """障害レースで馬場状態が芝馬場状態に格納される."""
    from .conftest import create_scraping_race_info

    mock_scraper.get_race_info.return_value = create_scraping_race_info(
        shiba_da="芝", race_shubetsu="障害", baba="稍"
    )

    result = provider.get_race_info(race_code)

    row = result.iloc[0]
    assert row["芝馬場状態コード"] == "2"
    assert pd.isna(row["ダート馬場状態コード"])


def test_date_differs_from_race_code_year_and_monthday_come_from_race_code(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    race_code: str,
) -> None:
    """rawの日付がrace_codeと異なる場合でも開催年/開催月日はrace_codeから導出される."""
    from datetime import date

    from .conftest import create_scraping_race_info

    # race_code=2025050206021211 に対して日付を意図的にずらす
    raw = create_scraping_race_info()
    raw["日付"] = date(2099, 12, 31)
    mock_scraper.get_race_info.return_value = raw

    result = provider.get_race_info(race_code)

    row = result.iloc[0]
    assert row["開催年"] == "2025"
    assert row["開催月日"] == "0502"


# 準正常系
def test_empty_raw_raises_value_error(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    race_code: str,
) -> None:
    """スクレイパが空DataFrameを返した場合にValueErrorが発生する."""
    import pytest

    mock_scraper.get_race_info.return_value = pd.DataFrame()

    with pytest.raises(ValueError, match="空のDataFrame"):
        provider.get_race_info(race_code)


def test_multiple_rows_raw_raises_value_error(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    turf_race_info: pd.DataFrame,
    race_code: str,
) -> None:
    """スクレイパが複数行のDataFrameを返した場合にValueErrorが発生する."""
    import pytest

    mock_scraper.get_race_info.return_value = pd.concat(
        [turf_race_info, turf_race_info], ignore_index=True
    )

    with pytest.raises(ValueError, match="2行"):
        provider.get_race_info(race_code)
