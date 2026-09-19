"""MykeibaDBProvider.get_expected_win_show_odds関数のテスト."""

import pytest

from keiba_data_interface.exceptions import UnsupportedOperationError
from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider


# 準正常系
def test_raises_unsupported(provider: MykeibaDBProvider, race_code: str) -> None:
    """mykeibadbは予想オッズを持たないためUnsupportedOperationError."""
    with pytest.raises(UnsupportedOperationError):
        provider.get_expected_win_show_odds(race_code)
