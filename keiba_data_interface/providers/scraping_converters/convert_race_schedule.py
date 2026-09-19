"""get_race_schedule用の変換関数."""

import logging

import pandas as pd

from keiba_data_interface.exceptions import RaceCodeError
from keiba_data_interface.schema.columns import RACE_SCHEDULE_COLUMNS
from keiba_data_interface.schema.types import RACE_SCHEDULE_TYPES
from keiba_data_interface.utils.dataframe import apply_types, ensure_columns

# レースID（netkeiba式）の桁数
_RACE_ID_LENGTH = 12


def convert_race_schedule(
    raw: pd.DataFrame, date: str, logger: logging.Logger | None = None
) -> pd.DataFrame:
    """RaceScheduleScraper.get_race_schedule()の出力をレース時刻表の統一スキーマに変換する.

    レースID（年(4)+競馬場(2)+回(2)+日目(2)+R(2)）と日付からレースコード
    （年(4)+月日(4)+競馬場(2)+回(2)+日目(2)+R(2)）を組み立てる。
    発走時刻が空のレースは欠損にする。

    Args:
        raw (pd.DataFrame): RaceScheduleScraper.get_race_schedule()の出力
        date (str): 対象日（YYYYMMDD）
        logger (logging.Logger | None): ロガー。省略時は __name__ ベースのロガーを使用

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame（RACE_SCHEDULE_COLUMNSのカラム、
            レースコード昇順）

    Raises:
        RaceCodeError: レースIDが12桁の数字でない場合
    """
    logger = logger or logging.getLogger(__name__)
    if len(raw) == 0:
        return apply_types(
            ensure_columns(pd.DataFrame(), RACE_SCHEDULE_COLUMNS), RACE_SCHEDULE_TYPES
        )

    rows: list[dict[str, object]] = []
    for _, row in raw.iterrows():
        race_id = str(row["レースID"])
        if len(race_id) != _RACE_ID_LENGTH or not race_id.isdigit():
            message = (
                f"レースIDは{_RACE_ID_LENGTH}桁の数字である必要があります: "
                f"date={date}, race_id={race_id!r}"
            )
            logger.error(message)
            raise RaceCodeError(message)
        start_time = str(row["発走時刻"]).strip() if pd.notna(row["発走時刻"]) else ""
        rows.append(
            {
                "レースコード": date + race_id[4:],
                "競馬場コード": race_id[4:6],
                "レース番号": int(row["R"]),
                "発走時刻": start_time if start_time else pd.NA,
                "競走名": row["レース名"],
            }
        )

    df = pd.DataFrame(rows).sort_values("レースコード").reset_index(drop=True)
    return apply_types(ensure_columns(df, RACE_SCHEDULE_COLUMNS), RACE_SCHEDULE_TYPES)
