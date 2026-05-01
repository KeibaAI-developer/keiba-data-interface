"""DataInterfaceクラスの実装.

利用者向けAPIのファサードクラスを提供する。
Provider名を指定することで、データソースを切り替えてデータを取得できる。
"""

import importlib
import logging

import pandas as pd

from keiba_data_interface.exceptions import KeibaDataInterfaceError
from keiba_data_interface.protocols import DataProvider

_PROVIDER_MAP: dict[str, str] = {
    "scraping": "keiba_data_interface.providers.scraping_provider.ScrapingProvider",
    "mykeibadb": "keiba_data_interface.providers.mykeibadb_provider.MykeibaDBProvider",
}


class DataInterface:
    """競馬データ統一インターフェース.

    データソースを選択し、統一されたインターフェースでデータを取得する。
    """

    def __init__(self, provider: str, logger: logging.Logger | None = None) -> None:
        """コンストラクタ.

        Args:
            provider: データソース名（'scraping' または 'mykeibadb'）
            logger: ロガーインスタンス

        Raises:
            KeibaDataInterfaceError: 不正なprovider名が指定された場合
        """
        self._logger = logger or logging.getLogger(__name__)
        provider_logger = self._logger.getChild(provider)
        self._provider: DataProvider = _create_provider(provider, provider_logger)
        self._logger.debug("DataInterfaceを初期化しました: provider=%s", provider)

    def get_race_basic_info(self, race_code: str) -> pd.DataFrame:
        """レース基本情報を取得する.

        Args:
            race_code: 16桁レースコード

        Returns:
            レース基本情報のDataFrame（1行）
        """
        result = self._provider.get_race_basic_info(race_code)
        return result

    def get_entry(self, race_code: str) -> pd.DataFrame:
        """出馬表を取得する.

        Args:
            race_code: 16桁レースコード

        Returns:
            出馬表のDataFrame（出走頭数行）
        """
        result = self._provider.get_entry(race_code)
        return result

    def get_win_show_odds(self, race_code: str) -> pd.DataFrame:
        """単複オッズを取得する.

        Args:
            race_code: 16桁レースコード

        Returns:
            単複オッズのDataFrame
        """
        result = self._provider.get_win_show_odds(race_code)
        return result

    def get_result(self, race_code: str) -> pd.DataFrame:
        """レース結果（馬毎）を取得する.

        Args:
            race_code: 16桁レースコード

        Returns:
            レース結果のDataFrame（出走頭数行）
        """
        result = self._provider.get_result(race_code)
        return result

    def get_race_result_info(self, race_code: str) -> pd.DataFrame:
        """レース結果情報（ラップ・コーナー通過順）を取得する.

        Args:
            race_code: 16桁レースコード

        Returns:
            レース結果情報のDataFrame（1行）
        """
        result = self._provider.get_race_result_info(race_code)
        return result

    def get_payoff(self, race_code: str) -> pd.DataFrame:
        """払戻情報を取得する.

        Args:
            race_code: 16桁レースコード

        Returns:
            払戻情報のDataFrame（1行）
        """
        result = self._provider.get_payoff(race_code)
        return result

    def get_past_performances(self, horse_id: str) -> pd.DataFrame:
        """過去成績（馬柱）を取得する.

        Args:
            horse_id: 馬ID（血統登録番号）

        Returns:
            過去成績のDataFrame
        """
        result = self._provider.get_past_performances(horse_id)
        return result

    def get_horse_master(self, horse_id: str) -> pd.DataFrame:
        """競走馬情報を取得する.

        Args:
            horse_id: 馬ID（血統登録番号）

        Returns:
            競走馬情報のDataFrame（1行）
        """
        result = self._provider.get_horse_master(horse_id)
        return result

    def get_schedule(self, start_date: str, end_date: str) -> pd.DataFrame:
        """開催スケジュールを取得する.

        Args:
            start_date: 開始日（YYYY-MM-DD形式）
            end_date: 終了日（YYYY-MM-DD形式）

        Returns:
            開催スケジュールのDataFrame
        """
        result = self._provider.get_schedule(start_date, end_date)
        return result


def _create_provider(provider: str, logger: logging.Logger) -> DataProvider:
    """Provider名に対応するProviderインスタンスを生成する.

    Args:
        provider: データソース名
        logger: ロガーインスタンス

    Returns:
        DataProviderインスタンス

    Raises:
        KeibaDataInterfaceError: 不正なprovider名が指定された場合
    """
    if provider not in _PROVIDER_MAP:
        valid = ", ".join(_PROVIDER_MAP)
        logger.error("不正なprovider名です: '%s' （有効な値: %s）", provider, valid)
        raise KeibaDataInterfaceError(f"不正なprovider名です: '{provider}' （有効な値: {valid}）")
    module_path, class_name = _PROVIDER_MAP[provider].rsplit(".", 1)
    module = importlib.import_module(module_path)
    provider_class = getattr(module, class_name)
    return provider_class(logger=logger)
