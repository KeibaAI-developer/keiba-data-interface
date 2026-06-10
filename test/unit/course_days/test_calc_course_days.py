"""calc_course_daysの単体テスト"""

from datetime import date, timedelta

import pandas as pd
import pytest

from keiba_data_interface.course_days import COURSE_DAYS_COLUMNS, calc_course_days
from keiba_data_interface.exceptions import KeibaDataInterfaceError

from .conftest import (
    MockProvider,
    RaceDay,
    build_race_basic_info,
    dirt_only_day_races,
    turf_day_races,
)


# 正常系
def test_calc_course_days_first_day() -> None:
    """過去に同一コースの開催がない場合は初日として計算される"""
    provider = MockProvider([])
    race_basic_info = build_race_basic_info(date(2025, 6, 8), "芝", "A")

    result = calc_course_days(race_basic_info, provider)

    assert result["芝コース日目"].iloc[0] == 1
    assert result["芝コース初日"].iloc[0] == "20250608"
    assert result["芝コース経過日数"].iloc[0] == 1
    assert result["芝コース週目"].iloc[0] == 1


def test_calc_course_days_counts_days_and_weeks() -> None:
    """連続する同一コースの開催日から日目・週目が計算される"""
    provider = MockProvider(
        [
            RaceDay(date(2025, 5, 31), 2, 1, turf_day_races("A")),
            RaceDay(date(2025, 6, 1), 2, 2, turf_day_races("A")),
            RaceDay(date(2025, 6, 7), 2, 3, turf_day_races("A")),
        ]
    )
    race_basic_info = build_race_basic_info(date(2025, 6, 8), "芝", "A")

    result = calc_course_days(race_basic_info, provider)

    assert result["芝コース日目"].iloc[0] == 4
    assert result["芝コース初日"].iloc[0] == "20250531"
    assert result["芝コース経過日数"].iloc[0] == 9
    assert result["芝コース週目"].iloc[0] == 2


def test_calc_course_days_resets_after_long_gap() -> None:
    """同一コースの開催間隔が14日以上空いた場合はリセットされる"""
    provider = MockProvider(
        [
            RaceDay(date(2025, 5, 10), 1, 7, turf_day_races("A")),
            RaceDay(date(2025, 5, 11), 1, 8, turf_day_races("A")),
            RaceDay(date(2025, 5, 31), 2, 1, turf_day_races("A")),
            RaceDay(date(2025, 6, 1), 2, 2, turf_day_races("A")),
        ]
    )
    race_basic_info = build_race_basic_info(date(2025, 6, 7), "芝", "A")

    result = calc_course_days(race_basic_info, provider)

    assert result["芝コース日目"].iloc[0] == 3
    assert result["芝コース初日"].iloc[0] == "20250531"
    assert result["芝コース経過日数"].iloc[0] == 8
    assert result["芝コース週目"].iloc[0] == 2


def test_calc_course_days_skips_different_course_days() -> None:
    """異なるコース区分の開催日は日数に数えず、セグメントも分断しない"""
    provider = MockProvider(
        [
            RaceDay(date(2025, 5, 25), 2, 1, turf_day_races("A")),
            RaceDay(date(2025, 5, 31), 2, 2, turf_day_races("B")),
            RaceDay(date(2025, 6, 1), 2, 3, turf_day_races("A")),
        ]
    )
    race_basic_info = build_race_basic_info(date(2025, 6, 8), "芝", "A")

    result = calc_course_days(race_basic_info, provider)

    assert result["芝コース日目"].iloc[0] == 3
    assert result["芝コース初日"].iloc[0] == "20250525"
    assert result["芝コース経過日数"].iloc[0] == 15
    assert result["芝コース週目"].iloc[0] == 3


def test_calc_course_days_skips_day_without_turf_race() -> None:
    """芝レースが存在しない開催日は日数に数えない"""
    provider = MockProvider(
        [
            RaceDay(date(2025, 6, 1), 2, 1, turf_day_races("A")),
            RaceDay(date(2025, 6, 7), 2, 2, dirt_only_day_races()),
        ]
    )
    race_basic_info = build_race_basic_info(date(2025, 6, 8), "芝", "A")

    result = calc_course_days(race_basic_info, provider)

    assert result["芝コース日目"].iloc[0] == 2
    assert result["芝コース初日"].iloc[0] == "20250601"
    assert result["芝コース経過日数"].iloc[0] == 8
    assert result["芝コース週目"].iloc[0] == 2


# 準正常系
@pytest.mark.parametrize(
    "shiba_da, course_kubun",
    [
        ("ダ", None),
        ("ダ", "A"),
        ("芝", None),
    ],
)
def test_calc_course_days_returns_nan_for_non_target_race(
    shiba_da: str, course_kubun: str | None
) -> None:
    """芝レースでない場合やコース区分が不明な場合は4カラムがNaNのまま返る"""
    provider = MockProvider([])
    race_basic_info = build_race_basic_info(date(2025, 6, 8), shiba_da, course_kubun)

    result = calc_course_days(race_basic_info, provider)

    for column in COURSE_DAYS_COLUMNS:
        assert pd.isna(result[column].iloc[0])


def test_calc_course_days_raises_when_lookback_exceeds_limit() -> None:
    """遡及が上限日数を超えた場合はKeibaDataInterfaceErrorが発生する"""
    target_date = date(2025, 6, 8)
    race_days = []
    # 上限を超えて毎週同一コースの開催が続くデータを生成する
    for week in range(1, 60):
        race_days.append(
            RaceDay(target_date - timedelta(days=7 * week), 1, week, turf_day_races("A"))
        )
    provider = MockProvider(race_days)
    race_basic_info = build_race_basic_info(target_date, "芝", "A")

    with pytest.raises(KeibaDataInterfaceError):
        calc_course_days(race_basic_info, provider)
