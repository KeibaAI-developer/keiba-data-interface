"""統合テスト用のカラム定義.

SCHEMA.mdに基づくscraping○カラムと、既知のデータソース差異カラムを定義する。
"""

from keiba_data_interface.schema.columns import WIN_SHOW_ODDS_COLUMNS

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
KNOWN_DIFF_RACE_RESULT_INFO: set[str] = {
    "後3ハロン",  # 障害レースはnetkeibaでラップタイムが公開されないためscrapingではNaN
    "後4ハロン",  # 障害レースはnetkeibaでラップタイムが公開されないためscrapingではNaN
}
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
    "後3ハロン",
    "後4ハロン",
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

# HorsePageScraperのみ対応するscraping○カラム
PAST_PERF_ADDITIONAL_SCRAPING_COLUMNS: list[str] = [
    "相手1馬名",
]

# get_past_performances時にscraping非対応のため除外するカラム
# (着差コード1はscrapingの着差カラムはタイム差として使用するため、着差コード1は常にNaNになる)
# (調教師名略称は表記ゆれがあるため除外)
PAST_PERF_EXCLUDE: set[str] = {
    "着差コード1",
    "調教師名略称",
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
ODDS_SCRAPING_COLUMNS: list[str] = WIN_SHOW_ODDS_COLUMNS

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


# ============================================================================
# 競走馬情報
# ============================================================================


def _build_horse_master_known_diff() -> set[str]:
    """競走馬情報の既知差分カラムセットを生成する."""
    chaku_sfx = ["1着", "2着", "3着", "4着", "5着", "着外"]
    cols: set[str] = {
        "調教師コード",  # 転厩後はscrapingは現在の調教師、mykeibadbはマスタ登録時の情報
        "調教師名略称",  # 表記ゆれあり
        "生産者コード",  # 外国馬はscrapingが独自変換、mykeibadbは00000000
        "生産者名",  # 表記ゆれあり（法人格有無の差異）
        "馬主名",  # 表記ゆれあり（法人格有無の差異・スペース挿入の差異）
        "東西所属コード",  # 地方馬は地方ページからコード取得不可のためscrapingはNaN
        "父父馬名",  # 外国馬はmykeibadbに日本語馬名なし（空文字列）
        "父母馬名",  # 外国馬はmykeibadbに日本語馬名なし（空文字列）
    }
    # 着回数系: scrapingはHTML表示件数（直近50走程度）から算出、mykeibadbは全件
    for prefix in ["総合", "中央合計", "障害"]:
        for suf in chaku_sfx:
            cols.add(f"{prefix}{suf}")
    # 方向別着回数も同様にHTML表示件数の差分が発生
    for direction in ["右", "左"]:
        for shiba_da in ["芝", "ダ"]:
            for suf in chaku_sfx:
                cols.add(f"{shiba_da}{direction}{suf}")
    # 障害馬場状態別着回数（scrapingは障害の詳細馬場状態が取得困難）
    for jotai in ["良", "稍", "重", "不"]:
        for suf in ["1着", "2着", "3着", "4着", "5着", "着外"]:
            cols.add(f"障{jotai}{suf}")
    return cols


KNOWN_DIFF_HORSE_MASTER: set[str] = _build_horse_master_known_diff()


def _build_horse_master_scraping_columns() -> list[str]:
    """競走馬情報のscraping○カラムリストを生成する."""
    chaku_sfx = ["1着", "2着", "3着", "4着", "5着", "着外"]
    cols: list[str] = [
        "血統登録番号",
        "生年月日",
        "馬名",
        "馬名半角ｶﾅ",
        "性別コード",
        "父馬名",
        "母馬名",
        "父父馬名",
        "父母馬名",
        "母父馬名",
        "母母馬名",
        "東西所属コード",
        "調教師コード",
        "調教師名略称",
        "生産者コード",
        "生産者名",
        "産地名",
        "馬主コード",
        "馬主名",
    ]
    for prefix in ["総合", "中央合計", "障害"]:
        for suf in chaku_sfx:
            cols.append(f"{prefix}{suf}")
    # 方向別（直線・右回り・左回り）: 競馬場から算出
    # 芝直: 新潟芝1000mのみ算出可能 / ダ直: 中央に存在しないため常に0
    for prefix in ["芝直", "芝右", "芝左", "ダ直", "ダ右", "ダ左"]:
        for suf in chaku_sfx:
            cols.append(f"{prefix}{suf}")
    # 馬場状態別
    for prefix in [
        "芝良",
        "芝稍",
        "芝重",
        "芝不",
        "ダ良",
        "ダ稍",
        "ダ重",
        "ダ不",
        "障良",
        "障稍",
        "障重",
        "障不",
    ]:
        for suf in chaku_sfx:
            cols.append(f"{prefix}{suf}")
    # 距離別
    for prefix in ["芝16下", "芝22下", "芝22超", "ダ16下", "ダ22下", "ダ22超"]:
        for suf in chaku_sfx:
            cols.append(f"{prefix}{suf}")
    return cols


HORSE_MASTER_SCRAPING_COLUMNS: list[str] = _build_horse_master_scraping_columns()
