"""DataProvider Protocolの定義.

データソースの抽象インターフェースを定義する。
ScrapingProviderおよびMykeibaDBProviderはこのProtocolに準拠する。
"""

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class DataProvider(Protocol):
    """データソースの抽象インターフェース.

    各データソース（scraping, mykeibadb）はこのProtocolを実装する。

    Attributes:
        supports_bulk: 一括取得メソッド（get_xxx_bulk）に対応しているか。
            未対応のProviderは一括取得メソッドでDataNotFoundErrorを送出するため、
            呼び出し側はこのフラグを見て1件ずつ取得する経路へ切り替える
    """

    supports_bulk: bool

    def get_race_basic_info(self, race_code: str) -> pd.DataFrame:
        """レース基本情報を取得する.

        Args:
            race_code: 16桁レースコード
        """
        ...

    def get_race_basic_info_bulk(self, race_codes: list[str]) -> pd.DataFrame:
        """複数レースのレース基本情報をまとめて取得する.

        Args:
            race_codes: 16桁レースコードのリスト

        Returns:
            レース基本情報のDataFrame。カラム構成はget_race_basic_infoと同一で、
            レースコード昇順に並ぶ。存在しないレースコードの行は含まれないため、
            行数は指定した件数と一致するとは限らない。重複したレースコードは
            取り除かれ、1レース1行になる
        """
        ...

    def get_race_data_bulk(
        self, race_codes: list[str], kinds: Sequence[str] | None = None
    ) -> dict[str, dict[str, pd.DataFrame]]:
        """複数レースのデータ種別ごとの結果をまとめて取得する.

        プリフェッチ層が使う。指定された種別に必要なテーブルだけを取得し、同一テーブルを
        引く種別はテーブル単位で1回だけ取得して、種別ごとの変換を適用して返す。

        Args:
            race_codes: 16桁レースコードのリスト
            kinds: 取得するデータ種別（DataKind）。省略時はレース単位の全種別

        Returns:
            データ種別（DataKind）→ レースコード → DataFrame の二段の辞書。
            存在しないレースコードは含まれない
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
            horse_id: 馬ID（血統登録番号）
        """
        ...

    def get_past_performances_bulk(self, horse_ids: list[str]) -> dict[str, pd.DataFrame]:
        """複数馬の過去成績（馬柱）をまとめて取得する.

        Args:
            horse_ids: 馬ID（血統登録番号）のリスト
        """
        ...

    def get_horse_master(self, horse_id: str) -> pd.DataFrame:
        """競走馬情報を取得する.

        Args:
            horse_id: 馬ID（血統登録番号）
        """
        ...

    def get_horse_master_bulk(self, horse_ids: list[str]) -> dict[str, pd.DataFrame]:
        """複数馬の競走馬情報をまとめて取得する.

        Args:
            horse_ids: 馬ID（血統登録番号）のリスト
        """
        ...

    def get_chakudosu(self, race_code: str) -> pd.DataFrame:
        """出走別着度数を取得する.

        Args:
            race_code: 16桁レースコード
        """
        ...

    def get_schedule(self, start_date: str, end_date: str) -> pd.DataFrame:
        """開催スケジュールを取得する.

        Args:
            start_date: 開始日（YYYY-MM-DD形式）
            end_date: 終了日（YYYY-MM-DD形式）
        """
        ...
