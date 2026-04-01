"""統合テスト用のカラム定義.

SCHEMA.mdに基づくscraping○カラムと、既知のデータソース差異カラムを定義する。
"""

from keiba_data_interface.schema.columns import ODDS_COLUMNS

# ============================================================================
# 既知のデータソース差異（値一致比較から除外するカラム）
# ============================================================================

# scrapingとmykeibadbでデータソースの表現が異なるため値一致比較から除外するカラム。
# 各差異の理由:
#   競走名本題: scraping=通称（例:日本ダービー）vs mykeibadb=正式名称（例:東京優駿）
#   グレード: scraping=G1 vs mykeibadb=GI（表記差異）
#   競走種別: scraping=○○ vs mykeibadb=（JRA-VANコード変換後名称の差異）
#   競走記号: 同上
#   重量種別: 同上
#   コース区分: scrapingは文字列、mykeibadbはコード変換後名称で差異あり
KNOWN_DIFF_RACE_INFO: set[str] = {
    "競走名本題",
    "グレード",
    "競走種別",
    "競走記号",
    "重量種別",
    "コース区分",
    "競走条件名称",  # mykeibadb converterが未対応でNAを返す
    "トラック",  # scraping="芝左" vs mykeibadb="芝・左"（変換フォーマット差異）
    "本賞金1着",  # netkeibaとJRA-VANで賞金データが異なる場合がある
    "本賞金2着",
    "本賞金3着",
    "本賞金4着",
    "本賞金5着",
    "芝馬場状態",  # scraping=NA vs mykeibadb=空文字（該当トラックなし時の表現差異）
    "ダート馬場状態",  # 同上
    "曜日",  # scraping="日" vs mykeibadb="祝"（祝日の表現差異）
    "出走頭数",  # 取消/除外馬をカウントに含むかの差異
}
KNOWN_DIFF_HORSE_RACE: set[str] = {
    "所属コード",  # past_perf: scrapingが取得していないカラム（NaN差異）
    "調教師名略称",  # 略称の長さが異なる
    "騎手名略称",  # 略称の長さが異なる
    "着差1",  # scraping="1/2" vs mykeibadb="1/2馬身"
    "獲得本賞金",  # scrapingは賞金なし=NA vs mykeibadb=0
    "タイム差",  # 単位差異（scraping=秒, mykeibadb=0.1秒単位）
    "増減差",  # mykeibadbは「計測不能」を999で表現、scrapingはNA
    "増減符号",  # scraping=NaN vs mykeibadb=空文字（馬体重未発表時の表現差異）
    "異常区分コード",  # mykeibadb=4以上（競走中止等）をscraping側と同様に0に正規化済み
    "1コーナー順位",  # 異常馬(競走中止等)時にscraping=NaN vs mykeibadb=0
    "2コーナー順位",  # 同上
    "3コーナー順位",  # 同上
    "4コーナー順位",  # 同上
    "単勝オッズ",  # 異常馬(出走取消等)時にscraping=NaN vs mykeibadb=0
    "単勝人気順",  # 異常馬時のデータソース差異、同率人気の扱い差異
    "後3ハロン",  # 異常馬(競走中止等)時にscraping=NaN vs mykeibadb=99.9
    "確定着順",  # 異常馬(競走中止等)時にscraping=NaN vs mykeibadb=0
    "走破タイム",  # 異常馬(競走中止等)時にscraping=NaN vs mykeibadb="0000"
    "馬体重",  # 出走取消時にscraping=NaN vs mykeibadb=0
    "相手1馬名",  # scraping="(馬名)" vs mykeibadb="馬名"（括弧有無差異）
    "調教師コード",  # past_perf: scrapingが取得していないカラム（NaN差異）
    "馬名",  # past_perf: scrapingが取得していないカラム（NaN差異）
    "馬齢",  # past_perf: scrapingが取得していないカラム（NaN差異）
    "性別コード",  # past_perf: scrapingが取得していないカラム（NaN差異）
}
KNOWN_DIFF_RACE_RESULT_INFO: set[str] = {
    "1コーナー",  # scraping converterがコーナー値（数字）を取得していない
    "2コーナー",
    "3コーナー",
    "4コーナー",
    "1コーナー通過順",  # scraping=NaN（1000m直線等でコーナーなし時）、フォーマット差異
    "2コーナー通過順",  # 同上
    "3コーナー通過順",  # 同上。障害レースではJRA-VANが空白を返す
    "4コーナー通過順",  # 同上
}
KNOWN_DIFF_PAYOFF: set[str] = {
    "出走頭数",  # scraping converterが出走頭数を取得していない
    "複勝1人気順",  # netkeibaとJRA-VANで同率人気の扱いが異なる場合がある
    "複勝2人気順",  # 同上
    "複勝3人気順",  # 同上
    "単勝1人気順",  # 同上
    "馬単1人気順",  # 同上
    "3連複1人気順",  # 同上
    "ワイド1人気順",  # 同上
    "ワイド2人気順",  # 同上
    "ワイド3人気順",  # 同上
    "枠連1組番1",  # 少頭数レースでscraping=NaN vs mykeibadb=0
    "枠連1組番2",  # 同上
    "複勝3馬番",  # 少頭数レース等でscraping=NaN vs mykeibadb=0
}

# ============================================================================
# scraping ○ カラム定義（SCHEMA.mdに基づく）
# ============================================================================

# テーブル1: レース基本情報
RACE_INFO_SCRAPING_COLUMNS: list[str] = [
    "レースコード",
    "開催年",
    "開催月日",
    "競馬場",
    "開催回",
    "開催日目",
    "レース番号",
    "曜日",
    "競走名本題",
    "グレード",
    "競走種別",
    "競走記号",
    "重量種別",
    "競走条件名称",
    "距離",
    "トラック",
    "コース区分",
    "本賞金1着",
    "本賞金2着",
    "本賞金3着",
    "本賞金4着",
    "本賞金5着",
    "発走時刻",
    "出走頭数",
    "天候",
    "芝馬場状態",
    "ダート馬場状態",
]

# テーブル2: レース結果情報
# 注意: SCHEMA.mdでは前3ハロン/後3ハロンがscraping=○だが、
# scrapingのget_lap_time()にレース前3F/レース後3Fカラムが存在しないため
# scraping converterは常にNaNを返す。値比較の対象外とする。
RACE_RESULT_INFO_SCRAPING_COLUMNS: list[str] = [
    "レースコード",
    *[f"ラップ{d}m" for d in range(100, 5001, 100)],
    "1コーナー",
    "1コーナー通過順",
    "2コーナー",
    "2コーナー通過順",
    "3コーナー",
    "3コーナー通過順",
    "4コーナー",
    "4コーナー通過順",
]

# テーブル3: 馬毎レース情報（get_entry / get_result共通）
HORSE_RACE_INFO_SCRAPING_COLUMNS: list[str] = [
    "レースコード",
    "開催年",
    "開催月日",
    "競馬場",
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
    "着差1",
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
    "着差1",
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


# テーブル4: 払戻情報（scraping ○ カラム）
def _build_payoff_scraping_columns() -> list[str]:
    """払戻情報のscraping○カラムを生成する."""
    cols: list[str] = [
        "レースコード",
        "開催年",
        "開催月日",
        "競馬場",
        "開催回",
        "開催日目",
        "レース番号",
        "出走頭数",
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

# テーブル5: 単複オッズ情報（全カラムが scraping ○）
ODDS_SCRAPING_COLUMNS: list[str] = ODDS_COLUMNS

# テーブル6: 開催スケジュール情報
SCHEDULE_SCRAPING_COLUMNS: list[str] = [
    "開催コード",
    "開催年",
    "開催月日",
    "競馬場",
    "開催回",
    "開催日目",
]
