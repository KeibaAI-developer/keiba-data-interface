"""DataProvider Protocolのテスト."""

from unittest.mock import patch

import pandas as pd

from keiba_data_interface.protocols import DataProvider
from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.providers.scraping_provider import ScrapingProvider


# 正常系
def test_full_provider_satisfies_protocol() -> None:
    """全メソッドを実装したクラスはDataProviderと判定される."""
    provider = _FullProvider()
    assert isinstance(provider, DataProvider)


def test_scraping_provider_satisfies_protocol() -> None:
    """ScrapingProviderがDataProviderと判定される."""
    provider = ScrapingProvider()
    assert isinstance(provider, DataProvider)


def test_mykeibadb_provider_satisfies_protocol() -> None:
    """MykeibaDBProviderがDataProviderと判定される."""
    with (
        patch("keiba_data_interface.providers.mykeibadb_provider.RaceGetter"),
        patch("keiba_data_interface.providers.mykeibadb_provider.OddsGetter"),
        patch("keiba_data_interface.providers.mykeibadb_provider.MasterGetter"),
    ):
        provider = MykeibaDBProvider()
        assert isinstance(provider, DataProvider)


def test_incomplete_provider_does_not_satisfy_protocol() -> None:
    """一部メソッドが欠けたクラスはDataProviderと判定されない."""
    provider = _IncompleteProvider()
    assert not isinstance(provider, DataProvider)


class _FullProvider:
    """全メソッドを実装したProvider."""

    def get_race_info(self, race_code: str) -> pd.DataFrame:
        """レース基本情報を取得する."""
        return pd.DataFrame()

    def get_entry(self, race_code: str) -> pd.DataFrame:
        """出馬表を取得する."""
        return pd.DataFrame()

    def get_win_show_odds(self, race_code: str) -> pd.DataFrame:
        """単複オッズを取得する."""
        return pd.DataFrame()

    def get_result(self, race_code: str) -> pd.DataFrame:
        """レース結果を取得する."""
        return pd.DataFrame()

    def get_race_result_info(self, race_code: str) -> pd.DataFrame:
        """レース結果情報を取得する."""
        return pd.DataFrame()

    def get_payoff(self, race_code: str) -> pd.DataFrame:
        """払戻情報を取得する."""
        return pd.DataFrame()

    def get_past_performances(self, horse_id: str) -> pd.DataFrame:
        """過去成績を取得する."""
        return pd.DataFrame()

    def get_horse_info(self, horse_id: str) -> pd.DataFrame:
        """競走馬情報を取得する."""
        return pd.DataFrame()

    def get_schedule(self, start_date: str, end_date: str) -> pd.DataFrame:
        """開催スケジュールを取得する."""
        return pd.DataFrame()


class _IncompleteProvider:
    """一部メソッドが欠けたProvider."""

    def get_race_info(self, race_code: str) -> pd.DataFrame:
        """レース基本情報を取得する."""
        return pd.DataFrame()
