"""芝コース日数情報の計算モジュール

レース基本情報の芝コース日目・芝コース初日・芝コース経過日数・芝コース週目を、
Providerによる過去レースの遡及取得から計算する
"""

import logging
from datetime import date, timedelta
from typing import Any

import pandas as pd

from keiba_data_interface.exceptions import KeibaDataInterfaceError
from keiba_data_interface.protocols import DataProvider

# 芝コース日数情報のカラム名リスト
COURSE_DAYS_COLUMNS: list[str] = [
    "芝コース日目",
    "芝コース初日",
    "芝コース経過日数",
    "芝コース週目",
]

# 同一コースの開催間隔がこの日数以上空いた場合、コース使用がリセットされたとみなす
_RESET_GAP_DAYS = 14
# 開催間隔がこの日数以下なら同一週の開催とみなす
_SAME_WEEK_GAP_DAYS = 2
# 過去レースの遡及上限日数
_MAX_LOOKBACK_DAYS = 365
# get_scheduleで一度に取得する日数
_SCHEDULE_WINDOW_DAYS = 14
# 1開催日の最大レース番号
_MAX_RACE_NUM = 12


def calc_course_days(
    race_basic_info: pd.DataFrame,
    provider: DataProvider,
    logger: logging.Logger | None = None,
) -> pd.DataFrame:
    """芝コース日数4カラムを計算して埋めたDataFrameを返す

    対象レースと同一競馬場・同一コース区分の過去開催日をProviderから遡及取得し、
    芝コース日目・芝コース初日・芝コース経過日数・芝コース週目を計算する。
    芝レースでない場合やコース区分が不明な場合は4カラムをNaNのまま返す。

    Args:
        race_basic_info (pd.DataFrame): レース基本情報（1行、RACE_BASIC_INFO_COLUMNSのカラム）
        provider (DataProvider): 過去レース取得に使用するProvider
        logger (logging.Logger | None): ロガーインスタンス

    Returns:
        pd.DataFrame: 芝コース日数4カラムを設定したレース基本情報

    Raises:
        KeibaDataInterfaceError: 過去レースの遡及が上限日数を超えた場合
    """
    logger = logger or logging.getLogger(__name__)
    df = race_basic_info.copy()
    row = df.iloc[0]
    if row["芝ダ"] != "芝" or pd.isna(row["コース区分"]):
        logger.debug(
            "芝レースでないかコース区分が不明のためコース日数を計算しません: レースコード=%s",
            row["レースコード"],
        )
        return df

    race_date = _to_date(str(row["開催年"]), str(row["開催月日"]))
    keibajo_code = str(row["競馬場コード"])
    course_kubun = str(row["コース区分"])
    logger.debug(
        "コース日数の計算を開始します: 競馬場コード=%s, コース区分=%s, 開催日=%s",
        keibajo_code,
        course_kubun,
        race_date,
    )
    past_days = _collect_same_course_days(provider, keibajo_code, course_kubun, race_date, logger)

    # 対象レース日を含めた同一コースの開催日リスト（昇順）
    course_day_list = past_days + [race_date]
    first_date = course_day_list[0]
    course_week = 1
    for prev_day, cur_day in zip(course_day_list, course_day_list[1:]):
        if (cur_day - prev_day).days > _SAME_WEEK_GAP_DAYS:
            course_week += 1

    df["芝コース日目"] = pd.array([len(course_day_list)], dtype="Int64")
    df["芝コース初日"] = first_date.strftime("%Y%m%d")
    df["芝コース経過日数"] = pd.array([(race_date - first_date).days + 1], dtype="Int64")
    df["芝コース週目"] = pd.array([course_week], dtype="Int64")
    logger.debug(
        "コース日数の計算が完了しました: 芝コース日目=%d, 芝コース週目=%d",
        len(course_day_list),
        course_week,
    )
    return df


def _collect_same_course_days(
    provider: DataProvider,
    keibajo_code: str,
    course_kubun: str,
    race_date: date,
    logger: logging.Logger,
) -> list[date]:
    """対象レース日より前の同一競馬場・同一コース区分の開催日リストを昇順で返す

    対象レース日から過去に向かって開催スケジュールを取得し、同一コース区分の開催日を収集する。
    直近の同一コース開催日との間隔が_RESET_GAP_DAYS以上空いた時点で遡及を終了する。

    Args:
        provider (DataProvider): 過去レース取得に使用するProvider
        keibajo_code (str): 競馬場コード（2桁）
        course_kubun (str): コース区分（A〜E）
        race_date (date): 対象レースの開催日
        logger (logging.Logger): ロガーインスタンス

    Returns:
        list[date]: 同一コース区分の開催日リスト（昇順）

    Raises:
        KeibaDataInterfaceError: 遡及が_MAX_LOOKBACK_DAYSを超えた場合
    """
    collected: list[date] = []
    # 直近の同一コース開催日（遡及終了判定の基準）
    latest = race_date
    window_end = race_date - timedelta(days=1)
    while (latest - window_end).days < _RESET_GAP_DAYS:
        window_start = window_end - timedelta(days=_SCHEDULE_WINDOW_DAYS - 1)
        if (race_date - window_start).days > _MAX_LOOKBACK_DAYS:
            logger.error(
                "コース日数計算の遡及が上限を超えました: 競馬場コード=%s, 開催日=%s",
                keibajo_code,
                race_date,
            )
            raise KeibaDataInterfaceError(
                f"コース日数計算の遡及が上限（{_MAX_LOOKBACK_DAYS}日）を超えました: "
                f"競馬場コード={keibajo_code}, 開催日={race_date}"
            )
        schedule_df = provider.get_schedule(window_start.isoformat(), window_end.isoformat())
        venue_days_df = _extract_venue_days(schedule_df, keibajo_code)
        for _, schedule_row in venue_days_df.iterrows():
            day = _to_date(str(schedule_row["開催年"]), str(schedule_row["開催月日"]))
            if (latest - day).days >= _RESET_GAP_DAYS:
                return sorted(collected)
            day_course_kubun = _get_course_kubun_of_day(provider, schedule_row, logger)
            if day_course_kubun == course_kubun:
                collected.append(day)
                latest = day
        window_end = window_start - timedelta(days=1)
    return sorted(collected)


def _get_course_kubun_of_day(
    provider: DataProvider, schedule_row: "pd.Series[Any]", logger: logging.Logger
) -> str | None:
    """開催日のコース区分を取得する

    レース番号1〜12の順にレース基本情報を取得し、最初に見つかった芝レースの
    コース区分を返す。芝コースのコース区分は競馬場・開催日単位で共通であるため、
    1レース分の情報で判定できる。
    開催日に存在しないレース番号（ValueError）は読み飛ばす。

    Args:
        provider (DataProvider): 過去レース取得に使用するProvider
        schedule_row (pd.Series): 開催スケジュールの1行
        logger (logging.Logger): ロガーインスタンス

    Returns:
        str | None: コース区分（A〜E）。芝レースが存在しない開催日はNone
    """
    year = str(schedule_row["開催年"])
    monthday = str(schedule_row["開催月日"])
    keibajo_code = str(schedule_row["競馬場コード"])
    kai = int(schedule_row["開催回"])
    nichime = int(schedule_row["開催日目"])
    for race_num in range(1, _MAX_RACE_NUM + 1):
        race_code = f"{year}{monthday}{keibajo_code}{kai:02d}{nichime:02d}{race_num:02d}"
        try:
            race_row = provider.get_race_basic_info(race_code).iloc[0]
        except ValueError as exc:
            logger.debug(
                "レース基本情報を取得できなかったため読み飛ばします: race_code=%s, %s",
                race_code,
                exc,
            )
            continue
        if race_row["芝ダ"] == "芝" and not pd.isna(race_row["コース区分"]):
            return str(race_row["コース区分"])
    logger.debug("芝レースが存在しない開催日です: 開催年=%s, 開催月日=%s", year, monthday)
    return None


def _extract_venue_days(schedule_df: pd.DataFrame, keibajo_code: str) -> pd.DataFrame:
    """開催スケジュールから指定競馬場の開催日行を新しい順に取り出す

    Args:
        schedule_df (pd.DataFrame): 開催スケジュールのDataFrame
        keibajo_code (str): 競馬場コード（2桁）

    Returns:
        pd.DataFrame: 指定競馬場の開催日行（開催日の降順、開催日単位で重複排除）
    """
    df = schedule_df[schedule_df["競馬場コード"] == keibajo_code]
    df = df.drop_duplicates(subset=["開催年", "開催月日"])
    df = df.sort_values(["開催年", "開催月日"], ascending=False)
    return df.reset_index(drop=True)


def _to_date(year: str, monthday: str) -> date:
    """開催年と開催月日からdate型を生成する

    Args:
        year (str): 開催年（yyyy形式4桁）
        monthday (str): 開催月日（mmdd形式4桁）

    Returns:
        date: 開催日
    """
    return date(int(year), int(monthday[:2]), int(monthday[2:]))
