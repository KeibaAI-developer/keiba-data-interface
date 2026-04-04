"""ScrapingProvider.get_result関数のテスト."""

from unittest.mock import MagicMock

import pandas as pd

from keiba_data_interface.providers.scraping_provider import ScrapingProvider
from keiba_data_interface.schema.columns import HORSE_RACE_INFO_COLUMNS


# 正常系
def test_output_columns_match_schema(
    provider_full: ScrapingProvider,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """出力DataFrameのカラム構成がHORSE_RACE_INFO_COLUMNSと一致する."""
    from .conftest import _create_scraping_result

    mock_result_scraper.get_result.return_value = _create_scraping_result()

    result = provider_full.get_result(race_code)

    assert list(result.columns) == HORSE_RACE_INFO_COLUMNS


def test_output_row_count(
    provider_full: ScrapingProvider,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """出力DataFrameの行数が入力と一致する."""
    from .conftest import _create_scraping_result

    mock_result_scraper.get_result.return_value = _create_scraping_result()

    result = provider_full.get_result(race_code)

    assert len(result) == 2


def test_time_sa_normal(
    provider_full: ScrapingProvider,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """タイム差が1着タイムとの差から正しく計算される."""
    from .conftest import _create_scraping_result

    mock_result_scraper.get_result.return_value = _create_scraping_result()

    result = provider_full.get_result(race_code)

    # 1着: 3:12.5 = 192.5秒、2着: 3:13.0 = 193.0秒 → 1着は-(2着-1着)=-0.5
    assert result.iloc[0]["タイム差"] == -0.5
    assert result.iloc[1]["タイム差"] == 0.5


def test_time_sa_excluded_for_chushi(
    provider_full: ScrapingProvider,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """競走中止馬のタイム差はNaNになる."""
    from .conftest import _create_scraping_result

    raw = _create_scraping_result()
    raw.loc[1, "異常区分"] = "中止"
    raw.loc[1, "着順"] = "中止"
    raw.loc[1, "タイム"] = None
    mock_result_scraper.get_result.return_value = raw

    result = provider_full.get_result(race_code)

    assert pd.isna(result.iloc[1]["タイム差"])


def test_ijo_kubun_kokaku(
    provider_full: ScrapingProvider,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """降着が着差テキストから正しく検出される."""
    from .conftest import _create_scraping_result

    raw = _create_scraping_result()
    raw.loc[0, "着差"] = "1位降着"
    mock_result_scraper.get_result.return_value = raw

    result = provider_full.get_result(race_code)

    assert result.iloc[0]["異常区分コード"] == "7"


def test_ijo_kubun_chushi(
    provider_full: ScrapingProvider,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """競走中止の異常区分が正しく変換される."""
    from .conftest import _create_scraping_result

    raw = _create_scraping_result()
    raw.loc[1, "異常区分"] = "中止"
    raw.loc[1, "着順"] = "中止"
    mock_result_scraper.get_result.return_value = raw

    result = provider_full.get_result(race_code)

    assert result.iloc[1]["異常区分コード"] == "4"


def test_ijo_kubun_shikkaku(
    provider_full: ScrapingProvider,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """失格の異常区分が正しく変換される."""
    from .conftest import _create_scraping_result

    raw = _create_scraping_result()
    raw.loc[1, "異常区分"] = "失格"
    raw.loc[1, "着順"] = "失格"
    mock_result_scraper.get_result.return_value = raw

    result = provider_full.get_result(race_code)

    assert result.iloc[1]["異常区分コード"] == "5"


def test_result_columns_mapped(
    provider_full: ScrapingProvider,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """結果固有カラムが正しくマッピングされる."""
    from .conftest import _create_scraping_result

    mock_result_scraper.get_result.return_value = _create_scraping_result()

    result = provider_full.get_result(race_code)

    row = result.iloc[0]
    assert row["確定着順"] == 1
    assert row["走破タイム"] == "3:12.5"
    assert row["単勝人気順"] == 1
    assert row["単勝オッズ"] == 3.5
    assert row["後3ハロン"] == 35.2
    assert row["1コーナー順位"] == 3
    assert row["4コーナー順位"] == 1


def test_chakusa_mapped(
    provider_full: ScrapingProvider,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """着差が着差コード1に正しくマッピングされる."""
    from .conftest import _create_scraping_result

    mock_result_scraper.get_result.return_value = _create_scraping_result()

    result = provider_full.get_result(race_code)

    assert result.iloc[1]["着差コード1"] == "K__"


def test_cockaku_chakusa_not_mapped_to_chakusa1(
    provider_full: ScrapingProvider,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """降着の場合、着差テキストは着差コード1にマッピングされない."""
    from .conftest import _create_scraping_result

    raw = _create_scraping_result()
    raw.loc[0, "着差"] = "1位降着"
    mock_result_scraper.get_result.return_value = raw

    result = provider_full.get_result(race_code)

    assert pd.isna(result.iloc[0]["着差コード1"])


def test_header_columns_from_race_code(
    provider_full: ScrapingProvider,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """ヘッダカラムがレースコードから正しく導出される."""
    from .conftest import _create_scraping_result

    mock_result_scraper.get_result.return_value = _create_scraping_result()

    result = provider_full.get_result(race_code)

    row = result.iloc[0]
    assert row["開催年"] == "2025"
    assert row["開催月日"] == "0502"
    assert row["競馬場"] == "中山"
    assert row["開催回"] == 2
    assert row["開催日目"] == 12
    assert row["レース番号"] == 11


def test_kakutoku_honshokin_derived(
    provider_full: ScrapingProvider,
    mock_scraper: MagicMock,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """着順とRaceInfo賞金から獲得本賞金が正しく導出される."""
    from .conftest import _create_scraping_race_info, _create_scraping_result

    mock_scraper.get_race_info.return_value = _create_scraping_race_info()
    mock_result_scraper.get_result.return_value = _create_scraping_result()

    result = provider_full.get_result(race_code)

    # 1着: 32000万円 → 3200000百円
    assert result.iloc[0]["獲得本賞金"] == 3200000
    # 2着: 12800万円 → 1280000百円
    assert result.iloc[1]["獲得本賞金"] == 1280000


def test_kakutoku_honshokin_nan_for_6th_and_below(
    provider_full: ScrapingProvider,
    mock_scraper: MagicMock,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """6着以下の獲得本賞金は0になる."""
    from .conftest import _create_scraping_race_info, _create_scraping_result

    raw = _create_scraping_result()
    raw.loc[1, "着順"] = "6"
    mock_scraper.get_race_info.return_value = _create_scraping_race_info()
    mock_result_scraper.get_result.return_value = raw

    result = provider_full.get_result(race_code)

    assert result.iloc[1]["獲得本賞金"] == 0


def test_kakutoku_honshokin_nan_for_ijo_kubun(
    provider_full: ScrapingProvider,
    mock_scraper: MagicMock,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """異常区分が空でない馬の獲得本賞金は0になる."""
    from .conftest import _create_scraping_race_info, _create_scraping_result

    raw = _create_scraping_result()
    raw.loc[0, "異常区分"] = "失格"
    raw.loc[0, "着順"] = "失格"
    mock_scraper.get_race_info.return_value = _create_scraping_race_info()
    mock_result_scraper.get_result.return_value = raw

    result = provider_full.get_result(race_code)

    assert result.iloc[0]["獲得本賞金"] == 0


def test_time_sa_nan_when_all_chushi(
    provider_full: ScrapingProvider,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """全馬競走中止の場合、全行のタイム差がNaNになる."""
    from .conftest import _create_scraping_result

    raw = _create_scraping_result()
    raw.loc[0, "着順"] = "中止"
    raw.loc[0, "タイム"] = None
    raw.loc[0, "異常区分"] = "中止"
    raw.loc[1, "着順"] = "中止"
    raw.loc[1, "タイム"] = None
    raw.loc[1, "異常区分"] = "中止"
    mock_result_scraper.get_result.return_value = raw

    result = provider_full.get_result(race_code)

    assert pd.isna(result.iloc[0]["タイム差"])
    assert pd.isna(result.iloc[1]["タイム差"])
