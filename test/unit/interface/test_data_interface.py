"""DataInterfaceクラスのテスト."""

from unittest.mock import patch

import pandas as pd
import pytest

from keiba_data_interface.exceptions import KeibaDataInterfaceError
from keiba_data_interface.interface import DataInterface
from keiba_data_interface.protocols import DataProvider
from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.providers.scraping_provider import ScrapingProvider

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
    ):
        interface = DataInterface(provider="mykeibadb")
        assert isinstance(interface._provider, MykeibaDBProvider)


def test_get_race_info_delegates(
    interface_with_mock: tuple[DataInterface, _MockProvider],
) -> None:
    """get_race_infoがProviderに委譲される."""
    interface, mock_provider = interface_with_mock
    result = interface.get_race_info("2025050206021211")
    mock_provider.get_race_info.assert_called_once_with("2025050206021211")
    pd.testing.assert_frame_equal(result, pd.DataFrame({"col": [1]}))


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


def test_get_horse_info_delegates(
    interface_with_mock: tuple[DataInterface, _MockProvider],
) -> None:
    """get_horse_infoがProviderに委譲される."""
    interface, mock_provider = interface_with_mock
    result = interface.get_horse_info("2022105081")
    mock_provider.get_horse_info.assert_called_once_with("2022105081")
    pd.testing.assert_frame_equal(result, pd.DataFrame({"col": [8]}))


def test_get_schedule_delegates(
    interface_with_mock: tuple[DataInterface, _MockProvider],
) -> None:
    """get_scheduleがProviderに委譲される."""
    interface, mock_provider = interface_with_mock
    result = interface.get_schedule("2025-01-01", "2025-01-31")
    mock_provider.get_schedule.assert_called_once_with("2025-01-01", "2025-01-31")
    pd.testing.assert_frame_equal(result, pd.DataFrame({"col": [9]}))


# 準正常系
def test_invalid_provider_raises_error() -> None:
    """不正なprovider名でKeibaDataInterfaceErrorが発生する."""
    with pytest.raises(KeibaDataInterfaceError, match="不正なprovider名です"):
        DataInterface(provider="invalid")


def test_empty_provider_raises_error() -> None:
    """空文字列のprovider名でKeibaDataInterfaceErrorが発生する."""
    with pytest.raises(KeibaDataInterfaceError, match="不正なprovider名です"):
        DataInterface(provider="")
