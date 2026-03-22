"""ScrapingProvider: keiba-scrapingを使用したデータ取得Provider."""

import asyncio
import inspect
import re
from datetime import date, timedelta
from typing import Any

import pandas as pd

from keiba_data_interface.schema.columns import (
    HORSE_RACE_INFO_COLUMNS,
    ODDS_COLUMNS,
    PAYOFF_COLUMNS,
    RACE_INFO_COLUMNS,
    RACE_RESULT_INFO_COLUMNS,
    SCHEDULE_COLUMNS,
)
from keiba_data_interface.schema.types import (
    HORSE_RACE_INFO_TYPES,
    ODDS_TYPES,
    PAYOFF_TYPES,
    RACE_INFO_TYPES,
    RACE_RESULT_INFO_TYPES,
    SCHEDULE_TYPES,
)
from keiba_data_interface.utils.converters import convert_manyen_to_hyakuyen, split_zogen
from keiba_data_interface.utils.dataframe import apply_types, ensure_columns
from keiba_data_interface.utils.race_code import (
    extract_race_code_parts,
    keibajo_code_to_name,
    race_code_to_race_id,
)

# 異常区分変換マッピング（scraping出力 → 統一スキーマ）
_IJO_KUBUN_MAP: dict[str, str] = {
    "出走": "",
    "取消": "出走取消",
    "除外": "競走除外",
    "中止": "競走中止",
    "失格": "失格",
}


class ScrapingProvider:
    """keiba-scrapingを使用したデータ取得Provider."""

    def __init__(
        self,
        scraper_class: type[Any] | None = None,
        result_scraper_class: type[Any] | None = None,
        odds_func: Any | None = None,
        past_performances_scraper_class: type[Any] | None = None,
        race_schedule_scraper_class: type[Any] | None = None,
    ) -> None:
        """ScrapingProviderを初期化する.

        Args:
            scraper_class: EntryPageScraperクラス。Noneの場合はデフォルトを使用。
            result_scraper_class: ResultPageScraperクラス。Noneの場合はデフォルトを使用。
            odds_func: scrape_odds_from_jra関数。Noneの場合はデフォルトを使用。
            past_performances_scraper_class: PastPerformancesScraperクラス。
                Noneの場合はデフォルトを使用。
            race_schedule_scraper_class: RaceScheduleScraperクラス。
                Noneの場合はデフォルトを使用。
        """
        if scraper_class is None:
            from scraping import EntryPageScraper

            scraper_class = EntryPageScraper
        self._scraper_class: type[Any] = scraper_class

        if result_scraper_class is None:
            from scraping import ResultPageScraper

            result_scraper_class = ResultPageScraper
        self._result_scraper_class: type[Any] = result_scraper_class

        if odds_func is None:
            from scraping import scrape_odds_from_jra

            odds_func = scrape_odds_from_jra
        self._odds_func: Any = odds_func

        if past_performances_scraper_class is None:
            from scraping import PastPerformancesScraper

            past_performances_scraper_class = PastPerformancesScraper
        self._past_performances_scraper_class: type[Any] = past_performances_scraper_class

        if race_schedule_scraper_class is None:
            from scraping import RaceScheduleScraper

            race_schedule_scraper_class = RaceScheduleScraper
        self._race_schedule_scraper_class: type[Any] = race_schedule_scraper_class

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
        scraper = self._scraper_class(race_id)
        raw = scraper.get_race_info()
        return self._convert_race_info(raw, race_code)

    def get_entry(self, race_code: str) -> pd.DataFrame:
        """出馬表を取得する.

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: 出馬表（出走頭数行、HORSE_RACE_INFO_COLUMNSのカラム）
        """
        race_id = race_code_to_race_id(race_code)
        scraper = self._scraper_class(race_id)
        raw = scraper.get_entry()
        return self._convert_entry(raw, race_code)

    def get_win_show_odds(self, race_code: str) -> pd.DataFrame:
        """単複オッズを取得する.

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: 単複オッズ（出走頭数行、ODDS_COLUMNSのカラム）
        """
        race_id = race_code_to_race_id(race_code)
        result = self._odds_func(race_id)
        if inspect.iscoroutine(result):
            raw: pd.DataFrame = asyncio.run(result)
        else:
            raw = result
        return self._convert_odds(raw, race_code)

    def get_result(self, race_code: str) -> pd.DataFrame:
        """レース結果（馬毎）を取得する.

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: レース結果（出走頭数行、HORSE_RACE_INFO_COLUMNSのカラム）
        """
        race_id = race_code_to_race_id(race_code)

        # 賞金情報を取得して着順→獲得本賞金マッピングを構築
        scraper_entry = self._scraper_class(race_id)
        raw_race_info = scraper_entry.get_race_info()
        prize_map = self._build_prize_map(raw_race_info)

        scraper = self._result_scraper_class(race_id)
        raw = scraper.get_result()
        return self._convert_result(raw, race_code, prize_map)

    def get_race_result_info(self, race_code: str) -> pd.DataFrame:
        """レース結果情報（ラップ・コーナー通過順）を取得する.

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: レース結果情報（1行、RACE_RESULT_INFO_COLUMNSのカラム）
        """
        race_id = race_code_to_race_id(race_code)
        scraper = self._result_scraper_class(race_id)
        raw_lap = scraper.get_lap_time()
        raw_corner = scraper.get_corner()
        return self._convert_race_result_info(raw_lap, raw_corner, race_code)

    def get_payoff(self, race_code: str) -> pd.DataFrame:
        """払戻情報を取得する.

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: 払戻情報（1行、PAYOFF_COLUMNSのカラム）
        """
        race_id = race_code_to_race_id(race_code)
        scraper = self._result_scraper_class(race_id)
        return self._convert_payoff(scraper, race_code)

    def get_past_performances(self, horse_id: str) -> pd.DataFrame:
        """過去成績（馬柱）を取得する.

        Args:
            horse_id (str): 馬ID（血統登録番号）

        Returns:
            pd.DataFrame: 過去成績（出走回数行、HORSE_RACE_INFO_COLUMNSのカラム）
        """
        scraper = self._past_performances_scraper_class(horse_id)
        raw = scraper.get_past_performances()
        return self._convert_past_performances(raw, horse_id)

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
            scraper = self._race_schedule_scraper_class(current.year, current.month, current.day)
            raw = scraper.get_race_schedule()
            if len(raw) > 0:
                converted = self._convert_schedule(raw)
                all_rows.append(converted)
            current += timedelta(days=1)
        if not all_rows:
            return apply_types(ensure_columns(pd.DataFrame(), SCHEDULE_COLUMNS), SCHEDULE_TYPES)
        result = pd.concat(all_rows, ignore_index=True)
        return result

    def _convert_race_info(self, raw: pd.DataFrame, race_code: str) -> pd.DataFrame:
        """scraping出力を統一スキーマに変換する.

        Args:
            raw (pd.DataFrame): EntryPageScraper.get_race_info()の出力
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: 統一スキーマに変換されたDataFrame

        Raises:
            ValueError: rawが0行または2行以上の場合
        """
        parts = extract_race_code_parts(race_code)

        if len(raw) == 0:
            raise ValueError(
                f"EntryPageScraper.get_race_info() が空のDataFrameを返しました。"
                f"race_code={race_code!r}"
            )
        if len(raw) > 1:
            raise ValueError(
                f"EntryPageScraper.get_race_info() は1行のDataFrameを返す必要がありますが、"
                f"{len(raw)}行返しました。race_code={race_code!r}"
            )

        row = raw.iloc[0]

        converted: dict[str, object] = {}

        # レースコード: 引数の16桁をそのまま使用
        converted["レースコード"] = race_code

        # 日付 → 開催年 + 開催月日（race_codeから導出してキー整合性を保証）
        converted["開催年"] = parts["年"]
        converted["開催月日"] = parts["月日"]

        # そのままマッピングするカラム
        converted["競馬場"] = row["競馬場"]
        converted["開催回"] = row["回"]
        converted["開催日目"] = row["開催日"]
        converted["レース番号"] = int(parts["R"])
        converted["曜日"] = row["曜日"]
        converted["競走名本題"] = row["レース名"]
        converted["発走時刻"] = row["発走時刻"]
        converted["天候"] = row["天候"]
        converted["距離"] = row["距離"]
        converted["競走種別"] = row["競走種別"]
        converted["競走条件名称"] = row["競走条件"]
        converted["グレード"] = row["グレード"]
        converted["競走記号"] = row["競走記号"]
        converted["重量種別"] = row["重量種別"]
        converted["出走頭数"] = row["頭数"]

        # 芝ダ + 左右 → トラック
        shiba_da = str(row["芝ダ"]) if pd.notna(row["芝ダ"]) else ""
        sayuu = str(row["左右"]) if pd.notna(row["左右"]) else ""
        converted["トラック"] = shiba_da + sayuu

        # コース + 内外 → コース区分
        course = str(row["コース"]) if pd.notna(row["コース"]) else ""
        uchisoto = str(row["内外"]) if pd.notna(row["内外"]) else ""
        converted["コース区分"] = course + uchisoto

        # 賞金: 万円 → 百円単位変換
        for i in range(1, 6):
            scraping_col = f"{i}着賞金"
            schema_col = f"本賞金{i}着"
            val = row[scraping_col]
            if pd.notna(val):
                converted[schema_col] = convert_manyen_to_hyakuyen(int(val))

        # 馬場 → 芝馬場状態 / ダート馬場状態の振り分け
        baba = row["馬場"] if pd.notna(row.get("馬場")) else None
        if baba is not None:
            if shiba_da == "芝" or shiba_da == "障":
                converted["芝馬場状態"] = baba
            elif shiba_da == "ダ":
                converted["ダート馬場状態"] = baba

        result = pd.DataFrame([converted])
        result = ensure_columns(result, RACE_INFO_COLUMNS)
        result = apply_types(result, RACE_INFO_TYPES)
        return result

    def _convert_entry(self, raw: pd.DataFrame, race_code: str) -> pd.DataFrame:
        """get_entry用: scraping出力を統一スキーマに変換する."""
        parts = extract_race_code_parts(race_code)
        rows: list[dict[str, object]] = []

        for _, row in raw.iterrows():
            converted: dict[str, object] = {}
            self._set_header_columns(converted, race_code, parts)
            converted["枠番"] = row["枠"]
            converted["馬番"] = row["馬番"]
            converted["血統登録番号"] = row["馬ID"]
            converted["馬名"] = row["馬名"]
            converted["性別"] = row["性別"]
            converted["馬齢"] = row["年齢"]
            converted["負担重量"] = row["斤量"]
            converted["騎手名略称"] = row["騎手"]
            converted["騎手コード"] = row["騎手ID"]
            converted["所属"] = row["所属"]
            converted["調教師名略称"] = row["厩舎"]
            converted["調教師コード"] = row["厩舎ID"]
            converted["馬体重"] = row["馬体重"]

            # 増減 → 増減符号 + 増減差
            self._set_zogen(converted, row["増減"])

            # 出走区分 → 異常区分
            shutsuso_kubun = row["出走区分"]
            if pd.notna(shutsuso_kubun):
                converted["異常区分"] = _IJO_KUBUN_MAP.get(str(shutsuso_kubun), str(shutsuso_kubun))

            rows.append(converted)

        result = pd.DataFrame(rows)
        result = ensure_columns(result, HORSE_RACE_INFO_COLUMNS)
        result = apply_types(result, HORSE_RACE_INFO_TYPES)
        return result

    def _convert_result(
        self,
        raw: pd.DataFrame,
        race_code: str,
        prize_map: dict[int, int] | None = None,
    ) -> pd.DataFrame:
        """get_result用: scraping出力を統一スキーマに変換する.

        Args:
            raw: ResultPageScraper.get_result()の出力
            race_code: 16桁レースコード
            prize_map: 着順→獲得本賞金(百円単位)のマッピング。
                Noneの場合は獲得本賞金を設定しない。
        """
        parts = extract_race_code_parts(race_code)

        # 1着タイムを取得（タイム差計算用）
        first_time: float | None = None
        for _, row in raw.iterrows():
            if pd.notna(row.get("着順")) and str(row["着順"]).isdigit():
                if int(row["着順"]) == 1 and pd.notna(row.get("タイム")):
                    first_time = _parse_time_to_seconds(str(row["タイム"]))
                    break

        rows: list[dict[str, object]] = []
        for _, row in raw.iterrows():
            converted: dict[str, object] = {}
            self._set_header_columns(converted, race_code, parts)
            converted["枠番"] = row["枠"]
            converted["馬番"] = row["馬番"]
            converted["血統登録番号"] = row["馬ID"]
            converted["馬名"] = row["馬名"]
            converted["性別"] = row["性別"]
            converted["馬齢"] = row["年齢"]
            converted["負担重量"] = row["斤量"]
            converted["騎手名略称"] = row["騎手"]
            converted["騎手コード"] = row["騎手ID"]
            converted["所属"] = row["所属"]
            converted["調教師名略称"] = row["厩舎"]
            converted["調教師コード"] = row["厩舎ID"]
            converted["馬体重"] = row["馬体重"]

            # 増減 → 増減符号 + 増減差
            self._set_zogen(converted, row["増減"])

            # 異常区分の判定
            ijo_kubun = row.get("異常区分", "")
            chakusa = row.get("着差", "")
            chakujun_raw = row.get("着順")

            is_kokaku = self._set_ijo_kubun(converted, ijo_kubun, chakusa)

            # 結果固有カラム
            if pd.notna(chakujun_raw) and str(chakujun_raw).isdigit():
                converted["確定着順"] = int(chakujun_raw)

            if pd.notna(row.get("タイム")):
                converted["走破タイム"] = row["タイム"]

            if pd.notna(chakusa) and not is_kokaku:
                converted["着差1"] = chakusa

            if pd.notna(row.get("人気")) and str(row["人気"]).isdigit():
                converted["単勝人気順"] = int(row["人気"])

            if pd.notna(row.get("単勝オッズ")):
                converted["単勝オッズ"] = row["単勝オッズ"]

            if pd.notna(row.get("後3F")):
                converted["後3ハロン"] = row["後3F"]

            # コーナー通過順
            for i in range(1, 5):
                col = f"{i}コーナー通過順"
                if pd.notna(row.get(col)):
                    converted[f"{i}コーナー順位"] = row[col]

            # タイム差の算出
            if (
                first_time is not None
                and pd.notna(row.get("タイム"))
                and converted.get("異常区分") == ""
            ):
                horse_time = _parse_time_to_seconds(str(row["タイム"]))
                converted["タイム差"] = round(horse_time - first_time, 1)

            # 獲得本賞金の導出
            if (
                prize_map is not None
                and pd.notna(chakujun_raw)
                and str(chakujun_raw).isdigit()
                and converted.get("異常区分") == ""
            ):
                chakujun = int(chakujun_raw)
                if chakujun in prize_map:
                    converted["獲得本賞金"] = prize_map[chakujun]

            rows.append(converted)

        result = pd.DataFrame(rows)
        result = ensure_columns(result, HORSE_RACE_INFO_COLUMNS)
        result = apply_types(result, HORSE_RACE_INFO_TYPES)
        return result

    @staticmethod
    def _build_prize_map(raw_race_info: pd.DataFrame) -> dict[int, int]:
        """レース情報から着順→獲得本賞金(百円単位)のマッピングを構築する."""
        prize_map: dict[int, int] = {}
        if len(raw_race_info) == 0:
            return prize_map
        row = raw_race_info.iloc[0]
        for i in range(1, 6):
            col = f"{i}着賞金"
            if col in row.index and pd.notna(row[col]):
                prize_map[i] = convert_manyen_to_hyakuyen(int(row[col]))
        return prize_map

    def _convert_race_result_info(
        self, raw_lap: pd.DataFrame, raw_corner: pd.DataFrame, race_code: str
    ) -> pd.DataFrame:
        """get_race_result_info用: ラップタイムとコーナー通過順を統一スキーマに変換する."""
        converted: dict[str, object] = {}
        converted["レースコード"] = race_code

        # ラップタイム
        if len(raw_lap) > 0:
            lap_row = raw_lap.iloc[0]
            for dist in range(100, 5001, 100):
                col = f"{dist}m"
                if col in lap_row.index and pd.notna(lap_row[col]):
                    converted[f"ラップ{dist}m"] = lap_row[col]

            # 前3ハロン / 後3ハロン
            if "レース前3F" in lap_row.index and pd.notna(lap_row["レース前3F"]):
                converted["前3ハロン"] = lap_row["レース前3F"]
            if "レース後3F" in lap_row.index and pd.notna(lap_row["レース後3F"]):
                converted["後3ハロン"] = lap_row["レース後3F"]

        # コーナー通過順
        if len(raw_corner) > 0:
            corner_row = raw_corner.iloc[0]
            for i in range(1, 5):
                col = f"{i}コーナー通過順"
                if col in corner_row.index and pd.notna(corner_row[col]):
                    converted[f"{i}コーナー通過順"] = corner_row[col]

        result = pd.DataFrame([converted])
        result = ensure_columns(result, RACE_RESULT_INFO_COLUMNS)
        result = apply_types(result, RACE_RESULT_INFO_TYPES)
        return result

    def _convert_odds(self, raw: pd.DataFrame, race_code: str) -> pd.DataFrame:
        """get_win_show_odds用: scraping出力を統一スキーマに変換する."""
        parts = extract_race_code_parts(race_code)
        rows: list[dict[str, object]] = []

        for _, row in raw.iterrows():
            converted: dict[str, object] = {}
            converted["レースコード"] = race_code
            converted["開催年"] = parts["年"]
            converted["開催月日"] = parts["月日"]
            converted["競馬場"] = keibajo_code_to_name(parts["競馬場"])
            converted["開催回"] = int(parts["回"])
            converted["開催日目"] = int(parts["日目"])
            converted["レース番号"] = int(parts["R"])
            converted["馬番"] = row["馬番"]

            if pd.notna(row.get("単勝オッズ")):
                converted["単勝オッズ"] = row["単勝オッズ"]
            if pd.notna(row.get("単勝人気")):
                converted["単勝人気"] = row["単勝人気"]
            if pd.notna(row.get("複勝最小オッズ")):
                converted["複勝最低オッズ"] = row["複勝最小オッズ"]
            if pd.notna(row.get("複勝最大オッズ")):
                converted["複勝最高オッズ"] = row["複勝最大オッズ"]
            if pd.notna(row.get("複勝人気")):
                converted["複勝人気"] = row["複勝人気"]

            rows.append(converted)

        result = pd.DataFrame(rows)
        result = ensure_columns(result, ODDS_COLUMNS)
        result = apply_types(result, ODDS_TYPES)
        return result

    def _convert_payoff(self, scraper: Any, race_code: str) -> pd.DataFrame:
        """get_payoff用: 8券種の払戻データを1行のDataFrameに結合する."""
        parts = extract_race_code_parts(race_code)
        converted: dict[str, object] = {}
        converted["レースコード"] = race_code
        converted["開催年"] = parts["年"]
        converted["開催月日"] = parts["月日"]
        converted["競馬場"] = keibajo_code_to_name(parts["競馬場"])
        converted["開催回"] = int(parts["回"])
        converted["開催日目"] = int(parts["日目"])
        converted["レース番号"] = int(parts["R"])

        def _map_single(
            raw: pd.DataFrame,
            kenshu: str,
            max_n: int,
        ) -> None:
            """単勝・複勝のカラムマッピング."""
            if len(raw) == 0:
                return
            row = raw.iloc[0]
            for i in range(1, max_n + 1):
                for scraping_suffix, schema_suffix in [
                    (f"馬番_{i}", f"{i}馬番"),
                    (f"払戻金_{i}", f"{i}払戻金"),
                    (f"人気_{i}", f"{i}人気順"),
                ]:
                    scraping_col = f"{kenshu}{scraping_suffix}"
                    schema_col = f"{kenshu}{schema_suffix}"
                    if scraping_col in row.index and pd.notna(row[scraping_col]):
                        converted[schema_col] = row[scraping_col]

        def _map_combination(
            raw: pd.DataFrame,
            kenshu: str,
            max_n: int,
            num_horses: int,
        ) -> None:
            """組み合わせ券種のカラムマッピング."""
            if len(raw) == 0:
                return
            row = raw.iloc[0]
            for i in range(1, max_n + 1):
                # 組番
                for j in range(1, num_horses + 1):
                    scraping_col = f"{kenshu}組番_{i}_{j}"
                    schema_col = f"{kenshu}{i}組番{j}"
                    if scraping_col in row.index and pd.notna(row[scraping_col]):
                        converted[schema_col] = row[scraping_col]
                # 払戻金
                scraping_col = f"{kenshu}払戻金_{i}"
                schema_col = f"{kenshu}{i}払戻金"
                if scraping_col in row.index and pd.notna(row[scraping_col]):
                    converted[schema_col] = row[scraping_col]
                # 人気順
                scraping_col = f"{kenshu}人気_{i}"
                schema_col = f"{kenshu}{i}人気順"
                if scraping_col in row.index and pd.notna(row[scraping_col]):
                    converted[schema_col] = row[scraping_col]

        # 単勝・複勝
        _map_single(scraper.get_win_payoff(), "単勝", 3)
        _map_single(scraper.get_show_payoff(), "複勝", 5)

        # 2頭組み合わせ
        _map_combination(scraper.get_bracket_payoff(), "枠連", 3, 2)
        _map_combination(scraper.get_quinella_payoff(), "馬連", 3, 2)
        _map_combination(scraper.get_quinella_place_payoff(), "ワイド", 7, 2)
        _map_combination(scraper.get_exacta_payoff(), "馬単", 6, 2)

        # 3頭組み合わせ
        _map_combination(scraper.get_trio_payoff(), "3連複", 3, 3)
        _map_combination(scraper.get_trifecta_payoff(), "3連単", 6, 3)

        result = pd.DataFrame([converted])
        result = ensure_columns(result, PAYOFF_COLUMNS)
        result = apply_types(result, PAYOFF_TYPES)
        return result

    def _convert_past_performances(self, raw: pd.DataFrame, horse_id: str) -> pd.DataFrame:
        """get_past_performances用: scraping出力を統一スキーマに変換する."""
        if len(raw) == 0:
            return apply_types(
                ensure_columns(pd.DataFrame(), HORSE_RACE_INFO_COLUMNS),
                HORSE_RACE_INFO_TYPES,
            )

        rows: list[dict[str, object]] = []
        for _, row in raw.iterrows():
            converted: dict[str, object] = {}

            # 血統登録番号
            converted["血統登録番号"] = horse_id

            # レースIDからレースコードを構築
            race_id_raw = row.get("レースID")
            if pd.notna(race_id_raw) and pd.notna(row.get("日付")):
                dt = row["日付"]
                if isinstance(dt, date):
                    monthday = f"{dt.month:02d}{dt.day:02d}"
                    race_id_str = str(race_id_raw)
                    # レースコード = 年(4) + 月日(4) + 競馬場(2) + 回(2) + 日目(2) + R(2)
                    converted["レースコード"] = race_id_str[:4] + monthday + race_id_str[4:]

            # 日付 → 開催年 + 開催月日
            if pd.notna(row.get("日付")):
                dt = row["日付"]
                if isinstance(dt, date):
                    converted["開催年"] = str(dt.year)
                    converted["開催月日"] = f"{dt.month:02d}{dt.day:02d}"

            converted["競馬場"] = row.get("競馬場")
            if pd.notna(row.get("回")):
                converted["開催回"] = row["回"]
            if pd.notna(row.get("開催日")):
                converted["開催日目"] = row["開催日"]
            if pd.notna(row.get("R")):
                converted["レース番号"] = row["R"]
            if pd.notna(row.get("枠")):
                converted["枠番"] = row["枠"]
            if pd.notna(row.get("馬番")):
                converted["馬番"] = row["馬番"]
            if pd.notna(row.get("馬名")):
                converted["馬名"] = row["馬名"]

            if pd.notna(row.get("斤量")):
                converted["負担重量"] = row["斤量"]
            if pd.notna(row.get("騎手")):
                converted["騎手名略称"] = row["騎手"]
            if pd.notna(row.get("騎手ID")):
                converted["騎手コード"] = row["騎手ID"]
            if pd.notna(row.get("馬体重")):
                converted["馬体重"] = row["馬体重"]

            # 増減 → 増減符号 + 増減差
            self._set_zogen(converted, row.get("増減"))

            # 異常区分
            ijo_kubun = row.get("異常区分", "")
            chakusa = row.get("着差", "")
            chakujun_raw = row.get("着順")

            is_kokaku = self._set_ijo_kubun(converted, ijo_kubun, chakusa)

            # 結果カラム
            if pd.notna(chakujun_raw) and str(chakujun_raw).isdigit():
                converted["確定着順"] = int(chakujun_raw)

            if pd.notna(row.get("タイム")):
                converted["走破タイム"] = row["タイム"]

            if pd.notna(chakusa) and not is_kokaku:
                converted["着差1"] = chakusa

            if pd.notna(row.get("人気")) and str(row["人気"]).isdigit():
                converted["単勝人気順"] = int(row["人気"])

            if pd.notna(row.get("単勝オッズ")):
                converted["単勝オッズ"] = row["単勝オッズ"]

            if pd.notna(row.get("後3F")):
                converted["後3ハロン"] = row["後3F"]

            if pd.notna(row.get("頭数")):
                converted["出走頭数"] = row["頭数"]

            # コーナー通過順
            for i in range(1, 5):
                col = f"{i}コーナー通過順"
                if pd.notna(row.get(col)):
                    converted[f"{i}コーナー順位"] = row[col]

            # 賞金: 万円 → 百円単位
            if pd.notna(row.get("賞金")):
                converted["獲得本賞金"] = convert_manyen_to_hyakuyen(int(row["賞金"]))

            # 勝ち馬(2着馬) → 相手1馬名
            if pd.notna(row.get("勝ち馬(2着馬)")):
                converted["相手1馬名"] = row["勝ち馬(2着馬)"]

            rows.append(converted)

        result = pd.DataFrame(rows)
        result = ensure_columns(result, HORSE_RACE_INFO_COLUMNS)
        result = apply_types(result, HORSE_RACE_INFO_TYPES)
        return result

    def _convert_schedule(self, raw: pd.DataFrame) -> pd.DataFrame:
        """get_schedule用: レース単位の出力を開催場単位に集約して統一スキーマに変換する."""
        # レースIDから開催コード的な情報を導出するため、
        # グループキーとして競馬場・日付・回・開催日を使用
        seen: dict[str, dict[str, object]] = {}

        for _, row in raw.iterrows():
            race_id = str(row["レースID"])
            # レースID: 年(4)+競馬場(2)+回(2)+日目(2)+R(2)
            if len(race_id) == 12:
                year = race_id[0:4]
                keibajo_code = race_id[4:6]
                kai = race_id[6:8]
                nichime = race_id[8:10]
                kaisai_key = f"{year}{keibajo_code}{kai}{nichime}"
            else:
                continue

            if kaisai_key in seen:
                continue

            converted: dict[str, object] = {}

            # 日付 → 開催年 + 開催月日
            dt = row["日付"]
            if isinstance(dt, date):
                monthday = f"{dt.month:02d}{dt.day:02d}"
                converted["開催コード"] = f"{year}{monthday}{keibajo_code}{kai}{nichime}"
                converted["開催年"] = year
                converted["開催月日"] = monthday

            converted["競馬場"] = row.get("競馬場")
            if pd.notna(row.get("回")):
                converted["開催回"] = row["回"]
            if pd.notna(row.get("開催日")):
                converted["開催日目"] = row["開催日"]

            seen[kaisai_key] = converted

        if not seen:
            return apply_types(
                ensure_columns(pd.DataFrame(), SCHEDULE_COLUMNS),
                SCHEDULE_TYPES,
            )

        result = pd.DataFrame(list(seen.values()))
        result = ensure_columns(result, SCHEDULE_COLUMNS)
        result = apply_types(result, SCHEDULE_TYPES)
        return result

    @staticmethod
    def _set_header_columns(
        converted: dict[str, object], race_code: str, parts: dict[str, str]
    ) -> None:
        """レースコードからヘッダカラムを設定する."""
        converted["レースコード"] = race_code
        converted["開催年"] = parts["年"]
        converted["開催月日"] = parts["月日"]
        converted["競馬場"] = keibajo_code_to_name(parts["競馬場"])
        converted["開催回"] = int(parts["回"])
        converted["開催日目"] = int(parts["日目"])
        converted["レース番号"] = int(parts["R"])

    @staticmethod
    def _set_zogen(converted: dict[str, object], zogen: Any) -> None:
        """増減符号と増減差を設定する."""
        if pd.notna(zogen):
            fugo, sa = split_zogen(int(zogen))
            converted["増減符号"] = fugo
            converted["増減差"] = sa

    @staticmethod
    def _set_ijo_kubun(
        converted: dict[str, object],
        ijo_kubun: Any,
        chakusa: Any,
    ) -> bool:
        """異常区分を設定し、降着かどうかを返す."""
        is_kokaku = (
            pd.notna(chakusa)
            and isinstance(chakusa, str)
            and re.search(r"\d+位降着", chakusa) is not None
        )
        if is_kokaku:
            converted["異常区分"] = "降着"
        elif pd.notna(ijo_kubun) and str(ijo_kubun) in _IJO_KUBUN_MAP:
            converted["異常区分"] = _IJO_KUBUN_MAP[str(ijo_kubun)]
        elif pd.notna(ijo_kubun) and str(ijo_kubun):
            converted["異常区分"] = str(ijo_kubun)
        else:
            converted["異常区分"] = ""
        return is_kokaku


def _parse_time_to_seconds(time_str: str) -> float:
    """走破タイム文字列("M:SS.S")を秒に変換する.

    Args:
        time_str (str): "M:SS.S"形式の走破タイム

    Returns:
        float: 秒単位の走破タイム

    Raises:
        ValueError: 走破タイム形式が不正な場合
    """
    m = re.match(r"(\d+):(\d+)\.(\d)", time_str)
    if not m:
        raise ValueError(f"走破タイム形式が不正です: {time_str}")
    minutes = int(m.group(1))
    seconds = int(m.group(2))
    tenths = int(m.group(3))
    return minutes * 60 + seconds + tenths / 10
