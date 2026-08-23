"""MykeibaDBProvider.get_horse_master_bulk関数のテスト.

`kyosoba_master2` は血統登録番号が主キーのためクエリ自体は速いが、頭数ぶんの往復と
変換（228カラムの型変換を1頭につき2回）が積み上がる。1回にまとめる。
"""

from collections.abc import Sequence
from unittest.mock import MagicMock

import pandas as pd
import pytest

from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.schema.columns import HORSE_MASTER_COLUMNS

from .conftest import create_kyosoba_master2_df

_HORSE_IDS = ["2021105001", "2021105002", "2021105003"]


def _make_multi_horse(horse_ids: list[str]) -> pd.DataFrame:
    """指定した馬ぶんのKYOSOBA_MASTER2出力を生成する.

    Args:
        horse_ids (list[str]): 血統登録番号のリスト

    Returns:
        pd.DataFrame: 各馬1行のKYOSOBA_MASTER2出力形式
    """
    rows = []
    for index, horse_id in enumerate(horse_ids):
        row = create_kyosoba_master2_df().iloc[0].copy()
        row["ketto_toroku_bango"] = horse_id
        row["bamei"] = f"テスト馬{index + 1}"
        rows.append(row)
    return pd.DataFrame(rows).reset_index(drop=True)


@pytest.fixture
def master_getter(mock_master_getter: MagicMock) -> MagicMock:
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

    mock_master_getter.get_kyosoba_master2.side_effect = side_effect
    return mock_master_getter


# 正常系
def test_result_matches_single_fetch(
    provider: MykeibaDBProvider, master_getter: MagicMock
) -> None:
    """戻り値が、馬ごとに1件取得した結果と一致する.

    値・カラム構成・dtype・indexのすべてを比較する。
    """
    result = provider.get_horse_master_bulk(_HORSE_IDS)

    for horse_id in _HORSE_IDS:
        pd.testing.assert_frame_equal(result[horse_id], provider.get_horse_master(horse_id))


def test_output_columns_match_schema(
    provider: MykeibaDBProvider, master_getter: MagicMock
) -> None:
    """各馬の出力カラム構成がHORSE_MASTER_COLUMNSと一致する."""
    result = provider.get_horse_master_bulk(_HORSE_IDS)

    for horse_id in _HORSE_IDS:
        assert list(result[horse_id].columns) == HORSE_MASTER_COLUMNS
        assert len(result[horse_id]) == 1


def test_query_is_issued_once(
    provider: MykeibaDBProvider, master_getter: MagicMock
) -> None:
    """頭数によらずクエリが1回で済む."""
    provider.get_horse_master_bulk(_HORSE_IDS)

    master_getter.get_kyosoba_master2.assert_called_once()


def test_duplicated_horse_id_is_fetched_once(
    provider: MykeibaDBProvider, master_getter: MagicMock
) -> None:
    """重複した馬IDを渡しても1回だけ取得する."""
    provider.get_horse_master_bulk([*_HORSE_IDS, _HORSE_IDS[0]])

    passed = master_getter.get_kyosoba_master2.call_args.kwargs["ketto_toroku_bango"]
    assert passed == _HORSE_IDS


# 準正常系
def test_horse_not_in_master_has_empty_dataframe(
    provider: MykeibaDBProvider, master_getter: MagicMock
) -> None:
    """マスタに存在しない馬のキーが存在し、1件取得と同じ空のDataFrameになる."""
    unknown = "9999999999"

    result = provider.get_horse_master_bulk([*_HORSE_IDS, unknown])

    assert unknown in result
    pd.testing.assert_frame_equal(result[unknown], provider.get_horse_master(unknown))


def test_horses_not_in_master_do_not_share_one_dataframe(
    provider: MykeibaDBProvider, master_getter: MagicMock
) -> None:
    """マスタに存在しない馬どうしが同じDataFrameを共有しない.

    同じインスタンスを共有すると、呼び出し側が一方を書き換えたときに他方まで変わる。
    """
    first, second = "9999999998", "9999999999"

    result = provider.get_horse_master_bulk([first, second])

    assert result[first] is not result[second]


def test_duplicated_rows_are_reduced_to_one(
    provider: MykeibaDBProvider, mock_master_getter: MagicMock
) -> None:
    """同じ馬の行が複数返っても1行だけを返す（1件取得と同じ）.

    血統登録番号はkyosoba_master2の主キーなので起こらないが、起きた場合も
    1件取得（raw.iloc[0]）と同じ結果になる必要がある。
    """
    horse_id = _HORSE_IDS[0]
    duplicated = _make_multi_horse([horse_id, horse_id])
    duplicated.loc[1, "bamei"] = "二行目の馬名"
    mock_master_getter.get_kyosoba_master2.return_value = duplicated

    result = provider.get_horse_master_bulk([horse_id])

    assert len(result[horse_id]) == 1
    assert result[horse_id]["馬名"].iloc[0] == "テスト馬1"


def test_empty_horse_ids_issues_no_query(
    provider: MykeibaDBProvider, master_getter: MagicMock
) -> None:
    """空のリストを渡すとクエリを発行せず空の辞書を返す."""
    result = provider.get_horse_master_bulk([])

    assert result == {}
    master_getter.get_kyosoba_master2.assert_not_called()


def test_unrequested_horse_is_not_included(
    provider: MykeibaDBProvider, mock_master_getter: MagicMock
) -> None:
    """要求していない馬が戻り値に混ざらない."""
    mock_master_getter.get_kyosoba_master2.return_value = _make_multi_horse(_HORSE_IDS)

    result = provider.get_horse_master_bulk(_HORSE_IDS[:1])

    assert set(result) == {_HORSE_IDS[0]}
