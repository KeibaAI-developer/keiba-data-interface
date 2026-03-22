"""ScrapingProvider: keiba-scrapingを使用したデータ取得Provider."""

from typing import Any

import pandas as pd

from keiba_data_interface.schema.columns import RACE_INFO_COLUMNS
from keiba_data_interface.schema.types import RACE_INFO_TYPES
from keiba_data_interface.utils.converters import convert_manyen_to_hyakuyen
from keiba_data_interface.utils.dataframe import apply_types, ensure_columns
from keiba_data_interface.utils.race_code import extract_race_code_parts, race_code_to_race_id


class ScrapingProvider:
    """keiba-scrapingを使用したデータ取得Provider."""

    def __init__(self, scraper_class: type[Any] | None = None) -> None:
        """ScrapingProviderを初期化する.

        Args:
            scraper_class (EntryPageScraper): スクレイパークラス。
                Noneの場合はEntryPageScraperを使用する。
                テスト時にモッククラスを注入するために使用する。
        """
        if scraper_class is None:
            from scraping import EntryPageScraper

            scraper_class = EntryPageScraper
        self._scraper_class: type[EntryPageScraper] = scraper_class

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

        Raises:
            NotImplementedError: 未実装
        """
        raise NotImplementedError

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

    def _convert_race_info(self, raw: pd.DataFrame, race_code: str) -> pd.DataFrame:
        """scraping出力を統一スキーマに変換する.

        Args:
            raw (pd.DataFrame): EntryPageScraper.get_race_info()の出力
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: 統一スキーマに変換されたDataFrame
        """
        parts = extract_race_code_parts(race_code)
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
