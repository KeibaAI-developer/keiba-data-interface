"""DataCacheの単体テスト."""

import datetime

import pytest

from keiba_data_interface.cache import DataCache, is_future_race_code

# 過去のレースコード（2020年）
_PAST_RACE_CODE = "2020122806050811"
_ANOTHER_PAST_RACE_CODE = "2020122806050812"


def _future_race_code() -> str:
    """未来（当日を含む）のレースコードを生成する.

    Returns:
        str: 16桁レースコード
    """
    today = datetime.date.today().strftime("%Y%m%d")
    return f"{today}06050811"


# 正常系
def test_set_and_get_returns_stored_value() -> None:
    """格納した値を取り出せる."""
    cache = DataCache()

    cache.set("race_basic_info", _PAST_RACE_CODE, "value")

    assert cache.get("race_basic_info", _PAST_RACE_CODE) == "value"


def test_get_returns_none_for_unknown_key() -> None:
    """格納していないキーではNoneを返す."""
    cache = DataCache()

    assert cache.get("race_basic_info", _PAST_RACE_CODE) is None


def test_kinds_are_separated() -> None:
    """データ種別が異なれば別の値として保持される.

    同じレースコードでも取得メソッドが違えば別の値になるため。
    """
    cache = DataCache()

    cache.set("race_basic_info", _PAST_RACE_CODE, "basic")
    cache.set("entry", _PAST_RACE_CODE, "entry")

    assert cache.get("race_basic_info", _PAST_RACE_CODE) == "basic"
    assert cache.get("entry", _PAST_RACE_CODE) == "entry"


def test_clear_removes_all_entries() -> None:
    """clearで保持している値がすべて消える."""
    cache = DataCache()
    cache.set("race_basic_info", _PAST_RACE_CODE, "value")

    cache.clear()

    assert cache.get("race_basic_info", _PAST_RACE_CODE) is None


def test_max_entries_evicts_oldest() -> None:
    """最大エントリ数を超えると最も古く使われたものから捨てられる."""
    cache = DataCache(max_entries=2)

    cache.set("race_basic_info", "2020122806050801", "a")
    cache.set("race_basic_info", "2020122806050802", "b")
    cache.set("race_basic_info", "2020122806050803", "c")

    assert cache.get("race_basic_info", "2020122806050801") is None
    assert cache.get("race_basic_info", "2020122806050802") == "b"
    assert cache.get("race_basic_info", "2020122806050803") == "c"


def test_access_makes_entry_recent() -> None:
    """取り出した値は最近使われたものとして扱われ、先に捨てられない."""
    cache = DataCache(max_entries=2)
    cache.set("race_basic_info", "2020122806050801", "a")
    cache.set("race_basic_info", "2020122806050802", "b")

    cache.get("race_basic_info", "2020122806050801")
    cache.set("race_basic_info", "2020122806050803", "c")

    assert cache.get("race_basic_info", "2020122806050801") == "a"
    assert cache.get("race_basic_info", "2020122806050802") is None


def test_max_entries_counts_per_kind() -> None:
    """最大エントリ数はデータ種別ごとに独立して数える."""
    cache = DataCache(max_entries=1)

    cache.set("race_basic_info", _PAST_RACE_CODE, "basic")
    cache.set("entry", _PAST_RACE_CODE, "entry")

    assert cache.get("race_basic_info", _PAST_RACE_CODE) == "basic"
    assert cache.get("entry", _PAST_RACE_CODE) == "entry"


# 準正常系
def test_future_race_is_not_stored() -> None:
    """未来レースは格納されない.

    単勝オッズは発走直前まで変動するため、キャッシュすると古い値を返す。
    """
    cache = DataCache()

    cache.set("race_basic_info", _future_race_code(), "value")

    assert cache.get("race_basic_info", _future_race_code()) is None


@pytest.mark.parametrize(
    "key, expected",
    [
        (_PAST_RACE_CODE, False),
        ("2020104614", False),
        ("abcdefghijklmnop", False),
        ("", False),
    ],
)
def test_is_future_race_code_for_non_future_keys(key: str, expected: bool) -> None:
    """過去レースコードやレースコード以外のキーは未来レースと判定されない.

    馬IDなどレースコード以外のキーも同じキャッシュへ入るため。
    """
    assert is_future_race_code(key) is expected


def test_is_future_race_code_includes_today() -> None:
    """当日のレースコードは未来レースと判定される.

    発走前のレースを過去として扱わないため。
    """
    assert is_future_race_code(_future_race_code()) is True


@pytest.mark.parametrize("max_entries", [0, -1])
def test_invalid_max_entries_raises(max_entries: int) -> None:
    """max_entriesが1未満の場合にValueErrorが発生する.

    負数を許すと退避のループが空のキャッシュに対して実行され、KeyErrorになる。
    """
    with pytest.raises(ValueError, match="max_entriesは1以上"):
        DataCache(max_entries=max_entries)
