"""CourseDaysCacheの単体テスト.

コース日数は「競馬場コード・開催日・コース区分」で決まり、レース単位の情報ではない。
同じ開催日のレースを繰り返し処理したときに再計算しないことを検証する。
"""

from datetime import date, timedelta

import pandas as pd
import pytest

from keiba_data_interface.course_days import (
    COURSE_DAYS_COLUMNS,
    CourseDaysCache,
    calc_course_days,
)

from .conftest import (
    KEIBAJO_CODE,
    MockProvider,
    RaceDay,
    build_race_basic_info,
    dirt_only_day_races,
    turf_day_races,
)

_TARGET_DATE = date(2025, 6, 8)


def _make_provider(race_day_count: int = 3, supports_bulk: bool = True) -> MockProvider:
    """同一コースの開催日が続くMockProviderを生成する.

    Args:
        race_day_count (int): 過去の開催日数
        supports_bulk (bool): 一括取得に対応しているか

    Returns:
        MockProvider: テスト用Provider
    """
    race_days = [
        RaceDay(_TARGET_DATE - timedelta(days=7 * week), 1, week, turf_day_races("A"))
        for week in range(1, race_day_count + 1)
    ]
    return MockProvider(race_days, supports_bulk=supports_bulk)


# 正常系
def test_second_call_does_not_query() -> None:
    """同一の競馬場・開催日・コース区分に対する2回目の呼び出しで問い合わせが発生しない."""
    provider = _make_provider()
    cache = CourseDaysCache()
    race_basic_info = build_race_basic_info(_TARGET_DATE, "芝", "A")

    calc_course_days(race_basic_info, provider, cache=cache)
    first_call_count = len(provider.get_race_basic_info_bulk_calls)
    calc_course_days(race_basic_info, provider, cache=cache)

    assert first_call_count > 0
    assert len(provider.get_race_basic_info_bulk_calls) == first_call_count


def test_cached_result_matches_uncached_result() -> None:
    """キャッシュの有無で戻り値が完全に一致する."""
    race_basic_info = build_race_basic_info(_TARGET_DATE, "芝", "A")
    cache = CourseDaysCache()

    uncached = calc_course_days(race_basic_info, _make_provider())
    calc_course_days(race_basic_info, _make_provider(), cache=cache)
    cached = calc_course_days(race_basic_info, _make_provider(), cache=cache)

    pd.testing.assert_frame_equal(cached, uncached)


def test_cached_result_keeps_other_columns() -> None:
    """キャッシュから返す場合も、渡されたレース基本情報の他のカラムが保持される.

    キャッシュするのは計算した4カラムの値だけで、DataFrame全体ではない。
    """
    provider = _make_provider()
    cache = CourseDaysCache()
    first = build_race_basic_info(_TARGET_DATE, "芝", "A")
    first["レースコード"] = "2025060805030111"
    second = build_race_basic_info(_TARGET_DATE, "芝", "A")
    second["レースコード"] = "2025060805030112"

    calc_course_days(first, provider, cache=cache)
    result = calc_course_days(second, provider, cache=cache)

    assert result["レースコード"].iloc[0] == "2025060805030112"


def test_course_kubun_of_day_is_queried_once_per_day() -> None:
    """同一開催日のコース区分の判定が1回だけ行われる."""
    provider = _make_provider(race_day_count=3)
    cache = CourseDaysCache()

    # コース区分が異なる2レースを処理する。開催日の判定はコース区分に依存しないため
    # 2回目は再問い合わせしない
    calc_course_days(build_race_basic_info(_TARGET_DATE, "芝", "A"), provider, cache=cache)
    first_call_count = len(provider.get_race_basic_info_bulk_calls)
    calc_course_days(build_race_basic_info(_TARGET_DATE, "芝", "B"), provider, cache=cache)

    assert len(provider.get_race_basic_info_bulk_calls) == first_call_count


def test_schedule_is_queried_once_per_period() -> None:
    """同一期間の開催スケジュールの取得が1回だけ行われる."""
    provider = _make_provider()
    cache = CourseDaysCache()
    schedule_calls: list[tuple[str, str]] = []
    original_get_schedule = provider.get_schedule

    def counted_get_schedule(start_date: str, end_date: str) -> pd.DataFrame:
        schedule_calls.append((start_date, end_date))
        return original_get_schedule(start_date, end_date)

    provider.get_schedule = counted_get_schedule  # type: ignore[method-assign]

    calc_course_days(build_race_basic_info(_TARGET_DATE, "芝", "A"), provider, cache=cache)
    first_call_count = len(schedule_calls)
    calc_course_days(build_race_basic_info(_TARGET_DATE, "芝", "A"), provider, cache=cache)

    assert first_call_count > 0
    assert len(schedule_calls) == first_call_count


def test_clear_makes_next_call_query_again() -> None:
    """clearの後は再び問い合わせが発生する."""
    provider = _make_provider()
    cache = CourseDaysCache()
    race_basic_info = build_race_basic_info(_TARGET_DATE, "芝", "A")

    calc_course_days(race_basic_info, provider, cache=cache)
    first_call_count = len(provider.get_race_basic_info_bulk_calls)
    cache.clear()
    calc_course_days(race_basic_info, provider, cache=cache)

    assert len(provider.get_race_basic_info_bulk_calls) > first_call_count


# 準正常系
def test_baseline_counts_past_same_course_days() -> None:
    """比較の基準として、同一コースの過去開催日が数えられることを確認する."""
    provider = _make_provider(race_day_count=3)
    cache = CourseDaysCache()

    result = calc_course_days(build_race_basic_info(_TARGET_DATE, "芝", "A"), provider, cache=cache)

    assert result["芝コース日目"].iloc[0] == 4


@pytest.mark.parametrize(
    "keibajo_code, race_date, course_kubun",
    [
        ("06", _TARGET_DATE, "A"),
        (KEIBAJO_CODE, _TARGET_DATE + timedelta(days=7), "A"),
        (KEIBAJO_CODE, _TARGET_DATE, "B"),
    ],
)
def test_different_key_is_calculated_separately(
    keibajo_code: str, race_date: date, course_kubun: str
) -> None:
    """キーのいずれかが異なれば別々に計算される.

    キャッシュのキーは競馬場コード・開催年・開催月日・コース区分である。
    どれか1つでも異なれば、先に計算した結果を再利用しない。

    クエリの発行回数ではなく計算結果で検証する。コース区分の判定と開催スケジュールは
    別のキーでキャッシュしており、コース区分だけが異なる場合はクエリが増えないため。
    """
    provider = _make_provider(race_day_count=3)
    cache = CourseDaysCache()

    baseline = calc_course_days(
        build_race_basic_info(_TARGET_DATE, "芝", "A"), provider, cache=cache
    )
    other = calc_course_days(
        build_race_basic_info(race_date, "芝", course_kubun, keibajo_code),
        provider,
        cache=cache,
    )

    assert baseline["芝コース日目"].iloc[0] == 4
    assert other["芝コース日目"].iloc[0] == 1


@pytest.mark.parametrize(
    "shiba_da, course_kubun",
    [
        ("ダ", "A"),
        ("芝", None),
    ],
)
def test_non_target_race_returns_nan_with_cache(
    shiba_da: str, course_kubun: str | None
) -> None:
    """芝レースでない場合やコース区分が不明な場合は、キャッシュを渡しても4カラムがNaNのまま返る."""
    provider = MockProvider([])
    cache = CourseDaysCache()
    race_basic_info = build_race_basic_info(_TARGET_DATE, shiba_da, course_kubun)

    result = calc_course_days(race_basic_info, provider, cache=cache)

    for column in COURSE_DAYS_COLUMNS:
        assert pd.isna(result[column].iloc[0])


def test_dirt_only_day_is_cached_as_none() -> None:
    """芝レースが存在しない開催日の判定結果もキャッシュされる."""
    provider = MockProvider(
        [RaceDay(_TARGET_DATE - timedelta(days=7), 1, 1, dirt_only_day_races())]
    )
    cache = CourseDaysCache()

    calc_course_days(build_race_basic_info(_TARGET_DATE, "芝", "A"), provider, cache=cache)
    first_call_count = len(provider.get_race_basic_info_bulk_calls)
    calc_course_days(build_race_basic_info(_TARGET_DATE, "芝", "B"), provider, cache=cache)

    assert len(provider.get_race_basic_info_bulk_calls) == first_call_count
