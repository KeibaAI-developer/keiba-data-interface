"""統合テスト用のカラム定義.

SCHEMA.mdに基づくscraping○カラムと、既知のデータソース差異カラムを定義する。
"""

from keiba_data_interface.schema.columns import ODDS_COLUMNS

# ============================================================================
# 既知のデータソース差異（値一致比較から除外するカラム）
# SCHEMA.md の「差分A: プロバイダー間の既知差分」に対応する。
# ============================================================================

KNOWN_DIFF_RACE_INFO: set[str] = {
    "曜日コード",  # mykeibadbでは祝日の場合"3"になる
    "競走名本題",  # 表記ゆれあり
    "グレードコード",  # scrapingでは特別競走と一般競走を区別できない場合あり
    "コース区分",  # scrapingでは障害のコース区分は不明
    "本賞金1着",  # scrapingとmykeibadbで賞金データが若干異なる場合がある
    "本賞金2着",
    "本賞金3着",
    "本賞金4着",
    "本賞金5着",
}
KNOWN_DIFF_RACE_RESULT_INFO: set[str] = set()
KNOWN_DIFF_HORSE_RACE: set[str] = {
    # entry/result
    "調教師名略称",  # 表記ゆれあり
    "騎手名略称",  # 表記ゆれあり
    "獲得本賞金",  # scrapingとmykeibadbで賞金データが若干異なる場合がある
    "着差コード1",  # 同着・失格・降着時に表現が異なる
    # past_performances
    "増減差",  # 前走が海外で計測不能のときはNaNが正しいがscrapingでは0になる
    "4コーナー順位",  # 千直の場合mykeibadbではNaN
    "タイム差",  # 失格の場合scrapingではNaNになる
}


def _build_payoff_known_diff() -> set[str]:
    """払戻情報の既知差分カラムセットを生成する.

    同オッズの場合にnetkeibaとJRA-VANで人気順が上下する場合がある。
    """
    cols: set[str] = set()
    for i in range(1, 4):
        cols.add(f"単勝{i}人気順")
    for i in range(1, 6):
        cols.add(f"複勝{i}人気順")
    for i in range(1, 4):
        cols.add(f"枠連{i}人気順")
    for i in range(1, 4):
        cols.add(f"馬連{i}人気順")
    for i in range(1, 8):
        cols.add(f"ワイド{i}人気順")
    for i in range(1, 7):
        cols.add(f"馬単{i}人気順")
    for i in range(1, 4):
        cols.add(f"3連複{i}人気順")
    for i in range(1, 7):
        cols.add(f"3連単{i}人気順")
    return cols


KNOWN_DIFF_PAYOFF: set[str] = _build_payoff_known_diff()

KNOWN_DIFF_ODDS: set[str] = {
    "単勝人気",  # 同オッズの場合人気順が上下する場合がある
    "複勝人気",  # 同オッズの場合人気順が上下する場合がある
}

# ============================================================================
# scraping ○ カラム定義（SCHEMA.mdに基づく）
# ============================================================================

# レース基本情報
RACE_INFO_SCRAPING_COLUMNS: list[str] = [
    "レースコード",
    "開催年",
    "開催月日",
    "競馬場コード",
    "開催回",
    "開催日目",
    "レース番号",
    "曜日コード",
    "競走名本題",
    "グレードコード",
    "競走種別コード",
    "競走記号コード",
    "重量種別コード",
    "競走条件コード",
    "距離",
    "レース種別",
    "芝ダ",
    "左右",
    "内外",
    "コース区分",
    "本賞金1着",
    "本賞金2着",
    "本賞金3着",
    "本賞金4着",
    "本賞金5着",
    "発走時刻",
    "登録頭数",
    "天候コード",
    "芝馬場状態コード",
    "ダート馬場状態コード",
]

# レース結果情報
RACE_RESULT_INFO_SCRAPING_COLUMNS: list[str] = [
    "レースコード",
    *[f"ラップ{d}m" for d in range(100, 5001, 100)],
    "前3ハロン",
    "後3ハロン",
    "1コーナー通過順",
    "2コーナー通過順",
    "3コーナー通過順",
    "4コーナー通過順",
]

# 馬毎レース情報（get_entry / get_result共通）
HORSE_RACE_INFO_SCRAPING_COLUMNS: list[str] = [
    "レースコード",
    "開催年",
    "開催月日",
    "競馬場コード",
    "開催回",
    "開催日目",
    "レース番号",
    "枠番",
    "馬番",
    "血統登録番号",
    "馬名",
    "性別コード",
    "馬齢",
    "所属コード",
    "調教師コード",
    "調教師名略称",
    "負担重量",
    "騎手コード",
    "騎手名略称",
    "馬体重",
    "増減符号",
    "増減差",
    "異常区分コード",
    "確定着順",
    "走破タイム",
    "着差コード1",
    "1コーナー順位",
    "2コーナー順位",
    "3コーナー順位",
    "4コーナー順位",
    "単勝オッズ",
    "単勝人気順",
    "獲得本賞金",
    "後3ハロン",
    "タイム差",
]

# get_entry時は結果系カラムが存在しないため除外する
ENTRY_ONLY_EXCLUDE: set[str] = {
    "確定着順",
    "走破タイム",
    "着差コード1",
    "1コーナー順位",
    "2コーナー順位",
    "3コーナー順位",
    "4コーナー順位",
    "単勝オッズ",
    "単勝人気順",
    "獲得本賞金",
    "後3ハロン",
    "タイム差",
    "馬体重",
    "増減符号",
    "増減差",
}

# PastPerformancesScraperのみ対応するscraping○カラム
PAST_PERF_ADDITIONAL_SCRAPING_COLUMNS: list[str] = [
    "相手1馬名",
]

# get_past_performances時にscraping非対応のため除外するカラム
# (着差コード1はscrapingの着差カラムはタイム差として使用するため、着差コード1は常にNaNになる)
# (性別コード・所属コード・馬齢・調教師コード・調教師名略称・馬名はPastPerformancesScraperが取得しない)
PAST_PERF_EXCLUDE: set[str] = {
    "着差コード1",
    "性別コード",
    "所属コード",
    "馬齢",
    "調教師コード",
    "調教師名略称",
    "馬名",
}


# 払戻情報
def _build_payoff_scraping_columns() -> list[str]:
    """払戻情報のscraping○カラムを生成する."""
    cols: list[str] = [
        "レースコード",
        "開催年",
        "開催月日",
        "競馬場コード",
        "開催回",
        "開催日目",
        "レース番号",
    ]
    # 単勝1〜3
    for i in range(1, 4):
        cols.extend([f"単勝{i}馬番", f"単勝{i}払戻金", f"単勝{i}人気順"])
    # 複勝1〜5
    for i in range(1, 6):
        cols.extend([f"複勝{i}馬番", f"複勝{i}払戻金", f"複勝{i}人気順"])
    # 枠連1〜3
    for i in range(1, 4):
        cols.extend([f"枠連{i}組番1", f"枠連{i}組番2", f"枠連{i}払戻金", f"枠連{i}人気順"])
    # 馬連1〜3
    for i in range(1, 4):
        cols.extend([f"馬連{i}組番1", f"馬連{i}組番2", f"馬連{i}払戻金", f"馬連{i}人気順"])
    # ワイド1〜7
    for i in range(1, 8):
        cols.extend([f"ワイド{i}組番1", f"ワイド{i}組番2", f"ワイド{i}払戻金", f"ワイド{i}人気順"])
    # 馬単1〜6
    for i in range(1, 7):
        cols.extend([f"馬単{i}組番1", f"馬単{i}組番2", f"馬単{i}払戻金", f"馬単{i}人気順"])
    # 3連複1〜3
    for i in range(1, 4):
        cols.extend(
            [
                f"3連複{i}組番1",
                f"3連複{i}組番2",
                f"3連複{i}組番3",
                f"3連複{i}払戻金",
                f"3連複{i}人気順",
            ]
        )
    # 3連単1〜6
    for i in range(1, 7):
        cols.extend(
            [
                f"3連単{i}組番1",
                f"3連単{i}組番2",
                f"3連単{i}組番3",
                f"3連単{i}払戻金",
                f"3連単{i}人気順",
            ]
        )
    return cols


PAYOFF_SCRAPING_COLUMNS: list[str] = _build_payoff_scraping_columns()

# 単複オッズ情報
ODDS_SCRAPING_COLUMNS: list[str] = ODDS_COLUMNS

# 開催スケジュール情報
SCHEDULE_SCRAPING_COLUMNS: list[str] = [
    "開催コード",
    "開催年",
    "開催月日",
    "競馬場コード",
    "開催回",
    "開催日目",
]

KNOWN_DIFF_SCHEDULE: set[str] = set()
