"""calc_course_days単体テスト用の共通定義

開催日データから開催スケジュールとレース基本情報の応答を生成するMockProviderを提供する
"""

from dataclasses import dataclass
from datetime import date

import pandas as pd

from keiba_data_interface.schema.columns import RACE_BASIC_INFO_COLUMNS

# 競馬場コード（東京）
KEIBAJO_CODE = "05"


@dataclass
class RaceDay:
    """テスト用の開催日データ

    Attributes:
        race_date (date): 開催日
        kai (int): 開催回
        nichime (int): 開催日目
        races (list[tuple[str, str | None]]): レース番号順の（芝ダ, コース区分）のリスト
        keibajo_code (str): 競馬場コード
    """

    race_date: date
    kai: int
    nichime: int
    races: list[tuple[str, str | None]]
    keibajo_code: str = KEIBAJO_CODE


class MockProvider:
    """開催日データから応答を生成するテスト用Provider

    Attributes:
        race_days (dict[date, RaceDay]): 開催日ごとのレース構成
    """

    def __init__(self, race_days: list[RaceDay]) -> None:
        self.race_days = {day.race_date: day for day in race_days}

    def get_schedule(self, start_date: str, end_date: str) -> pd.DataFrame:
        """期間内の開催日から開催スケジュールを生成する

        Args:
            start_date (str): 開始日（YYYY-MM-DD形式）
            end_date (str): 終了日（YYYY-MM-DD形式）

        Returns:
            pd.DataFrame: 開催スケジュールのDataFrame
        """
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        rows: list[list[object]] = []
        for day in self.race_days.values():
            if start <= day.race_date <= end:
                year = f"{day.race_date.year:04d}"
                monthday = f"{day.race_date.month:02d}{day.race_date.day:02d}"
                rows.append([year, monthday, day.keibajo_code, day.kai, day.nichime])
        columns = ["開催年", "開催月日", "競馬場コード", "開催回", "開催日目"]
        return pd.DataFrame(rows, columns=columns)

    def get_race_basic_info(self, race_code: str) -> pd.DataFrame:
        """レースコードに対応するレース基本情報を生成する

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: 芝ダ・コース区分を含むレース基本情報のDataFrame（1行）

        Raises:
            LookupError: 開催日データに存在しないレースコードの場合
        """
        race_date = date(int(race_code[:4]), int(race_code[4:6]), int(race_code[6:8]))
        race_num = int(race_code[14:16])
        day = self.race_days.get(race_date)
        if day is None or race_num > len(day.races):
            raise LookupError(f"開催日データに存在しないレースコードです: {race_code}")
        shiba_da, course_kubun = day.races[race_num - 1]
        kubun_value = course_kubun if course_kubun is not None else pd.NA
        return pd.DataFrame({"芝ダ": [shiba_da], "コース区分": [kubun_value]})

    def get_entry(self, race_code: str) -> pd.DataFrame:
        """テストでは使用しない

        Raises:
            NotImplementedError: 常に発生する
        """
        raise NotImplementedError

    def get_win_show_odds(self, race_code: str) -> pd.DataFrame:
        """テストでは使用しない

        Raises:
            NotImplementedError: 常に発生する
        """
        raise NotImplementedError

    def get_result(self, race_code: str) -> pd.DataFrame:
        """テストでは使用しない

        Raises:
            NotImplementedError: 常に発生する
        """
        raise NotImplementedError

    def get_race_result_info(self, race_code: str) -> pd.DataFrame:
        """テストでは使用しない

        Raises:
            NotImplementedError: 常に発生する
        """
        raise NotImplementedError

    def get_payoff(self, race_code: str) -> pd.DataFrame:
        """テストでは使用しない

        Raises:
            NotImplementedError: 常に発生する
        """
        raise NotImplementedError

    def get_past_performances(self, horse_id: str) -> pd.DataFrame:
        """テストでは使用しない

        Raises:
            NotImplementedError: 常に発生する
        """
        raise NotImplementedError

    def get_horse_master(self, horse_id: str) -> pd.DataFrame:
        """テストでは使用しない

        Raises:
            NotImplementedError: 常に発生する
        """
        raise NotImplementedError

    def get_chakudosu(self, race_code: str) -> pd.DataFrame:
        """テストでは使用しない

        Raises:
            NotImplementedError: 常に発生する
        """
        raise NotImplementedError


def build_race_basic_info(
    race_date: date,
    shiba_da: str,
    course_kubun: str | None,
    keibajo_code: str = KEIBAJO_CODE,
) -> pd.DataFrame:
    """対象レースのレース基本情報DataFrame（74カラム）を生成する

    Args:
        race_date (date): 開催日
        shiba_da (str): 芝ダ（"芝", "ダ"）
        course_kubun (str | None): コース区分（A〜E）。NoneはNaN扱い
        keibajo_code (str): 競馬場コード

    Returns:
        pd.DataFrame: レース基本情報のDataFrame（1行）
    """
    values: list[object] = [pd.NA] * len(RACE_BASIC_INFO_COLUMNS)
    df = pd.DataFrame([values], columns=RACE_BASIC_INFO_COLUMNS)
    monthday = f"{race_date.month:02d}{race_date.day:02d}"
    df["レースコード"] = f"{race_date.year:04d}{monthday}{keibajo_code}020111"
    df["開催年"] = f"{race_date.year:04d}"
    df["開催月日"] = monthday
    df["競馬場コード"] = keibajo_code
    df["芝ダ"] = shiba_da
    df["コース区分"] = course_kubun if course_kubun is not None else pd.NA
    return df


def turf_day_races(course_kubun: str) -> list[tuple[str, str | None]]:
    """ダート1レース後に芝レースが続く開催日のレース構成を生成する

    Args:
        course_kubun (str): 芝レースのコース区分

    Returns:
        list[tuple[str, str | None]]: レース番号順の（芝ダ, コース区分）のリスト
    """
    return [("ダ", None), ("芝", course_kubun)]


def dirt_only_day_races() -> list[tuple[str, str | None]]:
    """芝レースが存在しない開催日のレース構成（12レース全てダート）を生成する

    Returns:
        list[tuple[str, str | None]]: レース番号順の（芝ダ, コース区分）のリスト
    """
    return [("ダ", None)] * 12
