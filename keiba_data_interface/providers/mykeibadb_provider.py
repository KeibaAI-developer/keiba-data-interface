"""MykeibaDBProvider: mykeibadb-pythonを使用したデータ取得Provider.

mykeibadb-pythonのRaceGetterを使用してJRA-VANデータを取得し、
統一スキーマに変換する。
"""

import pandas as pd
from mykeibadb import RaceGetter

from keiba_data_interface.providers.mykeibadb_converters import convert_entry, convert_race_info


class MykeibaDBProvider:
    """mykeibadb-pythonを使用したデータ取得Provider."""

    def get_race_info(self, race_code: str) -> pd.DataFrame:
        """レース基本情報を取得する.

        RaceGetter.get_race_shosai()でレース詳細を取得し、統一スキーマに変換する。

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: レース基本情報（1行、RACE_INFO_COLUMNSのカラム）
        """
        getter = RaceGetter()
        raw = getter.get_race_shosai(race_code=race_code, convert_codes=True)
        return convert_race_info(raw)

    def get_entry(self, race_code: str) -> pd.DataFrame:
        """出馬表を取得する.

        RaceGetter.get_umagoto_race_joho()で馬毎レース情報を取得し、
        統一スキーマに変換する。

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: 出馬表（出走頭数行、HORSE_RACE_INFO_COLUMNSのカラム）
        """
        getter = RaceGetter()
        raw = getter.get_umagoto_race_joho(race_code=race_code, convert_codes=True)
        return convert_entry(raw)

    def get_win_show_odds(self, race_code: str) -> pd.DataFrame:
        """単複オッズを取得する.

        Args:
            race_code (str): 16桁レースコード

        Raises:
            NotImplementedError: 未実装
        """
        raise NotImplementedError

    def get_result(self, race_code: str) -> pd.DataFrame:
        """レース結果（馬毎）を取得する.

        Args:
            race_code (str): 16桁レースコード

        Raises:
            NotImplementedError: 未実装
        """
        raise NotImplementedError

    def get_race_result_info(self, race_code: str) -> pd.DataFrame:
        """レース結果情報（ラップ・コーナー通過順）を取得する.

        Args:
            race_code (str): 16桁レースコード

        Raises:
            NotImplementedError: 未実装
        """
        raise NotImplementedError

    def get_payoff(self, race_code: str) -> pd.DataFrame:
        """払戻情報を取得する.

        Args:
            race_code (str): 16桁レースコード

        Raises:
            NotImplementedError: 未実装
        """
        raise NotImplementedError

    def get_past_performances(self, horse_id: str) -> pd.DataFrame:
        """過去成績（馬柱）を取得する.

        Args:
            horse_id (str): 馬ID

        Raises:
            NotImplementedError: 未実装
        """
        raise NotImplementedError

    def get_schedule(self, start_date: str, end_date: str) -> pd.DataFrame:
        """開催スケジュールを取得する.

        Args:
            start_date (str): 開始日（YYYY-MM-DD形式）
            end_date (str): 終了日（YYYY-MM-DD形式）

        Raises:
            NotImplementedError: 未実装
        """
        raise NotImplementedError
