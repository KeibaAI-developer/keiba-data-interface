"""MykeibaDBProvider: mykeibadb-pythonを使用したデータ取得Provider.

mykeibadb-pythonのRaceGetter/OddsGetterを使用してJRA-VANデータを取得し、
統一スキーマに変換する。
"""

import logging
from collections.abc import Sequence
from datetime import date

import pandas as pd
from mykeibadb import HyosuGetter, MasterGetter, OddsGetter, RaceGetter, ShussobetsuGetter

from keiba_data_interface.cache import RACE_DATA_KINDS, DataKind
from keiba_data_interface.exceptions import DataNotFoundError
from keiba_data_interface.providers.mykeibadb_converters import (
    convert_chakudosu,
    convert_entry,
    convert_entry_bulk,
    convert_horse_master,
    convert_horse_master_bulk,
    convert_past_performances,
    convert_past_performances_bulk,
    convert_payoff,
    convert_payoff_bulk,
    convert_race_basic_info,
    convert_race_basic_info_bulk,
    convert_race_result_info,
    convert_race_result_info_bulk,
    convert_result,
    convert_result_bulk,
    convert_schedule,
    convert_win_show_odds,
    convert_win_show_votes,
)


class MykeibaDBProvider:
    """mykeibadb-pythonを使用したデータ取得Provider.

    Attributes:
        _race_getter (RaceGetter): JRA-VANデータ取得用のRaceGetterインスタンス
        _odds_getter (OddsGetter): JRA-VANオッズ取得用のOddsGetterインスタンス
        _master_getter (MasterGetter): JRA-VANマスタ取得用のMasterGetterインスタンス
        _shussobetsu_getter (ShussobetsuGetter): JRA-VAN出走別データ取得用の
            ShussobetsuGetterインスタンス
        _hyosu_getter (HyosuGetter): JRA-VAN票数取得用のHyosuGetterインスタンス
    """

    # 一括取得メソッドに対応している（RaceGetter等がキーのリストを受け付けるため）
    supports_bulk = True
    # 単複票数（HYOSU1_TANSHO / HYOSU1_FUKUSHO）を取得できる
    supports_votes = True

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """コンストラクタ.

        Args:
            logger: ロガーインスタンス
        """
        self._logger = logger or logging.getLogger(__name__)
        self._race_getter = RaceGetter(logger=self._logger)
        self._odds_getter = OddsGetter(logger=self._logger)
        self._master_getter = MasterGetter(logger=self._logger)
        self._shussobetsu_getter = ShussobetsuGetter(logger=self._logger)
        self._hyosu_getter = HyosuGetter(logger=self._logger)

    def get_race_basic_info(self, race_code: str) -> pd.DataFrame:
        """レース基本情報を取得する.

        RaceGetter.get_race_shosai()でレース詳細を取得し、統一スキーマに変換する。

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: レース基本情報（1行、RACE_INFO_COLUMNSのカラム）
        """
        self._logger.debug("RaceGetterでレース基本情報を取得: race_code=%s", race_code)
        raw = self._race_getter.get_race_shosai(race_code=race_code, convert_codes=False)
        result = convert_race_basic_info(raw)
        self._logger.debug("レース基本情報の取得が完了: race_code=%s", race_code)
        return result

    def get_race_basic_info_bulk(self, race_codes: list[str]) -> pd.DataFrame:
        """複数レースのレース基本情報をまとめて取得する.

        RaceGetter.get_race_shosai()へレースコードのリストを渡し、1クエリで取得して
        統一スキーマに変換する。レースコードごとに取得するとレース数だけクエリが
        発行されるため、まとめて取得する経路を用意している。

        Args:
            race_codes (list[str]): 16桁レースコードのリスト

        Returns:
            pd.DataFrame: レース基本情報（RACE_BASIC_INFO_COLUMNSのカラム、
                レースコード昇順）。存在しないレースコードの行は含まれない
        """
        unique_race_codes = list(dict.fromkeys(race_codes))
        if not unique_race_codes:
            self._logger.debug("レースコードが空のためクエリを発行しません")
            return convert_race_basic_info_bulk(pd.DataFrame())

        self._logger.debug(
            "RaceGetterでレース基本情報を一括取得: 件数=%d", len(unique_race_codes)
        )
        raw = self._race_getter.get_race_shosai(
            race_code=unique_race_codes, convert_codes=False
        )
        result = convert_race_basic_info_bulk(raw)
        self._logger.debug(
            "レース基本情報の一括取得が完了: 指定=%d件, 取得=%d件",
            len(unique_race_codes),
            len(result),
        )
        return result

    def get_race_data_bulk(
        self, race_codes: list[str], kinds: Sequence[str] | None = None
    ) -> dict[str, dict[str, pd.DataFrame]]:
        """複数レースのデータ種別ごとの結果をまとめて取得する.

        同一テーブルを引く種別はテーブル単位で1回だけ取得する。UMAGOTO_RACE_JOHOから
        出馬表とレース結果を、RACE_SHOSAIからレース基本情報とレース結果情報を作る。

        指定された種別に必要なテーブルだけを取得する。変換はレースコードでグループ化
        してから種別ごとの変換関数へ渡す。単勝人気順の再計算やレース内での人気順など、
        レース単位でしか計算できない処理を含むため、複数レースをまとめて変換できない。
        **減るのはクエリ回数であり変換回数ではない。** 使わない種別を指定から外すことで
        変換のコストも避けられる。

        Args:
            race_codes (list[str]): 16桁レースコードのリスト
            kinds (Sequence[str] | None): 取得するデータ種別（DataKind）。
                省略時はレース単位の全種別

        Returns:
            dict[str, dict[str, pd.DataFrame]]: データ種別 → レースコード → DataFrame。
                存在しないレースコードは含まれない
        """
        target_kinds = set(RACE_DATA_KINDS if kinds is None else kinds)
        unique_race_codes = list(dict.fromkeys(race_codes))
        if not unique_race_codes or not target_kinds:
            self._logger.debug("取得対象が無いためクエリを発行しません")
            return {}

        self._logger.debug(
            "レース単位データを一括取得: 件数=%d, 種別=%d",
            len(unique_race_codes),
            len(target_kinds),
        )
        result: dict[str, dict[str, pd.DataFrame]] = {}

        if target_kinds & {DataKind.RACE_BASIC_INFO, DataKind.RACE_RESULT_INFO}:
            raw_shosai = self._race_getter.get_race_shosai(
                race_code=unique_race_codes, convert_codes=False
            )
            if DataKind.RACE_BASIC_INFO in target_kinds:
                result[DataKind.RACE_BASIC_INFO] = _split_per_race(
                    convert_race_basic_info_bulk(raw_shosai)
                )
            if DataKind.RACE_RESULT_INFO in target_kinds:
                result[DataKind.RACE_RESULT_INFO] = _split_per_race(
                    convert_race_result_info_bulk(raw_shosai)
                )

        if target_kinds & {DataKind.ENTRY, DataKind.RESULT}:
            raw_umagoto = self._race_getter.get_umagoto_race_joho(
                race_code=unique_race_codes, convert_codes=False
            )
            if DataKind.ENTRY in target_kinds:
                result[DataKind.ENTRY] = _split_per_race(
                    convert_entry_bulk(raw_umagoto), sort_columns=["馬番"]
                )
            if DataKind.RESULT in target_kinds:
                result[DataKind.RESULT] = _split_per_race(
                    convert_result_bulk(raw_umagoto), sort_columns=["確定着順", "馬番"]
                )

        if DataKind.PAYOFF in target_kinds:
            raw_haraimodoshi = self._race_getter.get_haraimodoshi(
                race_code=unique_race_codes, convert_codes=False
            )
            result[DataKind.PAYOFF] = _split_per_race(convert_payoff_bulk(raw_haraimodoshi))

        if DataKind.WIN_SHOW_ODDS in target_kinds:
            raw_tansho = self._odds_getter.get_odds1_tansho(
                race_code=unique_race_codes, convert_codes=False
            )
            raw_fukusho = self._odds_getter.get_odds1_fukusho(
                race_code=unique_race_codes, convert_codes=False
            )
            result[DataKind.WIN_SHOW_ODDS] = _convert_odds_per_race(raw_tansho, raw_fukusho)
        self._logger.debug(
            "レース単位データの一括取得が完了: 指定=%d件, 種別=%s",
            len(unique_race_codes),
            {kind: len(by_race_code) for kind, by_race_code in result.items()},
        )
        return result

    def get_entry(self, race_code: str) -> pd.DataFrame:
        """出馬表を取得する.

        RaceGetter.get_umagoto_race_joho()で馬毎レース情報を取得し、
        統一スキーマに変換する。

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: 出馬表（出走頭数行、HORSE_RACE_INFO_COLUMNSのカラム, 馬番順）
        """
        self._logger.debug("RaceGetterで出馬表を取得: race_code=%s", race_code)
        raw = self._race_getter.get_umagoto_race_joho(race_code=race_code, convert_codes=False)
        df = convert_entry(raw)
        df = df.sort_values("馬番").reset_index(drop=True)
        self._logger.debug("出馬表の取得が完了: race_code=%s", race_code)
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
        self._logger.debug("OddsGetterで単複オッズを取得: race_code=%s", race_code)
        raw_tansho = self._odds_getter.get_odds1_tansho(race_code=race_code, convert_codes=False)
        raw_fukusho = self._odds_getter.get_odds1_fukusho(race_code=race_code, convert_codes=False)
        df = convert_win_show_odds(raw_tansho, raw_fukusho)
        df = df.sort_values("馬番").reset_index(drop=True)
        self._logger.debug("単複オッズの取得が完了: race_code=%s", race_code)
        return df

    def get_win_show_votes(self, race_code: str) -> pd.DataFrame:
        """単勝・複勝の票数を取得する.

        HyosuGetter.get_hyosu1_tansho() / get_hyosu1_fukusho() で馬番ごとの票数を、
        OddsGetter.get_odds1() で票数合計を取得し、マージして統一スキーマに変換する。

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: 単複票数（出走頭数行、WIN_SHOW_VOTES_COLUMNSのカラム, 馬番順）

        Raises:
            DataNotFoundError: 該当レースの票数（単勝・複勝・合計のいずれか）が存在しない、
                票数合計が1行でない、または登録済みの馬番が1頭も無い場合
        """
        self._logger.debug("HyosuGetterで単複票数を取得: race_code=%s", race_code)
        raw_tansho = self._hyosu_getter.get_hyosu1_tansho(race_code=race_code, convert_codes=False)
        raw_fukusho = self._hyosu_getter.get_hyosu1_fukusho(
            race_code=race_code, convert_codes=False
        )
        raw_odds1 = self._odds_getter.get_odds1(race_code=race_code, convert_codes=False)
        if len(raw_tansho) == 0 or len(raw_fukusho) == 0 or len(raw_odds1) == 0:
            message = (
                f"票数が存在しません: race_code={race_code}（単勝: {len(raw_tansho)}行, "
                f"複勝: {len(raw_fukusho)}行, 合計: {len(raw_odds1)}行）"
            )
            self._logger.error(message)
            raise DataNotFoundError(message)
        if len(raw_odds1) != 1:
            message = (
                f"票数合計は1行である必要があります: race_code={race_code}, rows={len(raw_odds1)}"
            )
            self._logger.error(message)
            raise DataNotFoundError(message)
        df = convert_win_show_votes(raw_tansho, raw_fukusho, raw_odds1)
        if df.empty:
            message = f"登録済みの票数が存在しません: race_code={race_code}"
            self._logger.error(message)
            raise DataNotFoundError(message)
        self._logger.debug("単複票数の取得が完了: race_code=%s", race_code)
        return df

    def get_result(self, race_code: str) -> pd.DataFrame:
        """レース結果（馬毎）を取得する.

        RaceGetter.get_umagoto_race_joho()で馬毎レース情報を取得し、
        get_entry用の変換に加えて走破タイムの変換を行う。

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: レース結果（出走頭数行、HORSE_RACE_INFO_COLUMNSのカラム,
                確定着順順・同着は馬番昇順）
        """
        self._logger.debug("RaceGetterでレース結果を取得: race_code=%s", race_code)
        raw = self._race_getter.get_umagoto_race_joho(race_code=race_code, convert_codes=False)
        df = convert_result(raw)
        # DBの行順は不定のため、同着時も順序が決定的になるよう馬番を第2キーにする
        df = df.sort_values(["確定着順", "馬番"]).reset_index(drop=True)
        self._logger.debug("レース結果の取得が完了: race_code=%s", race_code)
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
        self._logger.debug("RaceGetterでレース結果情報を取得: race_code=%s", race_code)
        raw = self._race_getter.get_race_shosai(race_code=race_code, convert_codes=False)
        result = convert_race_result_info(raw)
        self._logger.debug("レース結果情報の取得が完了: race_code=%s", race_code)
        return result

    def get_payoff(self, race_code: str) -> pd.DataFrame:
        """払戻情報を取得する.

        RaceGetter.get_haraimodoshi()で払戻情報を取得し、統一スキーマに変換する。

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: 払戻情報（1行、PAYOFF_COLUMNSのカラム）
        """
        self._logger.debug("RaceGetterで払戻情報を取得: race_code=%s", race_code)
        raw = self._race_getter.get_haraimodoshi(race_code=race_code, convert_codes=False)
        result = convert_payoff(raw)
        self._logger.debug("払戻情報の取得が完了: race_code=%s", race_code)
        return result

    def get_past_performances(self, horse_id: str) -> pd.DataFrame:
        """過去成績（馬柱）を取得する.

        RaceGetter.get_umagoto_race_joho()を馬ID（血統登録番号）指定で取得し、
        統一スキーマに変換する。

        Args:
            horse_id (str): 馬ID（血統登録番号）

        Returns:
            pd.DataFrame: 過去成績（出走回数行、HORSE_RACE_INFO_COLUMNSのカラム）
        """
        self._logger.debug("RaceGetterで過去成績を取得: horse_id=%s", horse_id)
        raw = self._race_getter.get_umagoto_race_joho(
            ketto_toroku_bango=horse_id, convert_codes=False
        )
        df = convert_past_performances(raw)
        df = df.sort_values("レースコード", ascending=False).reset_index(drop=True)
        self._logger.debug("過去成績の取得が完了: horse_id=%s", horse_id)
        return df

    def get_past_performances_bulk(self, horse_ids: list[str]) -> dict[str, pd.DataFrame]:
        """複数馬の過去成績（馬柱）をまとめて取得する.

        `umagoto_race_joho` の主キーは (race_code, ketto_toroku_bango) であり、
        血統登録番号だけで絞り込むと主キーの前方一致にならず、PostgreSQLがインデックスを
        頭から走査する（1頭あたり約276ms）。IN句でまとめると走査が1回で済み、
        16頭ぶんで実測8.8倍になる。

        Args:
            horse_ids (list[str]): 馬ID（血統登録番号）のリスト

        Returns:
            dict[str, pd.DataFrame]: 馬ID → 過去成績（レースコード降順）。
                指定した馬IDは必ずキーに含まれる。出走歴が無い馬には
                1件取得と同じカラム構成・dtypeの空DataFrameを返す
        """
        unique_horse_ids = list(dict.fromkeys(horse_ids))
        empty = convert_past_performances(pd.DataFrame())
        if not unique_horse_ids:
            self._logger.debug("取得対象が無いためクエリを発行しません")
            return {}

        self._logger.debug("RaceGetterで過去成績を一括取得: 頭数=%d", len(unique_horse_ids))
        raw = self._race_getter.get_umagoto_race_joho(
            ketto_toroku_bango=unique_horse_ids, convert_codes=False
        )
        converted = convert_past_performances_bulk(raw)
        # 出走歴が無い馬にはそれぞれ独立した空のDataFrameを持たせる。同じインスタンスを
        # 共有すると、呼び出し側が一方を書き換えたときに他方まで変わる
        result = {horse_id: empty.copy() for horse_id in unique_horse_ids}
        if not converted.empty:
            for horse_id, horse_df in converted.groupby("血統登録番号", sort=False):
                key = str(horse_id)
                if key not in result:
                    continue
                result[key] = horse_df.sort_values("レースコード", ascending=False).reset_index(
                    drop=True
                )
        self._logger.debug("過去成績の一括取得が完了: 頭数=%d", len(result))
        return result

    def get_horse_master(self, horse_id: str) -> pd.DataFrame:
        """競走馬マスタを取得する.

        MasterGetter.get_kyosoba_master2()で競走馬マスタを取得し、
        統一スキーマに変換する。

        Args:
            horse_id (str): 馬ID（血統登録番号）

        Returns:
            pd.DataFrame: 競走馬マスタ情報（1行、HORSE_MASTER_COLUMNSのカラム）
        """
        self._logger.debug("MasterGetterで競走馬情報を取得: horse_id=%s", horse_id)
        raw = self._master_getter.get_kyosoba_master2(
            ketto_toroku_bango=horse_id, convert_codes=False
        )
        result = convert_horse_master(raw)
        self._logger.debug("競走馬情報の取得が完了: horse_id=%s", horse_id)
        return result

    def get_horse_master_bulk(self, horse_ids: list[str]) -> dict[str, pd.DataFrame]:
        """複数馬の競走馬マスタをまとめて取得する.

        `kyosoba_master2` は血統登録番号が主キーのためクエリ自体は速いが、頭数ぶんの
        往復と変換（228カラムの型変換を1頭につき2回）が積み上がる。1回にまとめる。

        Args:
            horse_ids (list[str]): 馬ID（血統登録番号）のリスト

        Returns:
            dict[str, pd.DataFrame]: 馬ID → 競走馬マスタ（1行）。
                指定した馬IDは必ずキーに含まれる。マスタに存在しない馬には
                1件取得と同じカラム構成・dtypeの空DataFrameを返す
        """
        unique_horse_ids = list(dict.fromkeys(horse_ids))
        if not unique_horse_ids:
            self._logger.debug("取得対象が無いためクエリを発行しません")
            return {}

        self._logger.debug("MasterGetterで競走馬情報を一括取得: 頭数=%d", len(unique_horse_ids))
        raw = self._master_getter.get_kyosoba_master2(
            ketto_toroku_bango=unique_horse_ids, convert_codes=False
        )
        converted = convert_horse_master_bulk(raw)
        empty = convert_horse_master(pd.DataFrame())
        # マスタに存在しない馬にはそれぞれ独立した空のDataFrameを持たせる。同じ
        # インスタンスを共有すると、呼び出し側が一方を書き換えたときに他方まで変わる
        result = {horse_id: empty.copy() for horse_id in unique_horse_ids}
        if not converted.empty:
            for horse_id, horse_df in converted.groupby("血統登録番号", sort=False):
                key = str(horse_id)
                if key not in result:
                    continue
                # 1件版は raw.iloc[0] の1行だけを返す。血統登録番号はkyosoba_master2の
                # 主キーなので同じ馬が複数行になることはないが、なった場合も1件版と
                # 同じ結果にするため先頭行だけを採る
                result[key] = horse_df.head(1).reset_index(drop=True)
        self._logger.debug("競走馬情報の一括取得が完了: 頭数=%d", len(result))
        return result

    def get_chakudosu(self, race_code: str) -> pd.DataFrame:
        """出走別着度数を取得する.

        ShussobetsuGetterで競馬場別・距離別・馬場別の3テーブルを取得し、
        血統登録番号で結合して統一スキーマに変換する。

        Args:
            race_code (str): 16桁レースコード

        Returns:
            pd.DataFrame: 出走別着度数（出走頭数行、CHAKUDOSU_COLUMNSのカラム、
                血統登録番号昇順）
        """
        self._logger.debug("ShussobetsuGetterで出走別着度数を取得: race_code=%s", race_code)
        raw_keibajo = self._shussobetsu_getter.get_shussobetsu_keibajo(
            race_code=race_code, convert_codes=False
        )
        raw_kyori = self._shussobetsu_getter.get_shussobetsu_kyori(
            race_code=race_code, convert_codes=False
        )
        raw_baba = self._shussobetsu_getter.get_shussobetsu_baba(
            race_code=race_code, convert_codes=False
        )
        df = convert_chakudosu(raw_keibajo, raw_kyori, raw_baba)
        df = df.sort_values("血統登録番号").reset_index(drop=True)
        self._logger.debug("出走別着度数の取得が完了: race_code=%s", race_code)
        return df

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
        self._logger.debug(
            "RaceGetterで開催スケジュールを取得: start_date=%s, end_date=%s", start_date, end_date
        )
        raw = self._race_getter.get_kaisai_schedule(
            start_date=date.fromisoformat(start_date),
            end_date=date.fromisoformat(end_date),
            convert_codes=False,
        )
        result = convert_schedule(raw)
        self._logger.debug(
            "開催スケジュールの取得が完了: start_date=%s, end_date=%s", start_date, end_date
        )
        return result


def _split_per_race(
    converted: pd.DataFrame, sort_columns: list[str] | None = None
) -> dict[str, pd.DataFrame]:
    """一括変換した結果をレースコードで分割する.

    変換をレースごとに行うと、カラム数と呼び出し回数に比例する型変換
    （`apply_types`）がレース数だけ繰り返される。まとめて変換してから分割する。

    indexは1件取得と同じく通し番号へ戻す。呼び出し側が1件取得と同じ形を期待するため。

    Args:
        converted (pd.DataFrame): 一括変換の結果（レースコードカラムを含む）
        sort_columns (list[str] | None): レース内で並べ替えるカラム。1件取得と同じ
            並びにするために使う

    Returns:
        dict[str, pd.DataFrame]: レースコード → 変換後のDataFrame
    """
    if converted.empty:
        return {}
    per_race: dict[str, pd.DataFrame] = {}
    for race_code, race_df in converted.groupby("レースコード", sort=False):
        if sort_columns:
            race_df = race_df.sort_values(sort_columns)
        per_race[str(race_code)] = race_df.reset_index(drop=True)
    return per_race


def _convert_odds_per_race(
    raw_tansho: pd.DataFrame, raw_fukusho: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    """単勝・複勝オッズをレースコードでグループ化して変換する.

    単勝と複勝を馬番で結合するため、レース単位で組にしてから変換する。
    片方にしか存在しないレースコードも対象にする（convert_win_show_oddsが
    片方が空の場合に対応しているため）。

    Args:
        raw_tansho (pd.DataFrame): 単勝オッズの取得結果（複数レース分）
        raw_fukusho (pd.DataFrame): 複勝オッズの取得結果（複数レース分）

    Returns:
        dict[str, pd.DataFrame]: レースコード → 変換後のDataFrame
    """
    tansho_by_race = (
        {str(code): df for code, df in raw_tansho.groupby("race_code")}
        if not raw_tansho.empty
        else {}
    )
    fukusho_by_race = (
        {str(code): df for code, df in raw_fukusho.groupby("race_code")}
        if not raw_fukusho.empty
        else {}
    )

    race_codes = dict.fromkeys([*tansho_by_race, *fukusho_by_race])
    empty = pd.DataFrame()
    return {
        race_code: convert_win_show_odds(
            tansho_by_race.get(race_code, empty).reset_index(drop=True),
            fukusho_by_race.get(race_code, empty).reset_index(drop=True),
        )
        for race_code in race_codes
    }
