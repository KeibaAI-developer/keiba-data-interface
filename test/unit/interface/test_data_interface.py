"""DataInterfaceクラスのテスト."""

from unittest.mock import call, patch

import pandas as pd
import pytest

from keiba_data_interface.exceptions import KeibaDataInterfaceError
from keiba_data_interface.interface import DataInterface
from keiba_data_interface.protocols import DataProvider
from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.providers.scraping_provider import ScrapingProvider
from keiba_data_interface.schema.columns import RACE_BASIC_INFO_COLUMNS

from .conftest import _MockProvider


# 正常系
def test_mock_provider_satisfies_protocol(mock_provider: _MockProvider) -> None:
    """モックProviderがDataProviderのインスタンスと判定される."""
    assert isinstance(mock_provider, DataProvider)


def test_create_scraping_provider() -> None:
    """provider='scraping'でScrapingProviderが生成される."""
    interface = DataInterface(provider="scraping")
    assert isinstance(interface._provider, ScrapingProvider)


def test_create_mykeibadb_provider() -> None:
    """provider='mykeibadb'でMykeibaDBProviderが生成される."""
    with (
        patch("keiba_data_interface.providers.mykeibadb_provider.RaceGetter"),
        patch("keiba_data_interface.providers.mykeibadb_provider.OddsGetter"),
        patch("keiba_data_interface.providers.mykeibadb_provider.MasterGetter"),
        patch("keiba_data_interface.providers.mykeibadb_provider.ShussobetsuGetter"),
    ):
        interface = DataInterface(provider="mykeibadb")
        assert isinstance(interface._provider, MykeibaDBProvider)


def test_supports_bulk_reflects_provider(
    interface_with_mock: tuple[DataInterface, _MockProvider],
) -> None:
    """supports_bulkがProviderの値をそのまま返す."""
    interface, mock_provider = interface_with_mock

    mock_provider.supports_bulk = True
    assert interface.supports_bulk is True

    mock_provider.supports_bulk = False
    assert interface.supports_bulk is False


def test_get_race_basic_info_delegates(
    interface_with_mock: tuple[DataInterface, _MockProvider],
) -> None:
    """get_race_basic_infoがProviderに委譲される."""
    interface, mock_provider = interface_with_mock
    result = interface.get_race_basic_info("2025050206021211")
    mock_provider.get_race_basic_info.assert_called_once_with("2025050206021211")
    pd.testing.assert_frame_equal(result, pd.DataFrame({"col": [1]}))


def test_get_race_basic_info_bulk_delegates(
    interface_with_mock: tuple[DataInterface, _MockProvider],
) -> None:
    """get_race_basic_info_bulkがProviderに委譲される."""
    interface, mock_provider = interface_with_mock
    race_codes = ["2025050206021211", "2025050206021212"]
    result = interface.get_race_basic_info_bulk(race_codes)
    mock_provider.get_race_basic_info_bulk.assert_called_once_with(race_codes)
    pd.testing.assert_frame_equal(result, pd.DataFrame({"col": [11]}))


def test_get_race_basic_info_bulk_does_not_calc_course_days(
    interface_with_mock: tuple[DataInterface, _MockProvider],
) -> None:
    """get_race_basic_info_bulkが芝コース日数を計算しない.

    開催日ごとの遡及取得が必要で、まとめて取得する利点が失われるため付与しない。
    """
    interface, _ = interface_with_mock
    with patch("keiba_data_interface.course_days.calc_course_days") as mock_calc:
        interface.get_race_basic_info_bulk(["2025050206021211"])
    mock_calc.assert_not_called()


def test_get_race_basic_info_with_calc_course_days(
    interface_with_mock: tuple[DataInterface, _MockProvider],
) -> None:
    """calc_course_days=Trueで芝コース日数の計算結果が返される."""
    interface, mock_provider = interface_with_mock
    expected = pd.DataFrame({"col": [10]})
    with patch(
        "keiba_data_interface.course_days.calc_course_days", return_value=expected
    ) as mock_calc:
        result = interface.get_race_basic_info("2025050206021211", calc_course_days=True)
    mock_provider.get_race_basic_info.assert_called_once_with("2025050206021211")
    mock_calc.assert_called_once()
    pd.testing.assert_frame_equal(result, expected)


def test_get_race_basic_info_without_calc_course_days(
    interface_with_mock: tuple[DataInterface, _MockProvider],
) -> None:
    """デフォルトでは芝コース日数の計算が行われない."""
    interface, _ = interface_with_mock
    with patch("keiba_data_interface.course_days.calc_course_days") as mock_calc:
        interface.get_race_basic_info("2025050206021211")
    mock_calc.assert_not_called()


def test_get_race_basic_info_calc_course_days_end_to_end(
    interface_with_mock: tuple[DataInterface, _MockProvider],
) -> None:
    """calc_course_days=Trueで芝コース日数4カラムが計算値で埋まる."""
    interface, mock_provider = interface_with_mock
    values: list[object] = [pd.NA] * len(RACE_BASIC_INFO_COLUMNS)
    race_basic_info = pd.DataFrame([values], columns=RACE_BASIC_INFO_COLUMNS)
    race_basic_info["レースコード"] = "2025060805020111"
    race_basic_info["開催年"] = "2025"
    race_basic_info["開催月日"] = "0608"
    race_basic_info["競馬場コード"] = "05"
    race_basic_info["芝ダ"] = "芝"
    race_basic_info["コース区分"] = "A"
    mock_provider.get_race_basic_info.return_value = race_basic_info
    schedule_columns = ["開催年", "開催月日", "競馬場コード", "開催回", "開催日目"]
    mock_provider.get_schedule.return_value = pd.DataFrame(columns=schedule_columns)

    result = interface.get_race_basic_info("2025060805020111", calc_course_days=True)

    assert result["芝コース日目"].iloc[0] == 1
    assert result["芝コース初日"].iloc[0] == "20250608"
    assert result["芝コース経過日数"].iloc[0] == 1
    assert result["芝コース週目"].iloc[0] == 1


def test_get_entry_delegates(
    interface_with_mock: tuple[DataInterface, _MockProvider],
) -> None:
    """get_entryがProviderに委譲される."""
    interface, mock_provider = interface_with_mock
    result = interface.get_entry("2025050206021211")
    mock_provider.get_entry.assert_called_once_with("2025050206021211")
    pd.testing.assert_frame_equal(result, pd.DataFrame({"col": [2]}))


def test_get_win_show_odds_delegates(
    interface_with_mock: tuple[DataInterface, _MockProvider],
) -> None:
    """get_win_show_oddsがProviderに委譲される."""
    interface, mock_provider = interface_with_mock
    result = interface.get_win_show_odds("2025050206021211")
    mock_provider.get_win_show_odds.assert_called_once_with("2025050206021211")
    pd.testing.assert_frame_equal(result, pd.DataFrame({"col": [3]}))


def test_get_result_delegates(
    interface_with_mock: tuple[DataInterface, _MockProvider],
) -> None:
    """get_resultがProviderに委譲される."""
    interface, mock_provider = interface_with_mock
    result = interface.get_result("2025050206021211")
    mock_provider.get_result.assert_called_once_with("2025050206021211")
    pd.testing.assert_frame_equal(result, pd.DataFrame({"col": [4]}))


def test_get_race_result_info_delegates(
    interface_with_mock: tuple[DataInterface, _MockProvider],
) -> None:
    """get_race_result_infoがProviderに委譲される."""
    interface, mock_provider = interface_with_mock
    result = interface.get_race_result_info("2025050206021211")
    mock_provider.get_race_result_info.assert_called_once_with("2025050206021211")
    pd.testing.assert_frame_equal(result, pd.DataFrame({"col": [5]}))


def test_get_payoff_delegates(
    interface_with_mock: tuple[DataInterface, _MockProvider],
) -> None:
    """get_payoffがProviderに委譲される."""
    interface, mock_provider = interface_with_mock
    result = interface.get_payoff("2025050206021211")
    mock_provider.get_payoff.assert_called_once_with("2025050206021211")
    pd.testing.assert_frame_equal(result, pd.DataFrame({"col": [6]}))


def test_get_past_performances_delegates(
    interface_with_mock: tuple[DataInterface, _MockProvider],
) -> None:
    """get_past_performancesがProviderに委譲される."""
    interface, mock_provider = interface_with_mock
    result = interface.get_past_performances("2022105102")
    mock_provider.get_past_performances.assert_called_once_with("2022105102")
    pd.testing.assert_frame_equal(result, pd.DataFrame({"col": [7]}))


def test_get_past_performances_bulk_delegates_when_provider_supports_bulk(
    interface_with_mock: tuple[DataInterface, _MockProvider],
) -> None:
    """一括取得に対応したProviderではget_past_performances_bulkへ委譲される."""
    interface, mock_provider = interface_with_mock
    mock_provider.supports_bulk = True

    result = interface.get_past_performances_bulk(["2022105102"])

    mock_provider.get_past_performances_bulk.assert_called_once_with(["2022105102"])
    assert result == mock_provider.get_past_performances_bulk.return_value


def test_get_past_performances_bulk_fetches_one_by_one_when_not_supported(
    interface_with_mock: tuple[DataInterface, _MockProvider],
) -> None:
    """一括取得に未対応のProviderでは1頭ずつ取得して同じ形の辞書を返す.

    プリフェッチと違い戻り値そのものが必要なため、何もしないわけにはいかない。
    Providerの能力差を吸収するのはDataInterfaceの役割であり、呼び出し側が
    Providerの種類で分岐しなくて済む。

    馬IDと戻り値の対応が入れ替わらないことも検証する。
    """
    interface, mock_provider = interface_with_mock
    mock_provider.supports_bulk = False
    by_horse = {
        "2022105102": pd.DataFrame({"col": [1]}),
        "2022105081": pd.DataFrame({"col": [2]}),
    }
    mock_provider.get_past_performances.side_effect = lambda horse_id: by_horse[horse_id]

    result = interface.get_past_performances_bulk(["2022105102", "2022105081"])

    mock_provider.get_past_performances_bulk.assert_not_called()
    mock_provider.get_past_performances.assert_has_calls(
        [call("2022105102"), call("2022105081")]
    )
    assert set(result) == set(by_horse)
    for horse_id, expected in by_horse.items():
        pd.testing.assert_frame_equal(result[horse_id], expected)


def test_get_past_performances_bulk_does_not_fetch_duplicated_horse_twice(
    interface_with_mock: tuple[DataInterface, _MockProvider],
) -> None:
    """一括取得に未対応のProviderでも、重複した馬IDは1回だけ取得する."""
    interface, mock_provider = interface_with_mock
    mock_provider.supports_bulk = False

    interface.get_past_performances_bulk(["2022105102", "2022105102"])

    assert mock_provider.get_past_performances.call_count == 1


def test_get_horse_master_delegates(
    interface_with_mock: tuple[DataInterface, _MockProvider],
) -> None:
    """get_horse_masterがProviderに委譲される."""
    interface, mock_provider = interface_with_mock
    result = interface.get_horse_master("2022105081")
    mock_provider.get_horse_master.assert_called_once_with("2022105081")
    pd.testing.assert_frame_equal(result, pd.DataFrame({"col": [8]}))


def test_get_horse_master_bulk_delegates_when_provider_supports_bulk(
    interface_with_mock: tuple[DataInterface, _MockProvider],
) -> None:
    """一括取得に対応したProviderではget_horse_master_bulkへ委譲される."""
    interface, mock_provider = interface_with_mock
    mock_provider.supports_bulk = True

    result = interface.get_horse_master_bulk(["2022105081"])

    mock_provider.get_horse_master_bulk.assert_called_once_with(["2022105081"])
    assert result == mock_provider.get_horse_master_bulk.return_value


def test_get_horse_master_bulk_fetches_one_by_one_when_not_supported(
    interface_with_mock: tuple[DataInterface, _MockProvider],
) -> None:
    """一括取得に未対応のProviderでは1頭ずつ取得して同じ形の辞書を返す.

    馬IDと戻り値の対応が入れ替わらないことも検証する。
    """
    interface, mock_provider = interface_with_mock
    mock_provider.supports_bulk = False
    by_horse = {
        "2022105081": pd.DataFrame({"col": [1]}),
        "2022105102": pd.DataFrame({"col": [2]}),
    }
    mock_provider.get_horse_master.side_effect = lambda horse_id: by_horse[horse_id]

    result = interface.get_horse_master_bulk(["2022105081", "2022105102"])

    mock_provider.get_horse_master_bulk.assert_not_called()
    mock_provider.get_horse_master.assert_has_calls(
        [call("2022105081"), call("2022105102")]
    )
    assert set(result) == set(by_horse)
    for horse_id, expected in by_horse.items():
        pd.testing.assert_frame_equal(result[horse_id], expected)


def test_get_chakudosu_delegates(
    interface_with_mock: tuple[DataInterface, _MockProvider],
) -> None:
    """get_chakudosuがProviderに委譲される."""
    interface, mock_provider = interface_with_mock
    result = interface.get_chakudosu("2025050206021211")
    mock_provider.get_chakudosu.assert_called_once_with("2025050206021211")
    pd.testing.assert_frame_equal(result, pd.DataFrame({"col": [9]}))


def test_get_schedule_delegates(
    interface_with_mock: tuple[DataInterface, _MockProvider],
) -> None:
    """get_scheduleがProviderに委譲される."""
    interface, mock_provider = interface_with_mock
    result = interface.get_schedule("2025-01-01", "2025-01-31")
    mock_provider.get_schedule.assert_called_once_with("2025-01-01", "2025-01-31")
    pd.testing.assert_frame_equal(result, pd.DataFrame({"col": [10]}))


# 準正常系
def test_invalid_provider_raises_error() -> None:
    """不正なprovider名でKeibaDataInterfaceErrorが発生する."""
    with pytest.raises(KeibaDataInterfaceError, match="不正なprovider名です"):
        DataInterface(provider="invalid")


def test_empty_provider_raises_error() -> None:
    """空文字列のprovider名でKeibaDataInterfaceErrorが発生する."""
    with pytest.raises(KeibaDataInterfaceError, match="不正なprovider名です"):
        DataInterface(provider="")
