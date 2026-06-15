"""get_chakudosu用の変換関数.

各馬のraw馬柱（HorsePageScraper.get_past_performances()の出力）から
対象レース出走時点の条件別着回数を集計し、統一スキーマに変換する。
"""

from datetime import date

import pandas as pd

from keiba_data_interface.schema.columns import CHAKUDOSU_COLUMNS
from keiba_data_interface.schema.types import CHAKUDOSU_TYPES
from keiba_data_interface.utils.dataframe import apply_types, ensure_columns

_KEY_COLUMNS: set[str] = {"レースコード", "血統登録番号", "馬名"}
_COUNT_COLUMNS: list[str] = [col for col in CHAKUDOSU_COLUMNS if col not in _KEY_COLUMNS]

# 中央10場の回り（右/左）。新潟芝1000mのみ「直」の例外。
_MIGI_KEIBAJO: set[str] = {"札幌", "函館", "福島", "中山", "京都", "阪神", "小倉"}
_HIDARI_KEIBAJO: set[str] = {"新潟", "東京", "中京"}

# 距離区分の境界（境界値以下なら採用）。CHAKUDOSU.mdの区分と同一
_KYORI_KUBUN_BOUNDARIES: list[tuple[int, str]] = [
    (1200, "1200以下"),
    (1400, "1201-1400"),
    (1600, "1401-1600"),
    (1800, "1601-1800"),
    (2000, "1801-2000"),
    (2200, "2001-2200"),
    (2400, "2201-2400"),
    (2800, "2401-2800"),
]
_KYORI_KUBUN_OVER: str = "2801以上"


def convert_chakudosu(
    race_code: str,
    entry_df: pd.DataFrame,
    past_performances_map: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """各馬のraw馬柱から出走別着度数の統一スキーマを構築する.

    Args:
        race_code (str): 16桁レースコード
        entry_df (pd.DataFrame): 統一スキーマの出馬表（血統登録番号・馬名を使用）
        past_performances_map (dict[str, pd.DataFrame]):
            血統登録番号 → HorsePageScraper.get_past_performances() のraw出力

    Returns:
        pd.DataFrame: CHAKUDOSU_COLUMNS構成・出走頭数行・血統登録番号昇順
    """
    race_date = date(int(race_code[:4]), int(race_code[4:6]), int(race_code[6:8]))

    rows: list[dict[str, object]] = []
    for _, entry in entry_df.iterrows():
        ketto_toroku_bango = str(entry["血統登録番号"])
        row: dict[str, object] = {
            "レースコード": race_code,
            "血統登録番号": ketto_toroku_bango,
            "馬名": entry["馬名"],
        }
        past = past_performances_map.get(ketto_toroku_bango, pd.DataFrame())
        target = _filter_target_rows(past, race_date)
        if target.empty:
            row.update(dict.fromkeys(_COUNT_COLUMNS, pd.NA))
        else:
            counts = dict.fromkeys(_COUNT_COLUMNS, 0)
            for _, performance in target.iterrows():
                for col in _columns_for_performance(performance):
                    counts[col] += 1
            row.update(counts)
        rows.append(row)

    df = pd.DataFrame(rows)
    df = ensure_columns(df, CHAKUDOSU_COLUMNS)
    df = apply_types(df, CHAKUDOSU_TYPES)
    return df.sort_values("血統登録番号").reset_index(drop=True)


def _filter_target_rows(past: pd.DataFrame, race_date: date) -> pd.DataFrame:
    """対象レース出走時点までの集計対象行を抽出する.

    中央のレースかつ対象レースの開催日より前かつ着順が数値の行のみを残す。

    Args:
        past (pd.DataFrame): HorsePageScraper.get_past_performances() のraw出力
        race_date (date): 対象レースの開催日

    Returns:
        pd.DataFrame: 集計対象行
    """
    if past.empty:
        return past
    # 着順は取消・除外・中止・失格でNaN、降着は確定着順の数値（pd.to_numeric済み）
    mask = (
        (past["主催"] == "中央") & (past["日付"] < race_date) & past["着順"].notna()
    )
    return past[mask]


def _columns_for_performance(performance: pd.Series) -> list[str]:
    """1走分の成績からインクリメント対象のCHAKUDOSU_COLUMNSを求める.

    Args:
        performance (pd.Series): 集計対象の1走分（raw馬柱の1行）

    Returns:
        list[str]: インクリメント対象のカラム名リスト
    """
    keibajo = str(performance["競馬場"])
    shiba_da = str(performance["芝ダ"])
    baba_jotai = str(performance["馬場"])
    chaku_suffix = _chaku_suffix(performance["着順"])

    columns = [f"{keibajo}{shiba_da}{chaku_suffix}"]

    if shiba_da in ("芝", "ダ"):
        kyori = int(performance["距離"])
        columns.append(f"{shiba_da}{_kyori_kubun(kyori)}{chaku_suffix}")
        columns.append(f"{shiba_da}{_mawari(keibajo, shiba_da, kyori)}{chaku_suffix}")
        columns.append(f"{shiba_da}{baba_jotai}{chaku_suffix}")
    else:
        columns.append(f"障害{chaku_suffix}")
        columns.append(f"障{baba_jotai}{chaku_suffix}")

    return columns


def _chaku_suffix(chakujun: float) -> str:
    """着順から着順サフィックスを求める.

    Args:
        chakujun (float): 着順（数値）

    Returns:
        str: 着順サフィックス（"1着"〜"5着" または "着外"）
    """
    order = int(chakujun)
    if 1 <= order <= 5:
        return f"{order}着"
    return "着外"


def _kyori_kubun(kyori: int) -> str:
    """距離から距離区分を求める.

    Args:
        kyori (int): 距離（m）

    Returns:
        str: 距離区分（"1200以下"〜"2801以上"）
    """
    for boundary, label in _KYORI_KUBUN_BOUNDARIES:
        if kyori <= boundary:
            return label
    return _KYORI_KUBUN_OVER


def _mawari(keibajo: str, shiba_da: str, kyori: int) -> str:
    """競馬場・面・距離から回り（右/左/直）を求める.

    新潟芝1000mのみ直線（直）の例外。

    Args:
        keibajo (str): 競馬場名
        shiba_da (str): 芝ダ区分（"芝" または "ダ"）
        kyori (int): 距離（m）

    Returns:
        str: 回り（"右" / "左" / "直"）
    """
    if keibajo == "新潟" and shiba_da == "芝" and kyori == 1000:
        return "直"
    if keibajo in _MIGI_KEIBAJO:
        return "右"
    return "左"
