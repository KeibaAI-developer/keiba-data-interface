"""DataInterfaceクラスの実装.

利用者向けAPIのファサードクラスを提供する。
Provider名を指定することで、データソースを切り替えてデータを取得できる。
"""

import importlib
import logging
from collections.abc import Callable, Sequence

import pandas as pd

from keiba_data_interface import course_days
from keiba_data_interface.cache import DataCache, DataKind, is_future_race_code
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

    def __init__(
        self,
        provider: str,
        logger: logging.Logger | None = None,
        cache: DataCache | None = None,
    ) -> None:
        """コンストラクタ.

        Args:
            provider: データソース名（'scraping' または 'mykeibadb'）
            logger: ロガーインスタンス
            cache: 取得結果のキャッシュ。複数のDataInterfaceで共有したい場合に渡す。
                省略時はインスタンス専用のキャッシュを持つ

        Raises:
            KeibaDataInterfaceError: 不正なprovider名が指定された場合
        """
        self._logger = logger or logging.getLogger(__name__)
        provider_logger = self._logger.getChild(provider)
        self._provider: DataProvider = _create_provider(provider, provider_logger)
        self._cache = (
            cache if cache is not None else DataCache(logger=self._logger.getChild("cache"))
        )
        # キャッシュのデータ種別へデータソース名を含める。データソースが異なれば
        # 同じレースコードでも値が異なりうるため、共有しても混ざらないようにする
        self._cache_kind_prefix = provider
        # コース日数は開催日単位で決まる値のため、インスタンス内で使い回す
        self._course_days_cache = course_days.CourseDaysCache()
        self._logger.debug("DataInterfaceを初期化しました: provider=%s", provider)

    def get_race_basic_info(self, race_code: str, calc_course_days: bool = False) -> pd.DataFrame:
        """レース基本情報を取得する.

        Args:
            race_code: 16桁レースコード
            calc_course_days: Trueの場合、芝コース日数情報（芝コース日目・芝コース初日・
                芝コース経過日数・芝コース週目）を計算して付与する。計算には過去レースの
                遡及取得が発生するため取得時間が増加する（特にscraping providerでは
                複数ページのスクレイピングを伴う）

        Returns:
            レース基本情報のDataFrame（1行）
        """
        # コース日数を付与する前の値をキャッシュする。コース日数はCourseDaysCacheが
        # 別に持つため、ここへ混ぜると付与の有無で戻り値が変わってしまう
        result = self._get_cached(
            DataKind.RACE_BASIC_INFO, race_code, self._provider.get_race_basic_info
        )
        if calc_course_days:
            result = course_days.calc_course_days(
                result, self._provider, self._logger, self._course_days_cache
            )
        return result

    def get_race_basic_info_bulk(self, race_codes: list[str]) -> pd.DataFrame:
        """複数レースのレース基本情報をまとめて取得する.

        レースコードごとに`get_race_basic_info`を呼ぶとレース数だけクエリが発行される。
        本メソッドは1回のクエリでまとめて取得する。

        芝コース日数情報は付与しない。開催日ごとの遡及取得が必要で、まとめて取得する
        利点が失われるため。

        Args:
            race_codes: 16桁レースコードのリスト

        Returns:
            レース基本情報のDataFrame（RACE_BASIC_INFO_COLUMNSのカラム、レースコード昇順）。
            存在しないレースコードの行は含まれない。指定した件数と一致するとは限らない

        Raises:
            DataNotFoundError: scrapingプロバイダーを使用している場合
        """
        return self._provider.get_race_basic_info_bulk(race_codes)

    def prefetch_races(self, race_codes: Sequence[str]) -> None:
        """指定したレースコードのデータを一括取得してキャッシュへ格納する.

        レースコードごとに取得するとレース数だけクエリが発行される。これから使う
        レースコードをまとめて渡すことで、取得を1回にまとめられる。

        未来レース（当日を含む）はキャッシュしない。単勝オッズは発走直前まで変動し、
        キャッシュした値を返すと古いオッズで予測することになるため。

        一括取得に対応していないProvider（scraping）では何もしない。プリフェッチは
        高速化のための処理であり、行わなくても単一キー取得は従来どおり動作する。

        Args:
            race_codes: 16桁レースコードのリスト
        """
        if not self._provider.supports_bulk:
            self._logger.debug("Providerが一括取得に未対応のためプリフェッチしません")
            return

        targets = [code for code in dict.fromkeys(race_codes) if not is_future_race_code(code)]
        if not targets:
            self._logger.debug("プリフェッチ対象のレースコードがありません")
            return

        self._logger.debug("レース単位データをプリフェッチします: 件数=%d", len(targets))
        race_data = self._provider.get_race_data_bulk(targets)
        for kind, by_race_code in race_data.items():
            for race_code, df in by_race_code.items():
                self._cache.set(self._cache_kind(kind), race_code, df)
        self._logger.debug(
            "プリフェッチが完了しました: 種別=%d, レース基本情報=%d件",
            len(race_data),
            len(race_data.get(DataKind.RACE_BASIC_INFO, {})),
        )

    def _get_cached(
        self,
        kind: str,
        race_code: str,
        fetch: Callable[[str], pd.DataFrame],
    ) -> pd.DataFrame:
        """キャッシュを見てから取得する.

        キャッシュから返すのはコピーとする。呼び出し側が戻り値を変更してもキャッシュが
        壊れないようにするため。

        Args:
            kind (str): キャッシュのデータ種別
            race_code (str): 16桁レースコード
            fetch (Callable[[str], pd.DataFrame]): キャッシュに無い場合の取得処理

        Returns:
            pd.DataFrame: 取得したDataFrame
        """
        cached = self._cache.get(self._cache_kind(kind), race_code)
        if cached is not None:
            return cached.copy()

        result = fetch(race_code)
        self._cache.set(self._cache_kind(kind), race_code, result.copy())
        return result

    def _cache_kind(self, kind: str) -> str:
        """データソース名を含めたキャッシュのデータ種別名を返す.

        Args:
            kind (str): データ種別名

        Returns:
            str: データソース名を含めたデータ種別名
        """
        return f"{self._cache_kind_prefix}:{kind}"

    def clear_cache(self) -> None:
        """キャッシュを空にする."""
        self._cache.clear()

    def get_entry(self, race_code: str) -> pd.DataFrame:
        """出馬表を取得する.

        Args:
            race_code: 16桁レースコード

        Returns:
            出馬表のDataFrame（出走頭数行）
        """
        return self._get_cached(
            DataKind.ENTRY, race_code, self._provider.get_entry
        )

    def get_win_show_odds(self, race_code: str) -> pd.DataFrame:
        """単複オッズを取得する.

        Args:
            race_code: 16桁レースコード

        Returns:
            単複オッズのDataFrame
        """
        return self._get_cached(
            DataKind.WIN_SHOW_ODDS, race_code, self._provider.get_win_show_odds
        )

    def get_result(self, race_code: str) -> pd.DataFrame:
        """レース結果（馬毎）を取得する.

        Args:
            race_code: 16桁レースコード

        Returns:
            レース結果のDataFrame（出走頭数行）
        """
        return self._get_cached(
            DataKind.RESULT, race_code, self._provider.get_result
        )

    def get_race_result_info(self, race_code: str) -> pd.DataFrame:
        """レース結果情報（ラップ・コーナー通過順）を取得する.

        Args:
            race_code: 16桁レースコード

        Returns:
            レース結果情報のDataFrame（1行）
        """
        return self._get_cached(
            DataKind.RACE_RESULT_INFO, race_code, self._provider.get_race_result_info
        )

    def get_payoff(self, race_code: str) -> pd.DataFrame:
        """払戻情報を取得する.

        Args:
            race_code: 16桁レースコード

        Returns:
            払戻情報のDataFrame（1行）
        """
        return self._get_cached(
            DataKind.PAYOFF, race_code, self._provider.get_payoff
        )

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

    def get_chakudosu(self, race_code: str) -> pd.DataFrame:
        """出走別着度数を取得する.

        指定レース出走時点の各馬の累積着回数（競馬場別・距離別・馬場別・馬場状態別）を
        出走頭数分の行で返す。

        Args:
            race_code: 16桁レースコード

        Returns:
            出走別着度数のDataFrame（出走頭数行、血統登録番号昇順）

        Raises:
            DataNotFoundError: scrapingプロバイダーの場合（netkeibaから取得不可）
        """
        result = self._provider.get_chakudosu(race_code)
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
