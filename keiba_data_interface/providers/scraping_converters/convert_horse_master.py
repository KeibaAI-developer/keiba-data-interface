"""get_horse_master用のscraping変換関数.

HorsePageScraperの出力を統一スキーマに変換する。
"""

import pandas as pd

from keiba_data_interface.providers.scraping_converters.common import TOZAI_SHOZOKU_TO_CODE
from keiba_data_interface.schema.columns import (
    _BABA_BETSU_PREFIXES,
    _BABA_JOTAI_PREFIXES,
    _CHAKU_SUFFIXES,
    _KYORI_BETSU_PREFIXES,
    HORSE_MASTER_COLUMNS,
)
from keiba_data_interface.schema.types import HORSE_MASTER_TYPES
from keiba_data_interface.utils.converters import to_half_kana
from keiba_data_interface.utils.dataframe import apply_types, ensure_columns

_SEIBETSU_TO_CODE: dict[str, str] = {
    "牡": "1",
    "牝": "2",
    "セ": "3",
}

_CHAKU_COUNT_KEYS = ["1着", "2着", "3着", "4着", "5着", "着外"]

_BABA_TYPE_MAP: dict[str, str] = {
    "芝": "芝",
    "ダ": "ダ",
    "障": "障",
}

_BABA_JOTAI_MAP: dict[tuple[str, str], str] = {
    ("芝", "良"): "芝良",
    ("芝", "稍"): "芝稍",
    ("芝", "重"): "芝重",
    ("芝", "不"): "芝不",
    ("ダ", "良"): "ダ良",
    ("ダ", "稍"): "ダ稍",
    ("ダ", "重"): "ダ重",
    ("ダ", "不"): "ダ不",
    ("障", "良"): "障良",
    ("障", "稍"): "障稍",
    ("障", "重"): "障重",
    ("障", "不"): "障不",
}

_KEIBAJO_TO_DIRECTION: dict[str, str] = {
    "札幌": "右",
    "函館": "右",
    "福島": "右",
    "新潟": "左",
    "東京": "左",
    "中山": "右",
    "中京": "左",
    "京都": "右",
    "阪神": "右",
    "小倉": "右",
    "門別": "右",
    "盛岡": "左",
    "水沢": "右",
    "浦和": "左",
    "船橋": "左",
    "大井": "右",
    "川崎": "左",
    "金沢": "右",
    "笠松": "右",
    "名古屋": "右",
    "園田": "右",
    "姫路": "右",
    "高知": "右",
    "佐賀": "右",
    "帯広": "右",
}


def convert_horse_master(
    past_perf: pd.DataFrame,
    horse_id: str,
    horse_basic_info: pd.DataFrame,
) -> pd.DataFrame:
    """HorsePageScraper出力を統一スキーマに変換する.

    Args:
        past_perf (pd.DataFrame): HorsePageScraper.get_past_performances()の出力
        horse_id (str): 馬ID（血統登録番号）
        horse_basic_info (pd.DataFrame): HorsePageScraper.get_horse_basic_info()の出力

    Returns:
        pd.DataFrame: 統一スキーマに変換されたDataFrame（HORSE_MASTER_COLUMNSのカラム、1行）
    """
    data: dict[str, object] = {}

    if not horse_basic_info.empty:
        info = horse_basic_info.iloc[0]
        data["馬名"] = info.get("馬名", pd.NA)
        bamei = info.get("馬名", "")
        data["馬名半角ｶﾅ"] = to_half_kana(str(bamei)) if pd.notna(bamei) else pd.NA
        seibetsu = str(info.get("性別", "")).strip()
        data["性別コード"] = _SEIBETSU_TO_CODE.get(seibetsu, pd.NA)
        data["生年月日"] = str(info.get("生年月日", pd.NA))
        shozoku = str(info.get("所属", "")).strip()
        if shozoku:
            data["東西所属コード"] = TOZAI_SHOZOKU_TO_CODE.get(shozoku, "3")
        else:
            data["東西所属コード"] = pd.NA
        data["調教師コード"] = info.get("調教師ID", pd.NA)
        data["調教師名略称"] = info.get("調教師", pd.NA)
        seisansha_id = info.get("生産者ID", pd.NA)
        if shozoku == "海外":
            data["生産者コード"] = "00000000"
        elif pd.notna(seisansha_id) and seisansha_id != "":
            data["生産者コード"] = str(seisansha_id) + "00"
        else:
            data["生産者コード"] = pd.NA
        data["生産者名"] = info.get("生産者", pd.NA)
        data["産地名"] = info.get("産地", pd.NA)
        data["馬主コード"] = info.get("馬主ID", pd.NA)
        data["馬主名"] = info.get("馬主", pd.NA)
        data["父馬名"] = info.get("父", pd.NA)
        data["母馬名"] = info.get("母", pd.NA)
        data["父父馬名"] = info.get("父父", pd.NA)
        data["父母馬名"] = info.get("父母", pd.NA)
        data["母父馬名"] = info.get("母父", pd.NA)
        data["母母馬名"] = info.get("母母", pd.NA)

    data["血統登録番号"] = horse_id

    # 着回数
    _init_chaku_cols(data)
    if not past_perf.empty:
        chaku_vals = _build_chaku_values(past_perf)
        data.update(chaku_vals)

    df = pd.DataFrame([data])
    return apply_types(ensure_columns(df, HORSE_MASTER_COLUMNS), HORSE_MASTER_TYPES)


def _get_chaku_key(row: pd.Series) -> str | None:
    """過去成績1行から着順カテゴリを返す.

    取消・除外の場合はNone（カウント対象外）を返す。
    """
    ijo = str(row.get("異常区分", "")).strip()
    if ijo in ("取消", "除外"):
        return None
    chakujun = row.get("着順")
    if pd.isna(chakujun):
        return "着外"
    try:
        pos = int(chakujun)
    except (ValueError, TypeError):
        return "着外"
    if 1 <= pos <= 5:
        return f"{pos}着"
    return "着外"


def _is_chuo(row: pd.Series) -> bool:
    """中央（JRA）レースかどうかを判定する."""
    shusai = str(row.get("主催", "")).strip()
    return shusai == "中央"


def _get_shiba_da(row: pd.Series) -> str | None:
    """芝ダ区分を返す（芝/ダ/障のいずれか）."""
    val = str(row.get("芝ダ", "")).strip()
    if val in _BABA_TYPE_MAP:
        return _BABA_TYPE_MAP[val]
    return None


def _get_direction_prefix(shiba_da: str | None, row: pd.Series) -> str | None:
    """馬場別（方向）プレフィックス（例: 芝右, ダ左, 芝直）を返す."""
    if shiba_da not in ("芝", "ダ"):
        return None
    keibajo = str(row.get("競馬場", "")).strip()
    # 新潟芝1000mは直線コース
    if shiba_da == "芝" and keibajo == "新潟":
        kyori = row.get("距離")
        if not pd.isna(kyori) and int(kyori) == 1000:
            return "芝直"
    direction = _KEIBAJO_TO_DIRECTION.get(keibajo)
    if direction is None:
        return None
    return f"{shiba_da}{direction}"


def _get_baba_jotai_prefix(shiba_da: str | None, row: pd.Series) -> str | None:
    """馬場状態別プレフィックス（例: 芝良, ダ稍）を返す."""
    if shiba_da is None:
        return None
    baba = str(row.get("馬場", "")).strip()
    return _BABA_JOTAI_MAP.get((shiba_da, baba))


def _get_kyori_betsu_prefix(shiba_da: str | None, row: pd.Series) -> str | None:
    """距離別プレフィックス（例: 芝16下, ダ22超）を返す."""
    if shiba_da not in ("芝", "ダ"):
        return None
    kyori = row.get("距離")
    if pd.isna(kyori):
        return None
    dist = int(kyori)
    if shiba_da == "芝":
        if dist <= 1600:
            return "芝16下"
        if dist <= 2200:
            return "芝22下"
        return "芝22超"
    if dist <= 1600:
        return "ダ16下"
    if dist <= 2200:
        return "ダ22下"
    return "ダ22超"


def _count_chaku(
    past_perf: pd.DataFrame,
    mask: pd.Series | None = None,
) -> dict[str, int]:
    """着回数カウント辞書を返す.

    Args:
        past_perf (pd.DataFrame): 過去成績DataFrame
        mask (pd.Series | None): 集計対象行のブールマスク（Noneの場合は全行）

    Returns:
        dict[str, int]: {"1着": n, "2着": n, ..., "着外": n}
    """
    counts: dict[str, int] = {k: 0 for k in _CHAKU_COUNT_KEYS}
    target = past_perf if mask is None else past_perf[mask]
    for _, row in target.iterrows():
        key = _get_chaku_key(row)
        if key is not None:
            counts[key] += 1
    return counts


def _build_chaku_values(
    past_perf: pd.DataFrame,
) -> dict[str, int]:
    """全カテゴリの着回数値辞書を構築する.

    Returns:
        dict[str, int]: カラム名 → 着回数
    """
    result: dict[str, int] = {}

    # 総合（全レース）
    sogo = _count_chaku(past_perf)
    for suf in _CHAKU_SUFFIXES:
        result[f"総合{suf}"] = sogo[suf]

    # 中央合計（JRAのみ）
    chuo_mask = past_perf.apply(_is_chuo, axis=1)
    chuo = _count_chaku(past_perf, chuo_mask)
    for suf in _CHAKU_SUFFIXES:
        result[f"中央合計{suf}"] = chuo[suf]

    # 障害着回数
    shogai_mask = past_perf.apply(lambda r: _get_shiba_da(r) == "障", axis=1) & chuo_mask
    shogai = _count_chaku(past_perf, shogai_mask)
    for suf in _CHAKU_SUFFIXES:
        result[f"障害{suf}"] = shogai[suf]

    # 方向別（芝右/芝左/ダ右/ダ左）: 競馬場から算出
    for _, row in past_perf.iterrows():
        key = _get_chaku_key(row)
        if key is None:
            continue
        if not _is_chuo(row):
            continue
        shiba_da = _get_shiba_da(row)
        prefix = _get_direction_prefix(shiba_da, row)
        if prefix is not None:
            col = f"{prefix}{key}"
            result[col] = result.get(col, 0) + 1

    # 馬場状態別
    for _, row in past_perf.iterrows():
        key = _get_chaku_key(row)
        if key is None:
            continue
        if not _is_chuo(row):
            continue
        shiba_da = _get_shiba_da(row)
        prefix = _get_baba_jotai_prefix(shiba_da, row)
        if prefix is not None:
            col = f"{prefix}{key}"
            result[col] = result.get(col, 0) + 1

    # 距離別
    for _, row in past_perf.iterrows():
        key = _get_chaku_key(row)
        if key is None:
            continue
        if not _is_chuo(row):
            continue
        shiba_da = _get_shiba_da(row)
        prefix = _get_kyori_betsu_prefix(shiba_da, row)
        if prefix is not None:
            col = f"{prefix}{key}"
            result[col] = result.get(col, 0) + 1

    return result


def _init_chaku_cols(data: dict[str, object]) -> None:
    """着回数カラムを0で初期化する."""
    for suf in _CHAKU_SUFFIXES:
        data[f"総合{suf}"] = 0
        data[f"中央合計{suf}"] = 0
        data[f"障害{suf}"] = 0
    for prefix in _BABA_JOTAI_PREFIXES:
        for suf in _CHAKU_SUFFIXES:
            data[f"{prefix}{suf}"] = 0
    for prefix in _KYORI_BETSU_PREFIXES:
        for suf in _CHAKU_SUFFIXES:
            data[f"{prefix}{suf}"] = 0
    # 方向別（芝直/芝右/芝左/ダ直/ダ右/ダ左）は0で初期化
    for prefix in _BABA_BETSU_PREFIXES:
        if prefix == "障害":
            continue
        for suf in _CHAKU_SUFFIXES:
            data[f"{prefix}{suf}"] = 0
