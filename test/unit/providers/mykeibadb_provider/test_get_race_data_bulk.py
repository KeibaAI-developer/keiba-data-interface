"""MykeibaDBProvider.get_race_data_bulk関数のテスト.

プリフェッチ層が使う一括取得。指定された種別に必要なテーブルだけを取得することを
検証する。取得しない種別は変換も行われないため、変換のコストも避けられる。
"""

from unittest.mock import MagicMock

import pandas as pd
import pytest

from keiba_data_interface.cache import RACE_DATA_KINDS, DataKind
from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider

_RACE_CODES = ["2025050206050811", "2025050206050812"]


@pytest.fixture
def empty_getters(
    mock_race_getter: MagicMock, mock_odds_getter: MagicMock
) -> tuple[MagicMock, MagicMock]:
    """空のDataFrameを返すgetterのモック.

    テーブルが取得されたかどうかだけを見るため、中身は空でよい。
    """
    for method in ("get_race_shosai", "get_umagoto_race_joho", "get_haraimodoshi"):
        getattr(mock_race_getter, method).return_value = pd.DataFrame()
    for method in ("get_odds1_tansho", "get_odds1_fukusho"):
        getattr(mock_odds_getter, method).return_value = pd.DataFrame()
    return mock_race_getter, mock_odds_getter


# 正常系
def test_omitting_kinds_fetches_all_tables(
    provider: MykeibaDBProvider, empty_getters: tuple[MagicMock, MagicMock]
) -> None:
    """kindsを省略すると全テーブルを取得する（現状維持）."""
    race_getter, odds_getter = empty_getters

    provider.get_race_data_bulk(_RACE_CODES)

    race_getter.get_race_shosai.assert_called_once()
    race_getter.get_umagoto_race_joho.assert_called_once()
    race_getter.get_haraimodoshi.assert_called_once()
    odds_getter.get_odds1_tansho.assert_called_once()
    odds_getter.get_odds1_fukusho.assert_called_once()


def test_excluding_payoff_skips_haraimodoshi(
    provider: MykeibaDBProvider, empty_getters: tuple[MagicMock, MagicMock]
) -> None:
    """払戻情報を除くとHARAIMODOSHIを取得しない.

    convert_payoffは1回あたりのコストが大きく、使わないなら取得しないほうがよい。
    """
    race_getter, _ = empty_getters
    kinds = [kind for kind in RACE_DATA_KINDS if kind != DataKind.PAYOFF]

    result = provider.get_race_data_bulk(_RACE_CODES, kinds)

    race_getter.get_haraimodoshi.assert_not_called()
    assert DataKind.PAYOFF not in result


def test_only_race_basic_info_fetches_race_shosai_alone(
    provider: MykeibaDBProvider, empty_getters: tuple[MagicMock, MagicMock]
) -> None:
    """レース基本情報だけを指定するとRACE_SHOSAIだけを取得する."""
    race_getter, odds_getter = empty_getters

    provider.get_race_data_bulk(_RACE_CODES, [DataKind.RACE_BASIC_INFO])

    race_getter.get_race_shosai.assert_called_once()
    race_getter.get_umagoto_race_joho.assert_not_called()
    race_getter.get_haraimodoshi.assert_not_called()
    odds_getter.get_odds1_tansho.assert_not_called()
    odds_getter.get_odds1_fukusho.assert_not_called()


@pytest.mark.parametrize(
    "kind, other_kind",
    [
        (DataKind.RACE_BASIC_INFO, DataKind.RACE_RESULT_INFO),
        (DataKind.ENTRY, DataKind.RESULT),
    ],
)
def test_same_table_kinds_can_be_specified_individually(
    provider: MykeibaDBProvider,
    empty_getters: tuple[MagicMock, MagicMock],
    kind: str,
    other_kind: str,
) -> None:
    """同一テーブルを引く種別の片方だけを指定しても、その種別だけが返る."""
    result = provider.get_race_data_bulk(_RACE_CODES, [kind])

    assert kind in result
    assert other_kind not in result


def test_same_table_is_fetched_once_for_both_kinds(
    provider: MykeibaDBProvider, empty_getters: tuple[MagicMock, MagicMock]
) -> None:
    """同一テーブルを引く種別を両方指定してもテーブルの取得は1回で済む."""
    race_getter, _ = empty_getters

    provider.get_race_data_bulk(_RACE_CODES, [DataKind.ENTRY, DataKind.RESULT])

    race_getter.get_umagoto_race_joho.assert_called_once()


# 準正常系
def test_empty_kinds_fetches_nothing(
    provider: MykeibaDBProvider, empty_getters: tuple[MagicMock, MagicMock]
) -> None:
    """kindsに空のリストを渡すと何も取得しない."""
    race_getter, odds_getter = empty_getters

    result = provider.get_race_data_bulk(_RACE_CODES, [])

    assert result == {}
    race_getter.get_race_shosai.assert_not_called()
    odds_getter.get_odds1_tansho.assert_not_called()


def test_empty_race_codes_fetches_nothing(
    provider: MykeibaDBProvider, empty_getters: tuple[MagicMock, MagicMock]
) -> None:
    """レースコードが空の場合は何も取得しない."""
    race_getter, _ = empty_getters

    result = provider.get_race_data_bulk([])

    assert result == {}
    race_getter.get_race_shosai.assert_not_called()
