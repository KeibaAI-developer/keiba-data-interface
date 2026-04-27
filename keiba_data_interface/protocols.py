"""DataProvider Protocolの定義.

データソースの抽象インターフェースを定義する。
ScrapingProviderおよびMykeibaDBProviderはこのProtocolに準拠する。
"""

from typing import Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class DataProvider(Protocol):
    """データソースの抽象インターフェース.

    各データソース（scraping, mykeibadb）はこのProtocolを実装する。
    """

    def get_race_info(self, race_code: str) -> pd.DataFrame:
        """レース基本情報を取得する.

        Args:
            race_code: 16桁レースコード
        """
        ...

    def get_entry(self, race_code: str) -> pd.DataFrame:
        """出馬表を取得する.

        Args:
            race_code: 16桁レースコード
        """
        ...

    def get_win_show_odds(self, race_code: str) -> pd.DataFrame:
        """単複オッズを取得する.

        Args:
            race_code: 16桁レースコード
        """
        ...

    def get_result(self, race_code: str) -> pd.DataFrame:
        """レース結果（馬毎）を取得する.

        Args:
            race_code: 16桁レースコード
        """
        ...

    def get_race_result_info(self, race_code: str) -> pd.DataFrame:
        """レース結果情報（ラップ・コーナー通過順）を取得する.

        Args:
            race_code: 16桁レースコード
        """
        ...

    def get_payoff(self, race_code: str) -> pd.DataFrame:
        """払戻情報を取得する.

        Args:
            race_code: 16桁レースコード
        """
        ...

    def get_past_performances(self, horse_id: str) -> pd.DataFrame:
        """過去成績（馬柱）を取得する.

        Args:
            horse_id: 馬ID
        """
        ...

    def get_horse_info(self, horse_id: str) -> pd.DataFrame:
        """競走馬情報を取得する.

        Args:
            horse_id: 馬ID
        """
        ...

    def get_schedule(self, start_date: str, end_date: str) -> pd.DataFrame:
        """開催スケジュールを取得する.

        Args:
            start_date: 開始日（YYYY-MM-DD形式）
            end_date: 終了日（YYYY-MM-DD形式）
        """
        ...
