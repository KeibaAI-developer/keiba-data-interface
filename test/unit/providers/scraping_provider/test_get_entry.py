"""ScrapingProvider.get_entry関数のテスト."""

from unittest.mock import MagicMock

import pandas as pd

from keiba_data_interface.providers.scraping_provider import ScrapingProvider
from keiba_data_interface.schema.columns import HORSE_RACE_INFO_COLUMNS


# 正常系
def test_output_columns_match_schema(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    race_code: str,
) -> None:
    """出力DataFrameのカラム構成がHORSE_RACE_INFO_COLUMNSと一致する."""
    from .conftest import create_scraping_entry

    mock_scraper.get_entry.return_value = create_scraping_entry()

    result = provider.get_entry(race_code)

    assert list(result.columns) == HORSE_RACE_INFO_COLUMNS


def test_output_row_count(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    race_code: str,
) -> None:
    """出力DataFrameの行数が入力と一致する."""
    from .conftest import create_scraping_entry

    mock_scraper.get_entry.return_value = create_scraping_entry()

    result = provider.get_entry(race_code)

    assert len(result) == 2


def test_race_code_is_16_digits(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    race_code: str,
) -> None:
    """レースコードに引数の16桁がそのまま格納される."""
    from .conftest import create_scraping_entry

    mock_scraper.get_entry.return_value = create_scraping_entry()

    result = provider.get_entry(race_code)

    assert result.iloc[0]["レースコード"] == race_code
    assert result.iloc[1]["レースコード"] == race_code


def test_column_mapping(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    race_code: str,
) -> None:
    """カラム名マッピングが正しく変換される."""
    from .conftest import create_scraping_entry

    mock_scraper.get_entry.return_value = create_scraping_entry()

    result = provider.get_entry(race_code)

    row = result.iloc[0]
    assert row["血統登録番号"] == "2021105001"
    assert row["馬齢"] == 4
    assert row["負担重量"] == 58.0
    assert row["騎手名略称"] == "テスト騎手1"
    assert row["騎手コード"] == "01234"
    assert row["調教師名略称"] == "テスト厩舎1"
    assert row["調教師コード"] == "01111"
    assert row["馬名"] == "テスト馬1"
    assert row["性別コード"] == "1"
    assert row["所属コード"] == "2"
    assert row["枠番"] == 1
    assert row["馬番"] == 1
    assert row["馬体重"] == 480


def test_zogen_positive(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    race_code: str,
) -> None:
    """増減がプラスの場合、符号と差が正しく分離される."""
    from .conftest import create_scraping_entry

    mock_scraper.get_entry.return_value = create_scraping_entry()

    result = provider.get_entry(race_code)

    row = result.iloc[0]
    assert row["増減符号"] == "+"
    assert row["増減差"] == 2


def test_zogen_negative(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    race_code: str,
) -> None:
    """増減がマイナスの場合、符号と差が正しく分離される."""
    from .conftest import create_scraping_entry

    mock_scraper.get_entry.return_value = create_scraping_entry()

    result = provider.get_entry(race_code)

    row = result.iloc[1]
    assert row["増減符号"] == "-"
    assert row["増減差"] == 4


def test_zogen_zero(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    race_code: str,
) -> None:
    """増減がゼロの場合、増減差=0・増減符号=NaNになる."""
    from .conftest import create_scraping_entry

    entry = create_scraping_entry()
    entry.loc[0, "増減"] = 0
    mock_scraper.get_entry.return_value = entry

    result = provider.get_entry(race_code)

    row = result.iloc[0]
    assert pd.isna(row["増減符号"])
    assert row["増減差"] == 0


def test_zogen_nan(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    race_code: str,
) -> None:
    """増減がNaN（前計不）の場合、増減符号と増減差がNaNになる."""
    from .conftest import create_scraping_entry

    entry = create_scraping_entry()
    entry.loc[0, "増減"] = None
    mock_scraper.get_entry.return_value = entry

    result = provider.get_entry(race_code)

    row = result.iloc[0]
    assert pd.isna(row["増減符号"])
    assert pd.isna(row["増減差"])


def test_ijo_kubun_shutsuso(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    race_code: str,
) -> None:
    """出走区分"出走"が空文字に変換される."""
    from .conftest import create_scraping_entry

    mock_scraper.get_entry.return_value = create_scraping_entry()

    result = provider.get_entry(race_code)

    assert result.iloc[0]["異常区分コード"] == "0"


def test_ijo_kubun_torikeshi(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    race_code: str,
) -> None:
    """出走区分"取消"が"出走取消"に変換される."""
    from .conftest import create_scraping_entry

    entry = create_scraping_entry()
    entry.loc[0, "出走区分"] = "取消"
    mock_scraper.get_entry.return_value = entry

    result = provider.get_entry(race_code)

    assert result.iloc[0]["異常区分コード"] == "1"


def test_ijo_kubun_jogai(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    race_code: str,
) -> None:
    """出走区分"除外"が"競走除外"に変換される."""
    from .conftest import create_scraping_entry

    entry = create_scraping_entry()
    entry.loc[0, "出走区分"] = "除外"
    mock_scraper.get_entry.return_value = entry

    result = provider.get_entry(race_code)

    assert result.iloc[0]["異常区分コード"] == "3"


def test_missing_columns_filled_with_nan(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    race_code: str,
) -> None:
    """不足カラムがNaN埋めされる."""
    from .conftest import create_scraping_entry

    mock_scraper.get_entry.return_value = create_scraping_entry()

    result = provider.get_entry(race_code)

    row = result.iloc[0]
    assert pd.isna(row["品種"])
    assert pd.isna(row["毛色"])
    assert pd.isna(row["馬主コード"])
    assert pd.isna(row["確定着順"])
    assert pd.isna(row["走破タイム"])


def test_header_columns_from_race_code(
    provider: ScrapingProvider,
    mock_scraper: MagicMock,
    race_code: str,
) -> None:
    """開催年・開催月日・レース番号がrace_codeから導出される."""
    from .conftest import create_scraping_entry

    mock_scraper.get_entry.return_value = create_scraping_entry()

    result = provider.get_entry(race_code)

    row = result.iloc[0]
    assert row["開催年"] == "2025"
    assert row["開催月日"] == "0502"
    assert row["競馬場"] == "中山"
    assert row["開催回"] == 2
    assert row["開催日目"] == 12
    assert row["レース番号"] == 11
