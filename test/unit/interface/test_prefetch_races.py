"""DataInterface.prefetch_races と キャッシュ参照のテスト."""

import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from keiba_data_interface.cache import DataCache
from keiba_data_interface.interface import DataInterface

_RACE_CODES = ["2020122806050811", "2020122806050812"]


def _make_basic_info(race_code: str) -> pd.DataFrame:
    """レース基本情報の1行を生成する.

    Args:
        race_code (str): 16桁レースコード

    Returns:
        pd.DataFrame: レース基本情報（1行）
    """
    return pd.DataFrame({"レースコード": [race_code], "芝ダ": ["芝"], "コース区分": ["A"]})


def _future_race_code() -> str:
    """未来（当日を含む）のレースコードを生成する.

    Returns:
        str: 16桁レースコード
    """
    return f"{datetime.date.today().strftime('%Y%m%d')}06050811"


class _BulkProvider:
    """一括取得に対応したテスト用Provider."""

    supports_bulk = True

    def __init__(self) -> None:
        """コンストラクタ."""
        self.get_race_basic_info = MagicMock(
            side_effect=lambda race_code: _make_basic_info(race_code)
        )
        self.get_race_basic_info_bulk = MagicMock(
            side_effect=lambda race_codes: pd.concat(
                [_make_basic_info(c) for c in race_codes], ignore_index=True
            )
        )


class _NoBulkProvider(_BulkProvider):
    """一括取得に未対応のテスト用Provider."""

    supports_bulk = False


@pytest.fixture
def bulk_interface() -> tuple[DataInterface, _BulkProvider]:
    """一括取得に対応したProviderを差し替えたDataInterface."""
    provider = _BulkProvider()
    with patch("keiba_data_interface.interface._create_provider", return_value=provider):
        interface = DataInterface("mykeibadb")
    return interface, provider


# 正常系
def test_prefetched_race_is_not_queried_again(
    bulk_interface: tuple[DataInterface, _BulkProvider],
) -> None:
    """プリフェッチ後、対象レースコードの取得でクエリが発行されない."""
    interface, provider = bulk_interface

    interface.prefetch_races(_RACE_CODES)
    for race_code in _RACE_CODES:
        interface.get_race_basic_info(race_code)

    provider.get_race_basic_info.assert_not_called()


def test_prefetch_issues_single_query(
    bulk_interface: tuple[DataInterface, _BulkProvider],
) -> None:
    """プリフェッチが発行するクエリはレース数によらず1回である."""
    interface, provider = bulk_interface

    interface.prefetch_races(_RACE_CODES)

    provider.get_race_basic_info_bulk.assert_called_once()


def test_cached_result_matches_uncached_result(
    bulk_interface: tuple[DataInterface, _BulkProvider],
) -> None:
    """戻り値がキャッシュの有無で完全に一致する."""
    interface, _ = bulk_interface
    race_code = _RACE_CODES[0]

    uncached = interface.get_race_basic_info(race_code)
    interface.clear_cache()
    interface.prefetch_races([race_code])
    cached = interface.get_race_basic_info(race_code)

    pd.testing.assert_frame_equal(cached, uncached)


def test_modifying_result_does_not_break_cache(
    bulk_interface: tuple[DataInterface, _BulkProvider],
) -> None:
    """戻り値を変更しても次回の戻り値が変わらない.

    キャッシュから返すのはコピーであること。
    """
    interface, _ = bulk_interface
    race_code = _RACE_CODES[0]
    interface.prefetch_races([race_code])

    first = interface.get_race_basic_info(race_code)
    first["芝ダ"] = "ダ"
    second = interface.get_race_basic_info(race_code)

    assert second["芝ダ"].iloc[0] == "芝"


def test_single_fetch_is_cached(
    bulk_interface: tuple[DataInterface, _BulkProvider],
) -> None:
    """プリフェッチしていなくても、一度取得した結果はキャッシュされる."""
    interface, provider = bulk_interface
    race_code = _RACE_CODES[0]

    interface.get_race_basic_info(race_code)
    interface.get_race_basic_info(race_code)

    provider.get_race_basic_info.assert_called_once()


def test_clear_cache_makes_next_call_query_again(
    bulk_interface: tuple[DataInterface, _BulkProvider],
) -> None:
    """clear_cacheの後は再びクエリが発行される."""
    interface, provider = bulk_interface
    race_code = _RACE_CODES[0]
    interface.prefetch_races([race_code])

    interface.clear_cache()
    interface.get_race_basic_info(race_code)

    provider.get_race_basic_info.assert_called_once()


def test_shared_cache_works_across_interfaces() -> None:
    """cacheを共有した2つのDataInterfaceでキャッシュが効く."""
    cache = DataCache()
    provider_a = _BulkProvider()
    provider_b = _BulkProvider()
    with patch("keiba_data_interface.interface._create_provider", return_value=provider_a):
        interface_a = DataInterface("mykeibadb", cache=cache)
    with patch("keiba_data_interface.interface._create_provider", return_value=provider_b):
        interface_b = DataInterface("mykeibadb", cache=cache)

    interface_a.prefetch_races(_RACE_CODES)
    interface_b.get_race_basic_info(_RACE_CODES[0])

    provider_b.get_race_basic_info.assert_not_called()


def test_course_days_are_not_cached(
    bulk_interface: tuple[DataInterface, _BulkProvider],
) -> None:
    """コース日数を付与した結果はキャッシュされない.

    キャッシュするのは付与前の値。付与の有無で戻り値が変わってしまわないこと。
    """
    interface, _ = bulk_interface
    race_code = _RACE_CODES[0]
    with_days = _make_basic_info(race_code)
    with_days["芝コース日目"] = 3

    with patch(
        "keiba_data_interface.course_days.calc_course_days", return_value=with_days
    ):
        interface.get_race_basic_info(race_code, calc_course_days=True)
    result = interface.get_race_basic_info(race_code)

    assert "芝コース日目" not in result.columns


# 準正常系
def test_future_race_is_not_cached(
    bulk_interface: tuple[DataInterface, _BulkProvider],
) -> None:
    """未来レースはプリフェッチに渡してもキャッシュされず、毎回取得される."""
    interface, provider = bulk_interface
    race_code = _future_race_code()

    interface.prefetch_races([race_code])
    interface.get_race_basic_info(race_code)
    interface.get_race_basic_info(race_code)

    assert provider.get_race_basic_info.call_count == 2


def test_future_race_is_excluded_from_bulk_query(
    bulk_interface: tuple[DataInterface, _BulkProvider],
) -> None:
    """未来レースは一括取得の対象からも外れる."""
    interface, provider = bulk_interface

    interface.prefetch_races([_RACE_CODES[0], _future_race_code()])

    passed = provider.get_race_basic_info_bulk.call_args[0][0]
    assert passed == [_RACE_CODES[0]]


def test_prefetch_with_only_future_races_issues_no_query(
    bulk_interface: tuple[DataInterface, _BulkProvider],
) -> None:
    """未来レースだけを渡した場合はクエリを発行しない."""
    interface, provider = bulk_interface

    interface.prefetch_races([_future_race_code()])

    provider.get_race_basic_info_bulk.assert_not_called()


def test_prefetch_deduplicates_race_codes(
    bulk_interface: tuple[DataInterface, _BulkProvider],
) -> None:
    """重複したレースコードは取り除いて問い合わせる."""
    interface, provider = bulk_interface

    interface.prefetch_races([_RACE_CODES[0], _RACE_CODES[0], _RACE_CODES[1]])

    passed = provider.get_race_basic_info_bulk.call_args[0][0]
    assert passed == _RACE_CODES


def test_prefetch_with_empty_list_issues_no_query(
    bulk_interface: tuple[DataInterface, _BulkProvider],
) -> None:
    """空リストを渡した場合はクエリを発行しない."""
    interface, provider = bulk_interface

    interface.prefetch_races([])

    provider.get_race_basic_info_bulk.assert_not_called()


def test_provider_without_bulk_support_does_nothing() -> None:
    """一括取得に未対応のProviderではプリフェッチが何もしない.

    例外にはしない。プリフェッチは高速化のための処理であり、行わなくても
    単一キー取得は従来どおり動作するため。
    """
    provider = _NoBulkProvider()
    with patch("keiba_data_interface.interface._create_provider", return_value=provider):
        interface = DataInterface("scraping")

    interface.prefetch_races(_RACE_CODES)
    result = interface.get_race_basic_info(_RACE_CODES[0])

    provider.get_race_basic_info_bulk.assert_not_called()
    provider.get_race_basic_info.assert_called_once()
    assert not result.empty


def test_shared_cache_separates_providers() -> None:
    """cacheを共有してもデータソースが異なれば値が混ざらない.

    同じレースコードでもデータソースが違えば値が異なりうる。
    """
    cache = DataCache()
    mykeibadb_provider = _BulkProvider()
    scraping_provider = _NoBulkProvider()
    with patch(
        "keiba_data_interface.interface._create_provider", return_value=mykeibadb_provider
    ):
        mykeibadb_interface = DataInterface("mykeibadb", cache=cache)
    with patch(
        "keiba_data_interface.interface._create_provider", return_value=scraping_provider
    ):
        scraping_interface = DataInterface("scraping", cache=cache)

    mykeibadb_interface.get_race_basic_info(_RACE_CODES[0])
    scraping_interface.get_race_basic_info(_RACE_CODES[0])

    scraping_provider.get_race_basic_info.assert_called_once()
