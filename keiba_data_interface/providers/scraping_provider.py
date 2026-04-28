"""ScrapingProvider: keiba-scrapingを使用したデータ取得Provider."""

import asyncio
import logging
from collections.abc import Coroutine
from datetime import date, timedelta
from typing import TypeVar

import pandas as pd
from scraping import (
    EntryPageScraper,
    HorsePageScraper,
    RaceScheduleScraper,
    ResultPageScraper,
    scrape_odds_from_jra,
    scrape_odds_from_netkeiba,
)
from scraping.exceptions import PageNotFoundError

from keiba_data_interface.providers.scraping_converters import (
    build_prize_map,
    convert_entry,
    convert_horse_master,
    convert_odds,
    convert_past_performances,
    convert_payoff,
    convert_race_basic_info,
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

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """コンストラクタ.

        Args:
            logger: ロガーインスタンス
        """
        self._logger = logger or logging.getLogger(__name__)

    def get_race_basic_info(self, race_code: str) -> pd.DataFrame:
        """レース基本情報を取得する.

        16桁レースコードを12桁に変換してEntryPageScraperに渡し、
        scraping出力を統一スキーマに変換する。

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: レース基本情報（1行、RACE_INFO_COLUMNSのカラム）
        """
        race_id = race_code_to_race_id(race_code)
        self._logger.debug("EntryPageScraperでレース情報をスクレイピング: race_id=%s", race_id)
        scraper = EntryPageScraper(race_id, logger=self._logger)
        raw = scraper.get_race_info()
        result = convert_race_basic_info(raw, race_code)
        self._logger.info("レース基本情報の取得が完了: race_code=%s", race_code)
        return result

    def get_entry(self, race_code: str) -> pd.DataFrame:
        """出馬表を取得する.

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: 出馬表（出走頭数行、HORSE_RACE_INFO_COLUMNSのカラム）
        """
        race_id = race_code_to_race_id(race_code)
        self._logger.debug("EntryPageScraperで出馬表をスクレイピング: race_id=%s", race_id)
        scraper = EntryPageScraper(race_id, logger=self._logger)
        raw = scraper.get_entry()
        result = convert_entry(raw, race_code)
        self._logger.info("出馬表の取得が完了: race_code=%s", race_code)
        return result

    def get_win_show_odds(self, race_code: str) -> pd.DataFrame:
        """単複オッズを取得する.

        JRA公式サイトから取得を試み、失敗した場合はnetkeibaから取得する。

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: 単複オッズ（出走頭数行、ODDS_COLUMNSのカラム, 馬番順）
        """
        race_id = race_code_to_race_id(race_code)
        # JRAにオッズページがない場合（レース翌日以降など）はnetkeibaにフォールバックする
        try:
            self._logger.debug("JRAから単複オッズをスクレイピング: race_id=%s", race_id)
            raw = _run_async(scrape_odds_from_jra(race_id, logger=self._logger))
        except PageNotFoundError:
            self._logger.debug("JRAでオッズページが見つからないためnetkeibaから取得: race_id=%s", race_id)
            raw = scrape_odds_from_netkeiba(race_id, logger=self._logger)
        df = convert_odds(raw, race_code)
        df = df.sort_values("馬番").reset_index(drop=True)
        self._logger.info("単複オッズの取得が完了: race_code=%s", race_code)
        return df

    def get_result(self, race_code: str) -> pd.DataFrame:
        """レース結果（馬毎）を取得する.

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: レース結果（出走頭数行、HORSE_RACE_INFO_COLUMNSのカラム）
        """
        race_id = race_code_to_race_id(race_code)

        # 賞金情報を取得して着順→獲得本賞金マッピングを構築
        self._logger.debug("EntryPageScraperで賞金情報をスクレイピング: race_id=%s", race_id)
        scraper_entry = EntryPageScraper(race_id, logger=self._logger)
        raw_race_info = scraper_entry.get_race_info()
        prize_map = build_prize_map(raw_race_info)

        self._logger.debug("ResultPageScraperでレース結果をスクレイピング: race_id=%s", race_id)
        scraper = ResultPageScraper(race_id, logger=self._logger)
        raw = scraper.get_result()
        result = convert_result(raw, race_code, prize_map)
        self._logger.info("レース結果の取得が完了: race_code=%s", race_code)
        return result

    def get_race_result_info(self, race_code: str) -> pd.DataFrame:
        """レース結果情報（ラップ・コーナー通過順）を取得する.

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: レース結果情報（1行、RACE_RESULT_INFO_COLUMNSのカラム）
        """
        race_id = race_code_to_race_id(race_code)
        self._logger.debug("ResultPageScraperでラップ・コーナー情報をスクレイピング: race_id=%s", race_id)
        scraper = ResultPageScraper(race_id, logger=self._logger)
        raw_lap = scraper.get_lap_time()
        raw_corner = scraper.get_corner()
        result = convert_race_result_info(raw_lap, raw_corner, race_code)
        self._logger.info("レース結果情報の取得が完了: race_code=%s", race_code)
        return result

    def get_payoff(self, race_code: str) -> pd.DataFrame:
        """払戻情報を取得する.

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: 払戻情報（1行、PAYOFF_COLUMNSのカラム）
        """
        race_id = race_code_to_race_id(race_code)
        self._logger.debug("ResultPageScraperで払戻情報をスクレイピング: race_id=%s", race_id)
        scraper = ResultPageScraper(race_id, logger=self._logger)
        result = convert_payoff(scraper, race_code)
        self._logger.info("払戻情報の取得が完了: race_code=%s", race_code)
        return result

    def get_past_performances(self, horse_id: str) -> pd.DataFrame:
        """過去成績（馬柱）を取得する.

        Args:
            horse_id (str): 馬ID（血統登録番号）

        Returns:
            pd.DataFrame: 過去成績（出走回数行、HORSE_RACE_INFO_COLUMNSのカラム）
        """
        self._logger.debug("HorsePageScraperで過去成績をスクレイピング: horse_id=%s", horse_id)
        scraper = HorsePageScraper(horse_id, logger=self._logger)
        raw = scraper.get_past_performances()
        horse_basic_info = scraper.get_horse_basic_info()
        result = convert_past_performances(raw, horse_id, horse_basic_info)
        self._logger.info("過去成績の取得が完了: horse_id=%s", horse_id)
        return result

    def get_horse_master(self, horse_id: str) -> pd.DataFrame:
        """競走馬マスタを取得する.

        Args:
            horse_id (str): 馬ID（血統登録番号）

        Returns:
            pd.DataFrame: 競走馬マスタ情報（1行、HORSE_MASTER_COLUMNSのカラム）
        """
        self._logger.debug("HorsePageScraperで競走馬情報をスクレイピング: horse_id=%s", horse_id)
        scraper = HorsePageScraper(horse_id, logger=self._logger)
        past_perf = scraper.get_past_performances()
        horse_basic_info = scraper.get_horse_basic_info()
        result = convert_horse_master(past_perf, horse_id, horse_basic_info)
        self._logger.info("競走馬情報の取得が完了: horse_id=%s", horse_id)
        return result

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
            self._logger.debug(
                "RaceScheduleScraperで開催スケジュールをスクレイピング: %s", current.isoformat()
            )
            scraper = RaceScheduleScraper(
                current.year, current.month, current.day, logger=self._logger
            )
            raw = scraper.get_race_schedule()
            if len(raw) > 0:
                converted = convert_schedule(raw)
                all_rows.append(converted)
            current += timedelta(days=1)
        if not all_rows:
            self._logger.info(
                "開催スケジュールの取得が完了: start_date=%s, end_date=%s", start_date, end_date
            )
            return apply_types(ensure_columns(pd.DataFrame(), SCHEDULE_COLUMNS), SCHEDULE_TYPES)
        result = pd.concat(all_rows, ignore_index=True)
        self._logger.info(
            "開催スケジュールの取得が完了: start_date=%s, end_date=%s", start_date, end_date
        )
        return result


_T = TypeVar("_T")


def _run_async(coro: Coroutine[object, object, _T]) -> _T:
    """コルーチンを同期的に実行する.

    既存のイベントループが動作中の場合（Jupyter等）は新しいスレッドで
    イベントループを作成して実行し、そうでない場合は asyncio.run() を使用する。

    Args:
        coro: 実行するコルーチン

    Returns:
        コルーチンの実行結果
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)
