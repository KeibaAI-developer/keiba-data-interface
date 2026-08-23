"""MykeibaDBProvider.get_past_performances_bulk関数のテスト.

`umagoto_race_joho` の主キーは (race_code, ketto_toroku_bango) であり、血統登録番号
だけで絞り込むと主キーの前方一致にならずインデックスを頭から走査する。1頭ずつ取得すると
その走査が頭数ぶん繰り返されるため、IN句で1回にまとめる。
"""

from collections.abc import Sequence
from unittest.mock import MagicMock

import pandas as pd
import pytest

from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.schema.columns import RACE_INFO_BY_HORSE_COLUMNS

from .conftest import create_umagoto_race_joho_df

_HORSE_IDS = ["2021105001", "2021105002", "2021105003"]


def _make_multi_horse(horse_ids: list[str]) -> pd.DataFrame:
    """指定した馬ぶんのUMAGOTO_RACE_JOHO出力を生成する.

    馬ごとにレースコードをずらして、レースコード降順の並べ替えを検証できるようにする。

    Args:
        horse_ids (list[str]): 血統登録番号のリスト

    Returns:
        pd.DataFrame: 各馬2行のUMAGOTO_RACE_JOHO出力形式
    """
    frames = []
    for offset, horse_id in enumerate(horse_ids):
        df = create_umagoto_race_joho_df().copy()
        df["ketto_toroku_bango"] = horse_id
        df["race_code"] = [f"20250{offset}0206050811", f"20250{offset}0206050812"]
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


@pytest.fixture
def horse_getter(mock_race_getter: MagicMock) -> MagicMock:
    """血統登録番号で絞り込んで返すgetterのモック.

    1頭指定でもリスト指定でも、実際のgetterと同じ絞り込みを再現する。
    """
    full = _make_multi_horse(_HORSE_IDS)

    def side_effect(*_args: object, **kwargs: object) -> pd.DataFrame:
        """ketto_toroku_bango引数に一致する行だけを返す.

        Returns:
            pd.DataFrame: 指定された馬の行
        """
        horse_id = kwargs.get("ketto_toroku_bango")
        if isinstance(horse_id, str):
            ids: list[str] = [horse_id]
        elif isinstance(horse_id, Sequence):
            ids = [str(value) for value in horse_id]
        else:
            ids = []
        return full[full["ketto_toroku_bango"].isin(ids)].reset_index(drop=True)

    mock_race_getter.get_umagoto_race_joho.side_effect = side_effect
    return mock_race_getter


# 正常系
def test_result_matches_single_fetch(
    provider: MykeibaDBProvider, horse_getter: MagicMock
) -> None:
    """戻り値が、馬ごとに1件取得した結果と一致する.

    値・カラム構成・dtype・行順・indexのすべてを比較する。
    """
    result = provider.get_past_performances_bulk(_HORSE_IDS)

    for horse_id in _HORSE_IDS:
        expected = provider.get_past_performances(horse_id)
        pd.testing.assert_frame_equal(result[horse_id], expected)


def test_output_columns_match_schema(
    provider: MykeibaDBProvider, horse_getter: MagicMock
) -> None:
    """各馬の出力カラム構成がHORSE_RACE_INFO_COLUMNSと一致する."""
    result = provider.get_past_performances_bulk(_HORSE_IDS)

    for horse_id in _HORSE_IDS:
        assert list(result[horse_id].columns) == RACE_INFO_BY_HORSE_COLUMNS


def test_rows_are_sorted_by_race_code_descending(
    provider: MykeibaDBProvider, horse_getter: MagicMock
) -> None:
    """各馬の行がレースコード降順に並ぶ（1件取得と同じ並び）."""
    result = provider.get_past_performances_bulk(_HORSE_IDS)

    for horse_id in _HORSE_IDS:
        race_codes = result[horse_id]["レースコード"].tolist()
        assert race_codes == sorted(race_codes, reverse=True)


def test_query_is_issued_once(provider: MykeibaDBProvider, horse_getter: MagicMock) -> None:
    """頭数によらずクエリが1回で済む.

    1頭ずつ取得すると、主キーの前方一致にならない走査が頭数ぶん繰り返される。
    """
    provider.get_past_performances_bulk(_HORSE_IDS)

    horse_getter.get_umagoto_race_joho.assert_called_once()


def test_duplicated_horse_id_is_fetched_once(
    provider: MykeibaDBProvider, horse_getter: MagicMock
) -> None:
    """重複した馬IDを渡しても1回だけ取得する."""
    provider.get_past_performances_bulk([*_HORSE_IDS, _HORSE_IDS[0]])

    passed = horse_getter.get_umagoto_race_joho.call_args.kwargs["ketto_toroku_bango"]
    assert passed == _HORSE_IDS


# 準正常系
def test_horse_without_history_has_empty_dataframe(
    provider: MykeibaDBProvider, horse_getter: MagicMock
) -> None:
    """出走歴が無い馬のキーが存在し、1件取得と同じ空のDataFrameになる.

    キーを落とすと、カラム構成を知らない呼び出し側が空のDataFrameを組み立てられない。
    """
    make_debut = "9999999999"

    result = provider.get_past_performances_bulk([*_HORSE_IDS, make_debut])

    assert make_debut in result
    pd.testing.assert_frame_equal(
        result[make_debut], provider.get_past_performances(make_debut)
    )


def test_empty_horse_ids_issues_no_query(
    provider: MykeibaDBProvider, horse_getter: MagicMock
) -> None:
    """空のリストを渡すとクエリを発行せず空の辞書を返す."""
    result = provider.get_past_performances_bulk([])

    assert result == {}
    horse_getter.get_umagoto_race_joho.assert_not_called()


def test_unrequested_horse_is_not_included(
    provider: MykeibaDBProvider, mock_race_getter: MagicMock
) -> None:
    """要求していない馬が戻り値に混ざらない.

    getterが余分な行を返しても、指定した馬IDのキーだけを返す。
    """
    mock_race_getter.get_umagoto_race_joho.return_value = _make_multi_horse(_HORSE_IDS)

    result = provider.get_past_performances_bulk(_HORSE_IDS[:1])

    assert set(result) == {_HORSE_IDS[0]}
