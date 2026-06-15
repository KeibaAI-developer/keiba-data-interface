"""convert_chakudosu関数のテスト."""

from datetime import date

import pandas as pd
import pytest

from keiba_data_interface.providers.scraping_converters.convert_chakudosu import convert_chakudosu
from keiba_data_interface.schema.columns import CHAKUDOSU_COLUMNS

RACE_CODE = "2025050206050811"  # 開催日 = 2025-05-02


def _entry_df(horses: list[tuple[str, str]]) -> pd.DataFrame:
    """出馬表（血統登録番号・馬名のみ）のDataFrameを生成する."""
    return pd.DataFrame(horses, columns=["血統登録番号", "馬名"])


def _past_performances(rows: list[dict[str, object]]) -> pd.DataFrame:
    """raw馬柱（着度数集計に必要なカラムのみ）のDataFrameを生成する."""
    return pd.DataFrame(rows)


def _performance_row(
    日付: date,
    競馬場: str,
    芝ダ: str,
    距離: float,
    馬場: str,
    着順: float,
    主催: str = "中央",
    異常区分: str = "",
) -> dict[str, object]:
    """raw馬柱の1行分の辞書を生成する."""
    return {
        "日付": 日付,
        "主催": 主催,
        "競馬場": 競馬場,
        "芝ダ": 芝ダ,
        "距離": 距離,
        "馬場": 馬場,
        "着順": 着順,
        "異常区分": 異常区分,
    }


# 正常系
def test_output_columns_match_schema() -> None:
    """出力DataFrameのカラム構成がCHAKUDOSU_COLUMNSと一致する."""
    entry_df = _entry_df([("2021105001", "テスト馬1")])

    result = convert_chakudosu(RACE_CODE, entry_df, {})

    assert list(result.columns) == CHAKUDOSU_COLUMNS


def test_new_horse_all_zero() -> None:
    """中央出走歴のない馬は着回数カラムがすべて0になる."""
    entry_df = _entry_df([("2021105001", "テスト馬1")])

    result = convert_chakudosu(RACE_CODE, entry_df, {})

    row = result.iloc[0]
    assert row["レースコード"] == RACE_CODE
    assert row["血統登録番号"] == "2021105001"
    assert row["馬名"] == "テスト馬1"
    assert row["中山ダ1着"] == 0
    assert row["芝1200以下着外"] == 0


def test_keibajo_kyori_baba_columns_mapped() -> None:
    """競馬場別・距離別・馬場別・馬場状態別カラムが正しく集計される."""
    entry_df = _entry_df([("2021105001", "テスト馬1")])
    past = _past_performances(
        [_performance_row(date(2025, 4, 1), "中山", "ダ", 1800, "良", 1.0)]
    )

    result = convert_chakudosu(RACE_CODE, entry_df, {"2021105001": past})

    row = result.iloc[0]
    assert row["中山ダ1着"] == 1
    assert row["ダ1601-18001着"] == 1
    assert row["ダ右1着"] == 1
    assert row["ダ良1着"] == 1
    # 該当しないカラムは0
    assert row["中山ダ2着"] == 0
    assert row["芝1601-18001着"] == 0


@pytest.mark.parametrize(
    "kyori, expected_kubun",
    [
        (1200, "1200以下"),
        (1201, "1201-1400"),
        (1400, "1201-1400"),
        (1401, "1401-1600"),
        (1600, "1401-1600"),
        (1601, "1601-1800"),
        (1800, "1601-1800"),
        (1801, "1801-2000"),
        (2000, "1801-2000"),
        (2001, "2001-2200"),
        (2200, "2001-2200"),
        (2201, "2201-2400"),
        (2400, "2201-2400"),
        (2401, "2401-2800"),
        (2800, "2401-2800"),
        (2801, "2801以上"),
    ],
)
def test_kyori_kubun_boundary(kyori: int, expected_kubun: str) -> None:
    """距離区分の境界値が正しく判定される."""
    entry_df = _entry_df([("2021105001", "テスト馬1")])
    past = _past_performances(
        [_performance_row(date(2025, 4, 1), "東京", "芝", kyori, "良", 1.0)]
    )

    result = convert_chakudosu(RACE_CODE, entry_df, {"2021105001": past})

    row = result.iloc[0]
    assert row[f"芝{expected_kubun}1着"] == 1


def test_sixth_or_lower_is_chakugai() -> None:
    """着順6以上は着外として集計される."""
    entry_df = _entry_df([("2021105001", "テスト馬1")])
    past = _past_performances(
        [_performance_row(date(2025, 4, 1), "東京", "芝", 2000, "良", 8.0)]
    )

    result = convert_chakudosu(RACE_CODE, entry_df, {"2021105001": past})

    row = result.iloc[0]
    assert row["東京芝着外"] == 1
    assert row["東京芝1着"] == 0


def test_kourakuchaku_uses_confirmed_numeric_order() -> None:
    """降着の場合は確定着順（数値）で集計される."""
    entry_df = _entry_df([("2021105001", "テスト馬1")])
    # 降着により1着→4着に確定したケースを想定（rawでは確定着順の数値が入る）
    past = _past_performances(
        [_performance_row(date(2025, 4, 1), "東京", "芝", 2000, "良", 4.0)]
    )

    result = convert_chakudosu(RACE_CODE, entry_df, {"2021105001": past})

    row = result.iloc[0]
    assert row["東京芝4着"] == 1
    assert row["東京芝1着"] == 0


def test_nan_chakujun_excluded() -> None:
    """着順がNaN（取消・除外・失格）の行は集計対象外."""
    entry_df = _entry_df([("2021105001", "テスト馬1")])
    past = _past_performances(
        [
            _performance_row(
                date(2025, 4, 1), "東京", "芝", 2000, "良", float("nan"), 異常区分="取消"
            ),
            _performance_row(date(2025, 3, 1), "東京", "芝", 2000, "良", 1.0),
        ]
    )

    result = convert_chakudosu(RACE_CODE, entry_df, {"2021105001": past})

    row = result.iloc[0]
    assert row["東京芝1着"] == 1
    assert row["東京芝着外"] == 0


def test_chushi_counted_as_chakugai() -> None:
    """競走中止（着順NaN・異常区分="中止"）の行は着外として集計される."""
    entry_df = _entry_df([("2021105001", "テスト馬1")])
    past = _past_performances(
        [
            _performance_row(
                date(2025, 4, 1), "東京", "芝", 2000, "良", float("nan"), 異常区分="中止"
            )
        ]
    )

    result = convert_chakudosu(RACE_CODE, entry_df, {"2021105001": past})

    row = result.iloc[0]
    assert row["東京芝着外"] == 1
    assert row["芝1801-2000着外"] == 1
    assert row["芝左着外"] == 1
    assert row["芝良着外"] == 1


@pytest.mark.parametrize("shusai", ["地方", "海外"])
def test_chiho_kaigai_excluded(shusai: str) -> None:
    """地方・海外のレースは集計対象外."""
    entry_df = _entry_df([("2021105001", "テスト馬1")])
    past = _past_performances(
        [_performance_row(date(2025, 4, 1), "大井", "ダ", 1800, "良", 1.0, 主催=shusai)]
    )

    result = convert_chakudosu(RACE_CODE, entry_df, {"2021105001": past})

    row = result.iloc[0]
    assert row["ダ1601-18001着"] == 0


def test_date_filter_excludes_same_or_after_race_date() -> None:
    """対象レースの開催日以降の成績は集計対象外."""
    entry_df = _entry_df([("2021105001", "テスト馬1")])
    past = _past_performances(
        [
            # 対象レースと同日（未来の確定値は集計しない）
            _performance_row(date(2025, 5, 2), "東京", "芝", 2000, "良", 1.0),
            # 対象レースより前
            _performance_row(date(2025, 4, 1), "東京", "芝", 2000, "良", 2.0),
        ]
    )

    result = convert_chakudosu(RACE_CODE, entry_df, {"2021105001": past})

    row = result.iloc[0]
    assert row["東京芝1着"] == 0
    assert row["東京芝2着"] == 1


def test_niigata_shiba_1000_is_chokusen() -> None:
    """新潟芝1000mは回り「直」として集計される."""
    entry_df = _entry_df([("2021105001", "テスト馬1")])
    past = _past_performances(
        [_performance_row(date(2025, 4, 1), "新潟", "芝", 1000, "良", 1.0)]
    )

    result = convert_chakudosu(RACE_CODE, entry_df, {"2021105001": past})

    row = result.iloc[0]
    assert row["芝直1着"] == 1
    assert row["芝左1着"] == 0


def test_niigata_shiba_other_distance_is_hidari() -> None:
    """新潟芝1000m以外は左回りとして集計される."""
    entry_df = _entry_df([("2021105001", "テスト馬1")])
    past = _past_performances(
        [_performance_row(date(2025, 4, 1), "新潟", "芝", 1200, "良", 1.0)]
    )

    result = convert_chakudosu(RACE_CODE, entry_df, {"2021105001": past})

    row = result.iloc[0]
    assert row["芝左1着"] == 1
    assert row["芝直1着"] == 0


def test_jump_race_columns_mapped() -> None:
    """障害レースは障害・馬場状態別カラムに集計され距離別・馬場別は集計されない."""
    entry_df = _entry_df([("2021105001", "テスト馬1")])
    past = _past_performances(
        [_performance_row(date(2025, 4, 1), "中山", "障", 3200, "良", 1.0)]
    )

    result = convert_chakudosu(RACE_CODE, entry_df, {"2021105001": past})

    row = result.iloc[0]
    assert row["中山障1着"] == 1
    assert row["障害1着"] == 1
    assert row["障良1着"] == 1
    # 障害レースは距離別・馬場別（直右左）カラムには集計されない
    assert row["芝1200以下1着"] == 0
    assert row["芝直1着"] == 0


def test_sorted_by_ketto_toroku_bango() -> None:
    """出力DataFrameが血統登録番号昇順である."""
    entry_df = _entry_df([("2021105002", "テスト馬2"), ("2021105001", "テスト馬1")])

    result = convert_chakudosu(RACE_CODE, entry_df, {})

    assert list(result["血統登録番号"]) == ["2021105001", "2021105002"]


# 準正常系
def test_empty_past_performances_treated_as_new_horse() -> None:
    """馬柱が空DataFrameの場合は新馬扱い（全カラム0）になる."""
    entry_df = _entry_df([("2021105001", "テスト馬1")])

    result = convert_chakudosu(RACE_CODE, entry_df, {"2021105001": pd.DataFrame()})

    row = result.iloc[0]
    assert row["中山ダ1着"] == 0
