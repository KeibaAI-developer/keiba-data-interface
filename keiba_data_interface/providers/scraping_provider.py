"""ScrapingProvider: keiba-scrapingを使用したデータ取得Provider."""

import asyncio
import inspect
from datetime import date, timedelta
from typing import cast

import pandas as pd
from scraping import (
    EntryPageScraper,
    PastPerformancesScraper,
    RaceScheduleScraper,
    ResultPageScraper,
    scrape_odds_from_jra,
)

from keiba_data_interface.providers.scraping_converters import (
    build_prize_map,
    convert_entry,
    convert_odds,
    convert_past_performances,
    convert_payoff,
    convert_race_info,
    convert_race_result_info,
    convert_result,
    convert_schedule,
)
from keiba_data_interface.schema.columns import SCHEDULE_COLUMNS
from keiba_data_interface.schema.types import SCHEDULE_TYPES
from keiba_data_interface.utils.dataframe import apply_types, ensure_columns
from keiba_data_interface.utils.race_code import race_code_to_race_id


class ScrapingProvider:
    """keiba-scrapingを使用したデータ取得Provider."""

    def get_race_info(self, race_code: str) -> pd.DataFrame:
        """レース基本情報を取得する.

        16桁レースコードを12桁に変換してEntryPageScraperに渡し、
        scraping出力を統一スキーマに変換する。

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: レース基本情報（1行、RACE_INFO_COLUMNSのカラム）
        """
        race_id = race_code_to_race_id(race_code)
        scraper = EntryPageScraper(race_id)
        raw = scraper.get_race_info()
        return convert_race_info(raw, race_code)

    def get_entry(self, race_code: str) -> pd.DataFrame:
        """出馬表を取得する.

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: 出馬表（出走頭数行、HORSE_RACE_INFO_COLUMNSのカラム）
        """
        race_id = race_code_to_race_id(race_code)
        scraper = EntryPageScraper(race_id)
        raw = scraper.get_entry()
        return convert_entry(raw, race_code)

    def get_win_show_odds(self, race_code: str) -> pd.DataFrame:
        """単複オッズを取得する.

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: 単複オッズ（出走頭数行、ODDS_COLUMNSのカラム）
        """
        race_id = race_code_to_race_id(race_code)
        result = scrape_odds_from_jra(race_id)
        if inspect.iscoroutine(result):
            raw: pd.DataFrame = asyncio.run(result)
        else:
            raw = cast(pd.DataFrame, result)
        return convert_odds(raw, race_code)

    def get_result(self, race_code: str) -> pd.DataFrame:
        """レース結果（馬毎）を取得する.

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: レース結果（出走頭数行、HORSE_RACE_INFO_COLUMNSのカラム）
        """
        race_id = race_code_to_race_id(race_code)

        # 賞金情報を取得して着順→獲得本賞金マッピングを構築
        scraper_entry = EntryPageScraper(race_id)
        raw_race_info = scraper_entry.get_race_info()
        prize_map = build_prize_map(raw_race_info)

        scraper = ResultPageScraper(race_id)
        raw = scraper.get_result()
        return convert_result(raw, race_code, prize_map)

    def get_race_result_info(self, race_code: str) -> pd.DataFrame:
        """レース結果情報（ラップ・コーナー通過順）を取得する.

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: レース結果情報（1行、RACE_RESULT_INFO_COLUMNSのカラム）
        """
        race_id = race_code_to_race_id(race_code)
        scraper = ResultPageScraper(race_id)
        raw_lap = scraper.get_lap_time()
        raw_corner = scraper.get_corner()
        return convert_race_result_info(raw_lap, raw_corner, race_code)

    def get_payoff(self, race_code: str) -> pd.DataFrame:
        """払戻情報を取得する.

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: 払戻情報（1行、PAYOFF_COLUMNSのカラム）
        """
        race_id = race_code_to_race_id(race_code)
        scraper = ResultPageScraper(race_id)
        return convert_payoff(scraper, race_code)

    def get_past_performances(self, horse_id: str) -> pd.DataFrame:
        """過去成績（馬柱）を取得する.

        Args:
            horse_id (str): 馬ID（血統登録番号）

        Returns:
            pd.DataFrame: 過去成績（出走回数行、HORSE_RACE_INFO_COLUMNSのカラム）
        """
        scraper = PastPerformancesScraper(horse_id)
        raw = scraper.get_past_performances()
        return convert_past_performances(raw, horse_id)

    def get_schedule(self, start_date: str, end_date: str) -> pd.DataFrame:
        """開催スケジュールを取得する.

        Args:
            start_date (str): 開始日（YYYY-MM-DD形式）
            end_date (str): 終了日（YYYY-MM-DD形式）

        Returns:
            pd.DataFrame: 開催スケジュール（開催場数行、SCHEDULE_COLUMNSのカラム）
        """
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        all_rows: list[pd.DataFrame] = []
        current = start
        while current <= end:
            scraper = RaceScheduleScraper(current.year, current.month, current.day)
            raw = scraper.get_race_schedule()
            if len(raw) > 0:
                converted = convert_schedule(raw)
                all_rows.append(converted)
            current += timedelta(days=1)
        if not all_rows:
            return apply_types(ensure_columns(pd.DataFrame(), SCHEDULE_COLUMNS), SCHEDULE_TYPES)
        result = pd.concat(all_rows, ignore_index=True)
        return result
