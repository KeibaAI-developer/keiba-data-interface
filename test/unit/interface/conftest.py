"""DataInterfaceテスト用のfixture."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from keiba_data_interface.interface import DataInterface


class _MockProvider:
    """DataProvider Protocolを満たすモックProvider."""

    def __init__(self) -> None:
        """コンストラクタ."""
        self.get_race_basic_info = MagicMock(return_value=pd.DataFrame({"col": [1]}))
        self.get_entry = MagicMock(return_value=pd.DataFrame({"col": [2]}))
        self.get_win_show_odds = MagicMock(return_value=pd.DataFrame({"col": [3]}))
        self.get_result = MagicMock(return_value=pd.DataFrame({"col": [4]}))
        self.get_race_result_info = MagicMock(return_value=pd.DataFrame({"col": [5]}))
        self.get_payoff = MagicMock(return_value=pd.DataFrame({"col": [6]}))
        self.get_past_performances = MagicMock(return_value=pd.DataFrame({"col": [7]}))
        self.get_horse_master = MagicMock(return_value=pd.DataFrame({"col": [8]}))
        self.get_schedule = MagicMock(return_value=pd.DataFrame({"col": [9]}))


@pytest.fixture()
def mock_provider() -> _MockProvider:
    """MockProviderインスタンスを返すfixture."""
    return _MockProvider()


@pytest.fixture()
def interface_with_mock(mock_provider: _MockProvider) -> tuple[DataInterface, _MockProvider]:
    """MockProviderを使用するDataInterfaceとMockProviderのタプルを返すfixture."""
    with patch("keiba_data_interface.interface._create_provider", return_value=mock_provider):
        interface = DataInterface(provider="scraping")
    return interface, mock_provider
