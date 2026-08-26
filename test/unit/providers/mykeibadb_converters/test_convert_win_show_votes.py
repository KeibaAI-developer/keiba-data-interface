"""convert_win_show_votesのテスト."""

import pandas as pd
import pytest

from keiba_data_interface.providers.mykeibadb_converters import convert_win_show_votes
from keiba_data_interface.schema.columns import WIN_SHOW_VOTES_COLUMNS

_RACE_CODE = "2025050206050811"


def _tansho(umaban: list[str], hyosu: list[str], ninki: list[str]) -> pd.DataFrame:
    """HYOSU1_TANSHO相当のDataFrameを生成する."""
    n = len(umaban)
    return pd.DataFrame({
        "data_kubun": ["2"] * n,
        "race_code": [_RACE_CODE] * n,
        "kaisai_nen": ["2025"] * n,
        "kaisai_gappi": ["0502"] * n,
        "keibajo_code": ["06"] * n,
        "kaisai_kaiji": ["05"] * n,
        "kaisai_nichiji": ["08"] * n,
        "race_bango": ["11"] * n,
        "umaban": umaban,
        "hyosu": hyosu,
        "ninki": ninki,
    })


def _fukusho(umaban: list[str], hyosu: list[str], ninki: list[str]) -> pd.DataFrame:
    """HYOSU1_FUKUSHO相当のDataFrameを生成する."""
    return pd.DataFrame({
        "race_code": [_RACE_CODE] * len(umaban),
        "umaban": umaban,
        "hyosu": hyosu,
        "ninki": ninki,
    })


def _odds1(tansho_total: str = "00000300000", fukusho_total: str = "00000200000") -> pd.DataFrame:
    """ODDS1相当のDataFrame（1行）を生成する."""
    return pd.DataFrame({
        "race_code": [_RACE_CODE],
        "tansho_hyosu_gokei": [tansho_total],
        "fukusho_hyosu_gokei": [fukusho_total],
    })


# 正常系
def test_converts_to_schema_in_umaban_order() -> None:
    """馬番順に並び、スキーマのカラムと型で返る."""
    tansho = _tansho(["03", "01"], ["00000000200", "00000000100"], ["01", "02"])
    fukusho = _fukusho(["01", "03"], ["00000000050", "00000000080"], ["02", "01"])

    result = convert_win_show_votes(tansho, fukusho, _odds1())

    assert list(result.columns) == WIN_SHOW_VOTES_COLUMNS
    assert result["馬番"].tolist() == [1, 3]
    assert result["単勝票数"].tolist() == [100, 200]
    assert result["複勝票数"].tolist() == [50, 80]
    assert result["単勝票数人気"].tolist() == [2, 1]
    assert result["複勝票数人気"].tolist() == [2, 1]
    assert result["単勝票数合計"].tolist() == [300000, 300000]
    assert result["複勝票数合計"].tolist() == [200000, 200000]
    assert result["データ区分"].tolist() == ["2", "2"]
    assert str(result["単勝票数"].dtype) == "Int64"


def test_all_zero_votes_become_zero_and_cancelled_ninki_becomes_na() -> None:
    """ALL0の票数は0、'--'（発売前取消）・'**'（発売後取消）の人気は欠損になる."""
    tansho = _tansho(["01", "02"], ["00000000000", "00000000100"], ["--", "01"])
    fukusho = _fukusho(["01", "02"], ["00000000000", "00000000050"], ["**", "01"])

    result = convert_win_show_votes(tansho, fukusho, _odds1())

    row = result[result["馬番"] == 1].iloc[0]
    assert row["単勝票数"] == 0
    assert row["複勝票数"] == 0
    assert pd.isna(row["単勝票数人気"])
    assert pd.isna(row["複勝票数人気"])


def test_unregistered_rows_are_dropped() -> None:
    """票数がスペース（登録なし）の馬番は行ごと除かれる."""
    tansho = _tansho(["01", "02"], ["00000000100", "           "], ["01", "  "])
    fukusho = _fukusho(["01", "02"], ["00000000050", "           "], ["01", "  "])

    result = convert_win_show_votes(tansho, fukusho, _odds1())

    assert result["馬番"].tolist() == [1]


# 準正常系
def test_empty_input_raises() -> None:
    """いずれかの入力が空ならValueErrorになる."""
    with pytest.raises(ValueError, match="空"):
        convert_win_show_votes(pd.DataFrame(), _fukusho(["01"], ["1"], ["1"]), _odds1())


def test_multiple_odds1_rows_raise() -> None:
    """ODDS1が複数行ならValueErrorになる."""
    odds1 = pd.concat([_odds1(), _odds1()], ignore_index=True)

    with pytest.raises(ValueError, match="1行"):
        convert_win_show_votes(_tansho(["01"], ["1"], ["1"]), _fukusho(["01"], ["1"], ["1"]), odds1)
