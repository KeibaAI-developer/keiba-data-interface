"""複数レース分をまとめて変換するconverterのテスト.

一括変換の結果をレースコードで分割すると、レースごとに1件版で変換した結果と
一致することを検証する。

`pd.concat` はobject型カラムの全欠損を `<NA>` から `nan` へ変えるため、
1件版の結果を連結して比較してはならない。レース単位で突き合わせる。
"""

from unittest.mock import patch

import pandas as pd
import pytest

from keiba_data_interface.providers.mykeibadb_converters import (
    convert_entry,
    convert_entry_bulk,
    convert_payoff,
    convert_payoff_bulk,
    convert_race_result_info,
    convert_race_result_info_bulk,
    convert_result,
    convert_result_bulk,
)
from keiba_data_interface.schema.columns import (
    PAYOFF_COLUMNS,
    RACE_INFO_BY_HORSE_COLUMNS,
    RACE_RESULT_INFO_COLUMNS,
)

from ..mykeibadb_provider.conftest import (
    create_haraimodoshi_df,
    create_race_shosai_df,
    create_umagoto_race_joho_df,
)

_RACE_CODES = ["2025050206050810", "2025050206050811", "2025050206050812"]


def _make_umagoto(race_codes: list[str]) -> pd.DataFrame:
    """指定したレースコード分のUMAGOTO_RACE_JOHO出力を生成する.

    単勝オッズはレースごとに違う並びにして、単勝人気順がレースをまたいで
    付かないことを検証できるようにする。

    Args:
        race_codes (list[str]): レースコードのリスト

    Returns:
        pd.DataFrame: 各レース2頭分のUMAGOTO_RACE_JOHO出力形式
    """
    frames = []
    for offset, race_code in enumerate(race_codes):
        df = create_umagoto_race_joho_df().copy()
        df["race_code"] = race_code
        df["race_bango"] = int(race_code[-2:])
        if "tansho_odds" in df.columns:
            # レースごとにオッズの水準をずらす
            df["tansho_odds"] = [100 + offset * 1000, 200 + offset * 1000][: len(df)]
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def _make_race_shosai(race_codes: list[str]) -> pd.DataFrame:
    """指定したレースコード分のRACE_SHOSAI出力を生成する.

    Args:
        race_codes (list[str]): レースコードのリスト

    Returns:
        pd.DataFrame: 各レース1行のRACE_SHOSAI出力形式
    """
    rows = []
    for race_code in race_codes:
        row = create_race_shosai_df().iloc[0].copy()
        row["race_code"] = race_code
        row["race_bango"] = int(race_code[-2:])
        rows.append(row)
    return pd.DataFrame(rows).reset_index(drop=True)


def _make_haraimodoshi(race_codes: list[str]) -> pd.DataFrame:
    """指定したレースコード分のHARAIMODOSHI出力を生成する.

    Args:
        race_codes (list[str]): レースコードのリスト

    Returns:
        pd.DataFrame: 各レース1行のHARAIMODOSHI出力形式
    """
    rows = []
    for race_code in race_codes:
        row = create_haraimodoshi_df().iloc[0].copy()
        row["race_code"] = race_code
        row["race_bango"] = int(race_code[-2:])
        rows.append(row)
    return pd.DataFrame(rows).reset_index(drop=True)


def _assert_matches_single(
    raw: pd.DataFrame,
    bulk_result: pd.DataFrame,
    single_func: object,
    race_codes: list[str],
    sort_columns: list[str],
) -> None:
    """一括変換の結果を分割し、レースごとに1件版と一致することを検証する.

    Args:
        raw (pd.DataFrame): 変換元（複数レース分）
        bulk_result (pd.DataFrame): 一括変換の結果
        single_func (object): 1件版の変換関数
        race_codes (list[str]): 検証するレースコード
        sort_columns (list[str]): 突き合わせのために並べ替えるカラム
    """
    for race_code in race_codes:
        single_raw = raw[raw["race_code"] == race_code].reset_index(drop=True)
        expected = single_func(single_raw)  # type: ignore[operator]
        actual = bulk_result[bulk_result["レースコード"] == race_code].reset_index(drop=True)
        if sort_columns:
            expected = expected.sort_values(sort_columns).reset_index(drop=True)
            actual = actual.sort_values(sort_columns).reset_index(drop=True)
        pd.testing.assert_frame_equal(actual, expected)


# 正常系（1件版との一致）
@pytest.mark.parametrize(
    ("make_raw", "bulk_func", "single_func", "sort_columns", "columns"),
    [
        (_make_umagoto, convert_entry_bulk, convert_entry, ["馬番"], RACE_INFO_BY_HORSE_COLUMNS),
        (_make_umagoto, convert_result_bulk, convert_result, ["馬番"], RACE_INFO_BY_HORSE_COLUMNS),
        (_make_haraimodoshi, convert_payoff_bulk, convert_payoff, [], PAYOFF_COLUMNS),
        (
            _make_race_shosai,
            convert_race_result_info_bulk,
            convert_race_result_info,
            [],
            RACE_RESULT_INFO_COLUMNS,
        ),
    ],
    ids=["entry", "result", "payoff", "race_result_info"],
)
def test_bulk_result_matches_single_version(
    make_raw: object,
    bulk_func: object,
    single_func: object,
    sort_columns: list[str],
    columns: list[str],
) -> None:
    """一括変換の結果をレースコードで分割すると1件版と一致する."""
    raw = make_raw(_RACE_CODES)  # type: ignore[operator]

    result = bulk_func(raw)  # type: ignore[operator]

    assert list(result.columns) == columns
    _assert_matches_single(raw, result, single_func, _RACE_CODES, sort_columns)


@pytest.mark.parametrize(
    ("make_raw", "bulk_func", "single_func", "sort_columns"),
    [
        (_make_umagoto, convert_entry_bulk, convert_entry, ["馬番"]),
        (_make_umagoto, convert_result_bulk, convert_result, ["馬番"]),
        (_make_haraimodoshi, convert_payoff_bulk, convert_payoff, []),
        (_make_race_shosai, convert_race_result_info_bulk, convert_race_result_info, []),
    ],
    ids=["entry", "result", "payoff", "race_result_info"],
)
def test_bulk_with_single_race_matches_single_version(
    make_raw: object,
    bulk_func: object,
    single_func: object,
    sort_columns: list[str],
) -> None:
    """1レースだけを渡しても1件版と同じ結果になる."""
    race_codes = _RACE_CODES[:1]
    raw = make_raw(race_codes)  # type: ignore[operator]

    result = bulk_func(raw)  # type: ignore[operator]

    _assert_matches_single(raw, result, single_func, race_codes, sort_columns)


# 正常系（レース単位の処理）
def test_ninkijun_is_recalculated_per_race() -> None:
    """単勝人気順がレースごとに再計算される.

    レースをまたいで順位を付けると、オッズの水準が違うレースで人気順が壊れる。
    """
    raw = _make_umagoto(_RACE_CODES)

    result = convert_result_bulk(raw)

    for race_code in _RACE_CODES:
        ninki = result[result["レースコード"] == race_code]["単勝人気順"].tolist()
        assert sorted(ninki) == [1, 2]


def test_apply_types_is_called_once_regardless_of_race_count() -> None:
    """apply_typesの呼び出し回数がレース数によらない.

    レースごとに変換すると、レース数に比例して呼ばれる。
    """
    raw = _make_umagoto(_RACE_CODES)

    with patch(
        "keiba_data_interface.providers.mykeibadb_converters.convert_entry.apply_types",
        wraps=None,
    ) as mock_apply:
        mock_apply.side_effect = lambda df, types: df
        convert_entry_bulk(raw)

    assert mock_apply.call_count == 1


# 準正常系
@pytest.mark.parametrize(
    ("make_raw", "bulk_func", "columns"),
    [
        (_make_umagoto, convert_entry_bulk, RACE_INFO_BY_HORSE_COLUMNS),
        (_make_umagoto, convert_result_bulk, RACE_INFO_BY_HORSE_COLUMNS),
        (_make_haraimodoshi, convert_payoff_bulk, PAYOFF_COLUMNS),
        (_make_race_shosai, convert_race_result_info_bulk, RACE_RESULT_INFO_COLUMNS),
    ],
    ids=["entry", "result", "payoff", "race_result_info"],
)
def test_bulk_with_empty_raw_returns_empty_with_schema(
    make_raw: object,
    bulk_func: object,
    columns: list[str],
) -> None:
    """0行のrawを渡すとスキーマどおりのカラムを持つ0行のDataFrameを返す."""
    raw = make_raw(_RACE_CODES).iloc[0:0]  # type: ignore[operator]

    result = bulk_func(raw)  # type: ignore[operator]

    assert len(result) == 0
    assert list(result.columns) == columns
