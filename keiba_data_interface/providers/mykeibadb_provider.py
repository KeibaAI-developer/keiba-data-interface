"""MykeibaDBProvider: mykeibadb-pythonを使用したデータ取得Provider.

mykeibadb-pythonのRaceGetter/OddsGetterを使用してJRA-VANデータを取得し、
統一スキーマに変換する。
"""

from datetime import date

import pandas as pd
from mykeibadb import MasterGetter, OddsGetter, RaceGetter

from keiba_data_interface.providers.mykeibadb_converters import (
    convert_entry,
    convert_horse_master,
    convert_past_performances,
    convert_payoff,
    convert_race_basic_info,
    convert_race_result_info,
    convert_result,
    convert_schedule,
    convert_win_show_odds,
)


class MykeibaDBProvider:
    """mykeibadb-pythonを使用したデータ取得Provider.

    Attributes:
        _race_getter (RaceGetter): JRA-VANデータ取得用のRaceGetterインスタンス
        _odds_getter (OddsGetter): JRA-VANオッズ取得用のOddsGetterインスタンス
        _master_getter (MasterGetter): JRA-VANマスタ取得用のMasterGetterインスタンス
    """

    def __init__(self) -> None:
        """コンストラクタ."""
        self._race_getter = RaceGetter()
        self._odds_getter = OddsGetter()
        self._master_getter = MasterGetter()

    def get_race_basic_info(self, race_code: str) -> pd.DataFrame:
        """レース基本情報を取得する.

        RaceGetter.get_race_shosai()でレース詳細を取得し、統一スキーマに変換する。

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: レース基本情報（1行、RACE_INFO_COLUMNSのカラム）
        """
        raw = self._race_getter.get_race_shosai(race_code=race_code, convert_codes=False)
        return convert_race_basic_info(raw)

    def get_entry(self, race_code: str) -> pd.DataFrame:
        """出馬表を取得する.

        RaceGetter.get_umagoto_race_joho()で馬毎レース情報を取得し、
        統一スキーマに変換する。

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: 出馬表（出走頭数行、HORSE_RACE_INFO_COLUMNSのカラム, 馬番順）
        """
        raw = self._race_getter.get_umagoto_race_joho(race_code=race_code, convert_codes=False)
        df = convert_entry(raw)
        df = df.sort_values("馬番").reset_index(drop=True)
        return df

    def get_win_show_odds(self, race_code: str) -> pd.DataFrame:
        """単複オッズを取得する.

        OddsGetter.get_odds1_tansho()とget_odds1_fukusho()でオッズを取得し、
        マージして統一スキーマに変換する。

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: 単複オッズ（馬番数行、ODDS_COLUMNSのカラム, 馬番順）
        """
        raw_tansho = self._odds_getter.get_odds1_tansho(race_code=race_code, convert_codes=False)
        raw_fukusho = self._odds_getter.get_odds1_fukusho(race_code=race_code, convert_codes=False)
        df = convert_win_show_odds(raw_tansho, raw_fukusho)
        df = df.sort_values("馬番").reset_index(drop=True)
        return df

    def get_result(self, race_code: str) -> pd.DataFrame:
        """レース結果（馬毎）を取得する.

        RaceGetter.get_umagoto_race_joho()で馬毎レース情報を取得し、
        get_entry用の変換に加えて走破タイムの変換を行う。

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: レース結果（出走頭数行、HORSE_RACE_INFO_COLUMNSのカラム, 確定着順順）
        """
        raw = self._race_getter.get_umagoto_race_joho(race_code=race_code, convert_codes=False)
        df = convert_result(raw)
        df = df.sort_values("確定着順").reset_index(drop=True)
        return df

    def get_race_result_info(self, race_code: str) -> pd.DataFrame:
        """レース結果情報（ラップ・コーナー通過順）を取得する.

        RaceGetter.get_race_shosai()でレース詳細を取得し、
        ラップタイムとコーナー通過順を統一スキーマに変換する。

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: レース結果情報（1行、RACE_RESULT_INFO_COLUMNSのカラム）
        """
        raw = self._race_getter.get_race_shosai(race_code=race_code, convert_codes=False)
        return convert_race_result_info(raw)

    def get_payoff(self, race_code: str) -> pd.DataFrame:
        """払戻情報を取得する.

        RaceGetter.get_haraimodoshi()で払戻情報を取得し、統一スキーマに変換する。

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: 払戻情報（1行、PAYOFF_COLUMNSのカラム）
        """
        raw = self._race_getter.get_haraimodoshi(race_code=race_code, convert_codes=False)
        return convert_payoff(raw)

    def get_past_performances(self, horse_id: str) -> pd.DataFrame:
        """過去成績（馬柱）を取得する.

        RaceGetter.get_umagoto_race_joho()を馬ID（血統登録番号）指定で取得し、
        統一スキーマに変換する。

        Args:
            horse_id (str): 馬ID（血統登録番号）

        Returns:
            pd.DataFrame: 過去成績（出走回数行、HORSE_RACE_INFO_COLUMNSのカラム）
        """
        raw = self._race_getter.get_umagoto_race_joho(
            ketto_toroku_bango=horse_id, convert_codes=False
        )
        df = convert_past_performances(raw)
        df = df.sort_values("レースコード", ascending=False).reset_index(drop=True)
        return df

    def get_horse_master(self, horse_id: str) -> pd.DataFrame:
        """競走馬マスタを取得する.

        MasterGetter.get_kyosoba_master2()で競走馬マスタを取得し、
        統一スキーマに変換する。

        Args:
            horse_id (str): 馬ID（血統登録番号）

        Returns:
            pd.DataFrame: 競走馬マスタ情報（1行、HORSE_MASTER_COLUMNSのカラム）
        """
        raw = self._master_getter.get_kyosoba_master2(
            ketto_toroku_bango=horse_id, convert_codes=False
        )
        return convert_horse_master(raw)

    def get_schedule(self, start_date: str, end_date: str) -> pd.DataFrame:
        """開催スケジュールを取得する.

        RaceGetter.get_kaisai_schedule()で日付範囲の開催スケジュールを取得し、
        統一スキーマに変換する。

        Args:
            start_date (str): 開始日（YYYY-MM-DD形式）
            end_date (str): 終了日（YYYY-MM-DD形式）

        Returns:
            pd.DataFrame: 開催スケジュール（開催場数行、SCHEDULE_COLUMNSのカラム）
        """
        raw = self._race_getter.get_kaisai_schedule(
            start_date=date.fromisoformat(start_date),
            end_date=date.fromisoformat(end_date),
            convert_codes=False,
        )
        return convert_schedule(raw)
