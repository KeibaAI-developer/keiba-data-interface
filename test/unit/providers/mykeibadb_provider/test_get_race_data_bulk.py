"""MykeibaDBProvider.get_race_data_bulk関数のテスト.

プリフェッチ層が使う一括取得。指定された種別に必要なテーブルだけを取得することを
検証する。取得しない種別は変換も行われないため、変換のコストも避けられる。
"""

from collections.abc import Callable, Sequence
from unittest.mock import MagicMock

import pandas as pd
import pytest

from keiba_data_interface.cache import RACE_DATA_KINDS, DataKind
from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider

from .conftest import (
    create_haraimodoshi_df,
    create_odds1_fukusho_df,
    create_odds1_tansho_df,
    create_race_shosai_df,
    create_umagoto_race_joho_df,
)

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


# 正常系（戻り値が1件取得と一致すること）
@pytest.fixture
def multi_race_getters(
    mock_race_getter: MagicMock, mock_odds_getter: MagicMock
) -> tuple[MagicMock, MagicMock]:
    """複数レース分のデータを返すgetterのモック.

    1件取得（race_code指定）でも一括取得（リスト指定）でも、指定されたレースコードの
    行だけを返すようにする。実際のgetterと同じ絞り込みを再現する。
    """

    def make_side_effect(full: pd.DataFrame) -> Callable[..., pd.DataFrame]:
        """race_code引数で絞り込んで返すside_effectを作る.

        Args:
            full (pd.DataFrame): 全レース分のデータ

        Returns:
            Callable[..., pd.DataFrame]: getterのside_effectに渡す関数
        """

        def side_effect(*_args: object, **kwargs: object) -> pd.DataFrame:
            """race_code引数に一致する行だけを返す.

            Returns:
                pd.DataFrame: 指定されたレースコードの行
            """
            race_code = kwargs.get("race_code")
            if isinstance(race_code, str):
                codes: list[str] = [race_code]
            elif isinstance(race_code, Sequence):
                codes = [str(code) for code in race_code]
            else:
                codes = []
            return full[full["race_code"].isin(codes)].reset_index(drop=True)

        return side_effect

    mock_race_getter.get_race_shosai.side_effect = make_side_effect(
        _make_multi_race(create_race_shosai_df, _RACE_CODES)
    )
    mock_race_getter.get_umagoto_race_joho.side_effect = make_side_effect(
        _make_multi_race(create_umagoto_race_joho_df, _RACE_CODES)
    )
    mock_race_getter.get_haraimodoshi.side_effect = make_side_effect(
        _make_multi_race(create_haraimodoshi_df, _RACE_CODES)
    )
    mock_odds_getter.get_odds1_tansho.side_effect = make_side_effect(
        _make_multi_race(create_odds1_tansho_df, _RACE_CODES)
    )
    mock_odds_getter.get_odds1_fukusho.side_effect = make_side_effect(
        _make_multi_race(create_odds1_fukusho_df, _RACE_CODES)
    )
    return mock_race_getter, mock_odds_getter


def _make_multi_race(
    factory: Callable[[], pd.DataFrame], race_codes: list[str]
) -> pd.DataFrame:
    """1レース分のフィクスチャを複製して複数レース分のDataFrameを作る.

    Args:
        factory (Callable[[], pd.DataFrame]): 1レース分のDataFrameを返す関数
        race_codes (list[str]): 複製するレースコード

    Returns:
        pd.DataFrame: 複数レース分を縦に連結したDataFrame
    """
    frames = []
    for race_code in race_codes:
        df = factory().copy()
        df["race_code"] = race_code
        df["race_bango"] = int(race_code[-2:])
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


@pytest.mark.parametrize(
    ("kind", "single_method"),
    [
        (DataKind.RACE_BASIC_INFO, "get_race_basic_info"),
        (DataKind.RACE_RESULT_INFO, "get_race_result_info"),
        (DataKind.ENTRY, "get_entry"),
        (DataKind.RESULT, "get_result"),
        (DataKind.PAYOFF, "get_payoff"),
        (DataKind.WIN_SHOW_ODDS, "get_win_show_odds"),
    ],
    ids=["race_basic_info", "race_result_info", "entry", "result", "payoff", "win_show_odds"],
)
def test_bulk_result_matches_single_fetch(
    provider: MykeibaDBProvider,
    multi_race_getters: tuple[MagicMock, MagicMock],
    kind: str,
    single_method: str,
) -> None:
    """一括取得の戻り値が、レースごとに1件取得した結果と一致する.

    値・カラム構成・dtype・行順・indexのすべてを比較する。プリフェッチできる全種別
    （RACE_DATA_KINDS）を対象にする。
    """
    result = provider.get_race_data_bulk(_RACE_CODES, [kind])

    for race_code in _RACE_CODES:
        expected = getattr(provider, single_method)(race_code)
        pd.testing.assert_frame_equal(result[kind][race_code], expected)


def test_entry_is_sorted_by_uma_ban(
    provider: MykeibaDBProvider, multi_race_getters: tuple[MagicMock, MagicMock]
) -> None:
    """出馬表が馬番昇順に並ぶ（1件取得と同じ並び）."""
    result = provider.get_race_data_bulk(_RACE_CODES, [DataKind.ENTRY])

    for race_code in _RACE_CODES:
        uma_ban = result[DataKind.ENTRY][race_code]["馬番"].tolist()
        assert uma_ban == sorted(uma_ban)


def test_result_is_sorted_by_chakujun_and_uma_ban(
    provider: MykeibaDBProvider, multi_race_getters: tuple[MagicMock, MagicMock]
) -> None:
    """レース結果が確定着順・馬番の昇順に並ぶ（1件取得と同じ並び）."""
    result = provider.get_race_data_bulk(_RACE_CODES, [DataKind.RESULT])

    for race_code in _RACE_CODES:
        df = result[DataKind.RESULT][race_code]
        keys = list(zip(df["確定着順"], df["馬番"], strict=True))
        assert keys == sorted(keys)


def test_index_is_reset_per_race(
    provider: MykeibaDBProvider, multi_race_getters: tuple[MagicMock, MagicMock]
) -> None:
    """レースごとのindexが通し番号に戻る（1件取得と同じ）.

    一括変換の結果は全レースを通した位置になるため、分割時に戻す必要がある。
    """
    result = provider.get_race_data_bulk(_RACE_CODES, [DataKind.ENTRY])

    for race_code in _RACE_CODES:
        df = result[DataKind.ENTRY][race_code]
        assert list(df.index) == list(range(len(df)))


# 準正常系
def test_missing_race_code_is_not_included(
    provider: MykeibaDBProvider, multi_race_getters: tuple[MagicMock, MagicMock]
) -> None:
    """存在しないレースコードはキーに含まれない."""
    missing = "2025050206059999"

    result = provider.get_race_data_bulk([*_RACE_CODES, missing], [DataKind.ENTRY])

    assert set(result[DataKind.ENTRY]) == set(_RACE_CODES)


def test_single_race_code_matches_single_fetch(
    provider: MykeibaDBProvider, multi_race_getters: tuple[MagicMock, MagicMock]
) -> None:
    """1レースだけを指定しても1件取得と一致する."""
    race_code = _RACE_CODES[0]

    result = provider.get_race_data_bulk([race_code], [DataKind.RESULT])

    pd.testing.assert_frame_equal(
        result[DataKind.RESULT][race_code], provider.get_result(race_code)
    )
