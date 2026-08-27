"""DataInterfaceクラスの実装.

利用者向けAPIのファサードクラスを提供する。
Provider名を指定することで、データソースを切り替えてデータを取得できる。
"""

import importlib
import logging
from collections.abc import Callable, Sequence

import pandas as pd

from keiba_data_interface.cache import (
    RACE_DATA_KINDS,
    DataCache,
    DataKind,
    is_future_race_code,
)
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
        self._logger.debug("DataInterfaceを初期化しました: provider=%s", provider)

    @property
    def supports_bulk(self) -> bool:
        """Providerが一括取得に対応しているか.

        一括取得の有無で処理を変えたい呼び出し側のために公開する。多くの場合は
        `DataInterface` 側が能力差を吸収する（`get_past_performances_bulk` など）ため、
        呼び出し側が参照する必要はない。

        Returns:
            Providerが一括取得メソッドに対応していればTrue
        """
        return self._provider.supports_bulk

    def get_race_basic_info(self, race_code: str) -> pd.DataFrame:
        """レース基本情報を取得する.

        Args:
            race_code: 16桁レースコード

        Returns:
            レース基本情報のDataFrame（1行）

        Raises:
            DataNotFoundError: レースが存在しない場合
        """
        return self._get_cached(
            DataKind.RACE_BASIC_INFO, race_code, self._provider.get_race_basic_info
        )

    def get_race_basic_info_bulk(self, race_codes: list[str]) -> pd.DataFrame:
        """複数レースのレース基本情報をまとめて取得する.

        レースコードごとに`get_race_basic_info`を呼ぶとレース数だけクエリが発行される。
        本メソッドは1回のクエリでまとめて取得する。

        Args:
            race_codes: 16桁レースコードのリスト

        Returns:
            レース基本情報のDataFrame（RACE_BASIC_INFO_COLUMNSのカラム、レースコード昇順）。
            存在しないレースコードの行は含まれない。指定した件数と一致するとは限らない

        Raises:
            UnsupportedOperationError: scrapingプロバイダーを使用している場合
        """
        return self._provider.get_race_basic_info_bulk(race_codes)

    def prefetch_races(
        self, race_codes: Sequence[str], kinds: Sequence[str] | None = None
    ) -> None:
        """指定したレースコードのデータを一括取得してキャッシュへ格納する.

        レースコードごとに取得するとレース数だけクエリが発行される。これから使う
        レースコードをまとめて渡すことで、取得を1回にまとめられる。

        使わないデータ種別は `kinds` から外すこと。取得だけでなく変換のコストも
        避けられる。変換はレース単位でしか行えないため、取得する種別を絞る以外に
        減らす手段がない。

        未来レース（当日を含む）はキャッシュしない。単勝オッズは発走直前まで変動し、
        キャッシュした値を返すと古いオッズで予測することになるため。

        一括取得に対応していないProvider（scraping）では何もしない。プリフェッチは
        高速化のための処理であり、行わなくても単一キー取得は従来どおり動作する。

        Args:
            race_codes: 16桁レースコードのリスト
            kinds: 取得するデータ種別（DataKind）。省略時はレース単位の全種別。
                空のリストを渡した場合は何も取得しない

        Raises:
            ValueError: kindsに未知のデータ種別が含まれる場合
        """
        if kinds is not None:
            unknown_kinds = sorted(set(kinds) - set(RACE_DATA_KINDS))
            if unknown_kinds:
                message = (
                    f"未知のデータ種別が指定されました: {unknown_kinds}"
                    f"（指定できる種別: {list(RACE_DATA_KINDS)}）"
                )
                self._logger.error(message)
                raise ValueError(message)

        if not self._provider.supports_bulk:
            self._logger.debug("Providerが一括取得に未対応のためプリフェッチしません")
            return

        targets = [code for code in dict.fromkeys(race_codes) if not is_future_race_code(code)]
        if not targets:
            self._logger.debug("プリフェッチ対象のレースコードがありません")
            return

        self._logger.debug("レース単位データをプリフェッチします: 件数=%d", len(targets))
        race_data = self._provider.get_race_data_bulk(targets, kinds)
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

    def get_win_show_votes(self, race_code: str) -> pd.DataFrame:
        """単勝・複勝の票数を取得する.

        票数は予測時に対象レース1件を取るデータのため、キャッシュ（prefetch_races）の
        対象にしない。

        Args:
            race_code: 16桁レースコード

        Returns:
            単複票数のDataFrame（出走頭数行、馬番順）

        Raises:
            DataNotFoundError: 該当レースの票数が存在しない場合
            UnsupportedOperationError: scrapingプロバイダーの場合（netkeibaに票数の掲載が無い）
        """
        return self._provider.get_win_show_votes(race_code)

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

        Raises:
            DataNotFoundError: レースが存在しない場合
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

        Raises:
            DataNotFoundError: レースが存在しない場合
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

    def get_past_performances_bulk(self, horse_ids: list[str]) -> dict[str, pd.DataFrame]:
        """複数馬の過去成績（馬柱）をまとめて取得する.

        Providerが一括取得に対応していない場合は1頭ずつ取得して同じ形の辞書を返す。
        `prefetch_races`（一括に未対応なら何もしない）と違い、こちらは戻り値そのものが
        必要なため。Providerの能力差を吸収するのはDataInterfaceの役割であり、
        呼び出し側がProviderの種類で分岐しなくて済む。

        Args:
            horse_ids: 馬ID（血統登録番号）のリスト

        Returns:
            馬ID → 過去成績のDataFrame（レースコード降順）。
            指定した馬IDは必ずキーに含まれる
        """
        if self._provider.supports_bulk:
            return self._provider.get_past_performances_bulk(horse_ids)

        self._logger.debug("Providerが一括取得に未対応のため1頭ずつ取得します")
        return {
            horse_id: self._provider.get_past_performances(horse_id)
            for horse_id in dict.fromkeys(horse_ids)
        }

    def get_horse_master(self, horse_id: str) -> pd.DataFrame:
        """競走馬情報を取得する.

        Args:
            horse_id: 馬ID（血統登録番号）

        Returns:
            競走馬情報のDataFrame（1行）
        """
        result = self._provider.get_horse_master(horse_id)
        return result

    def get_horse_master_bulk(self, horse_ids: list[str]) -> dict[str, pd.DataFrame]:
        """複数馬の競走馬情報をまとめて取得する.

        Providerが一括取得に対応していない場合は1頭ずつ取得して同じ形の辞書を返す。
        `get_past_performances_bulk` と同じ扱い。

        Args:
            horse_ids: 馬ID（血統登録番号）のリスト

        Returns:
            馬ID → 競走馬情報のDataFrame（1行）。
            指定した馬IDは必ずキーに含まれる
        """
        if self._provider.supports_bulk:
            return self._provider.get_horse_master_bulk(horse_ids)

        self._logger.debug("Providerが一括取得に未対応のため1頭ずつ取得します")
        return {
            horse_id: self._provider.get_horse_master(horse_id)
            for horse_id in dict.fromkeys(horse_ids)
        }

    def get_chakudosu(self, race_code: str) -> pd.DataFrame:
        """出走別着度数を取得する.

        指定レース出走時点の各馬の累積着回数（競馬場別・距離別・馬場別・馬場状態別）を
        出走頭数分の行で返す。

        Args:
            race_code: 16桁レースコード

        Returns:
            出走別着度数のDataFrame（出走頭数行、血統登録番号昇順）

        Raises:
            UnsupportedOperationError: scrapingプロバイダーの場合（netkeibaから取得不可）
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
