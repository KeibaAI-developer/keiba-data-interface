"""各テーブルの型定義辞書.

SCHEMA.mdに基づく各テーブルのカラム型定義を辞書で提供する。
DataFrame生成時の型変換に使用する。

型マッピング:
    - str → "object"
    - int → "Int64"（pandas nullable integer）
    - float → "Float64"（pandas nullable float）
"""

# レース基本情報テーブルの型定義辞書
RACE_INFO_TYPES: dict[str, str] = {
    "レースコード": "object",
    "開催年": "object",
    "開催月日": "object",
    "競馬場": "object",
    "開催回": "Int64",
    "開催日目": "Int64",
    "レース番号": "Int64",
    "曜日": "object",
    "特別競走番号": "Int64",
    "競走名本題": "object",
    "競走名副題": "object",
    "競走名カッコ内": "object",
    "競走名本題欧字": "object",
    "競走名副題欧字": "object",
    "競走名カッコ内欧字": "object",
    "競走名略称10文字": "object",
    "競走名略称6文字": "object",
    "競走名略称3文字": "object",
    "競走名区分": "object",
    "重賞回次": "Int64",
    "グレード": "object",
    "変更前グレード": "object",
    "競走種別": "object",
    "競走記号": "object",
    "重量種別": "object",
    "競走条件2歳": "object",
    "競走条件3歳": "object",
    "競走条件4歳": "object",
    "競走条件5歳以上": "object",
    "競走条件最若年": "object",
    "競走条件名称": "object",
    "距離": "Int64",
    "変更前距離": "Int64",
    "トラック": "object",
    "変更前トラック": "object",
    "コース区分": "object",
    "変更前コース区分": "object",
    "本賞金1着": "Int64",
    "本賞金2着": "Int64",
    "本賞金3着": "Int64",
    "本賞金4着": "Int64",
    "本賞金5着": "Int64",
    "本賞金6着": "Int64",
    "本賞金7着": "Int64",
    "変更前本賞金1着": "Int64",
    "変更前本賞金2着": "Int64",
    "変更前本賞金3着": "Int64",
    "変更前本賞金4着": "Int64",
    "変更前本賞金5着": "Int64",
    "付加賞金1着": "Int64",
    "付加賞金2着": "Int64",
    "付加賞金3着": "Int64",
    "付加賞金4着": "Int64",
    "付加賞金5着": "Int64",
    "変更前付加賞金1着": "Int64",
    "変更前付加賞金2着": "Int64",
    "変更前付加賞金3着": "Int64",
    "発走時刻": "object",
    "変更前発走時刻": "object",
    "登録頭数": "Int64",
    "出走頭数": "Int64",
    "入線頭数": "Int64",
    "天候": "object",
    "芝馬場状態": "object",
    "ダート馬場状態": "object",
}


# レース結果情報テーブルの型定義辞書
def _generate_race_result_info_types() -> dict[str, str]:
    """レース結果情報テーブルの型定義辞書を生成する."""
    types: dict[str, str] = {"レースコード": "object"}

    # ラップ100m〜5000m: float
    for distance in range(100, 5001, 100):
        types[f"ラップ{distance}m"] = "Float64"

    types["障害マイルタイム"] = "object"
    types["前3ハロン"] = "Float64"
    types["前4ハロン"] = "Float64"
    types["後3ハロン"] = "Float64"
    types["後4ハロン"] = "Float64"
    types["1コーナー"] = "object"
    types["1コーナー周回数"] = "Int64"
    types["1コーナー通過順"] = "object"
    types["2コーナー"] = "object"
    types["2コーナー周回数"] = "Int64"
    types["2コーナー通過順"] = "object"
    types["3コーナー"] = "object"
    types["3コーナー周回数"] = "Int64"
    types["3コーナー通過順"] = "object"
    types["4コーナー"] = "object"
    types["4コーナー周回数"] = "Int64"
    types["4コーナー通過順"] = "object"
    types["レコード更新区分"] = "object"

    return types


RACE_RESULT_INFO_TYPES: dict[str, str] = _generate_race_result_info_types()

# 馬毎レース情報テーブルの型定義辞書
HORSE_RACE_INFO_TYPES: dict[str, str] = {
    "レースコード": "object",
    "開催年": "object",
    "開催月日": "object",
    "競馬場": "object",
    "開催回": "Int64",
    "開催日目": "Int64",
    "レース番号": "Int64",
    "枠番": "Int64",
    "馬番": "Int64",
    "血統登録番号": "object",
    "馬名": "object",
    "馬記号": "object",
    "性別": "object",
    "品種": "object",
    "毛色": "object",
    "馬齢": "Int64",
    "所属": "object",
    "調教師コード": "object",
    "調教師名略称": "object",
    "馬主コード": "object",
    "馬主名": "object",
    "服色標示": "object",
    "負担重量": "Float64",
    "変更前負担重量": "Float64",
    "ブリンカー使用区分": "object",
    "騎手コード": "object",
    "変更前騎手コード": "object",
    "騎手名略称": "object",
    "変更前騎手名略称": "object",
    "騎手見習コード": "object",
    "変更前騎手見習コード": "object",
    "馬体重": "Int64",
    "増減符号": "object",
    "増減差": "Int64",
    "異常区分": "object",
    "入線順位": "Int64",
    "確定着順": "Int64",
    "同着区分": "object",
    "同着頭数": "Int64",
    "走破タイム": "object",
    "着差1": "object",
    "着差2": "object",
    "着差3": "object",
    "1コーナー順位": "Int64",
    "2コーナー順位": "Int64",
    "3コーナー順位": "Int64",
    "4コーナー順位": "Int64",
    "単勝オッズ": "Float64",
    "単勝人気順": "Int64",
    "獲得本賞金": "Int64",
    "獲得付加賞金": "Int64",
    "後4ハロン": "Float64",
    "後3ハロン": "Float64",
    "相手1血統登録番号": "object",
    "相手1馬名": "object",
    "相手2血統登録番号": "object",
    "相手2馬名": "object",
    "相手3血統登録番号": "object",
    "相手3馬名": "object",
    "タイム差": "Float64",
    "レコード更新区分": "object",
    "マイニング区分": "object",
    "マイニング予想走破タイム": "object",
    "マイニング予想誤差プラス": "object",
    "マイニング予想誤差マイナス": "object",
    "マイニング予想順位": "Int64",
    "脚質判定": "object",
}


# 払戻情報テーブルの型定義辞書
def _generate_payoff_types() -> dict[str, str]:
    """払戻情報テーブルの型定義辞書を生成する."""
    types: dict[str, str] = {
        "レースコード": "object",
        "開催年": "object",
        "開催月日": "object",
        "競馬場": "object",
        "開催回": "Int64",
        "開催日目": "Int64",
        "レース番号": "Int64",
        "登録頭数": "Int64",
        "出走頭数": "Int64",
    }

    # 不成立フラグ: str
    for kenshu in ["単勝", "複勝", "枠連", "馬連", "ワイド", "馬単", "3連複", "3連単"]:
        types[f"不成立フラグ{kenshu}"] = "object"

    # 特払フラグ: str
    for kenshu in ["単勝", "複勝", "枠連", "馬連", "ワイド", "馬単", "3連複", "3連単"]:
        types[f"特払フラグ{kenshu}"] = "object"

    # 返還フラグ: str
    for kenshu in ["単勝", "複勝", "枠連", "馬連", "ワイド", "馬単", "3連複", "3連単"]:
        types[f"返還フラグ{kenshu}"] = "object"

    # 返還馬番情報1〜28: str
    for i in range(1, 29):
        types[f"返還馬番情報{i}"] = "object"

    # 返還枠番情報1〜8: str
    for i in range(1, 9):
        types[f"返還枠番情報{i}"] = "object"

    # 返還同枠情報1〜8: str
    for i in range(1, 9):
        types[f"返還同枠情報{i}"] = "object"

    # 単勝1〜3: int
    for i in range(1, 4):
        types[f"単勝{i}馬番"] = "Int64"
        types[f"単勝{i}払戻金"] = "Int64"
        types[f"単勝{i}人気順"] = "Int64"

    # 複勝1〜5: int
    for i in range(1, 6):
        types[f"複勝{i}馬番"] = "Int64"
        types[f"複勝{i}払戻金"] = "Int64"
        types[f"複勝{i}人気順"] = "Int64"

    # 枠連1〜3: int
    for i in range(1, 4):
        types[f"枠連{i}組番1"] = "Int64"
        types[f"枠連{i}組番2"] = "Int64"
        types[f"枠連{i}払戻金"] = "Int64"
        types[f"枠連{i}人気順"] = "Int64"

    # 馬連1〜3: int
    for i in range(1, 4):
        types[f"馬連{i}組番1"] = "Int64"
        types[f"馬連{i}組番2"] = "Int64"
        types[f"馬連{i}払戻金"] = "Int64"
        types[f"馬連{i}人気順"] = "Int64"

    # ワイド1〜7: int
    for i in range(1, 8):
        types[f"ワイド{i}組番1"] = "Int64"
        types[f"ワイド{i}組番2"] = "Int64"
        types[f"ワイド{i}払戻金"] = "Int64"
        types[f"ワイド{i}人気順"] = "Int64"

    # 馬単1〜6: int
    for i in range(1, 7):
        types[f"馬単{i}組番1"] = "Int64"
        types[f"馬単{i}組番2"] = "Int64"
        types[f"馬単{i}払戻金"] = "Int64"
        types[f"馬単{i}人気順"] = "Int64"

    # 3連複1〜3: int
    for i in range(1, 4):
        types[f"3連複{i}組番1"] = "Int64"
        types[f"3連複{i}組番2"] = "Int64"
        types[f"3連複{i}組番3"] = "Int64"
        types[f"3連複{i}払戻金"] = "Int64"
        types[f"3連複{i}人気順"] = "Int64"

    # 3連単1〜6: int
    for i in range(1, 7):
        types[f"3連単{i}組番1"] = "Int64"
        types[f"3連単{i}組番2"] = "Int64"
        types[f"3連単{i}組番3"] = "Int64"
        types[f"3連単{i}払戻金"] = "Int64"
        types[f"3連単{i}人気順"] = "Int64"

    return types


PAYOFF_TYPES: dict[str, str] = _generate_payoff_types()


# 単複オッズ情報テーブルの型定義辞書
ODDS_TYPES: dict[str, str] = {
    "レースコード": "object",
    "開催年": "object",
    "開催月日": "object",
    "競馬場": "object",
    "開催回": "Int64",
    "開催日目": "Int64",
    "レース番号": "Int64",
    "馬番": "Int64",
    "単勝オッズ": "Float64",
    "単勝人気": "Int64",
    "複勝最低オッズ": "Float64",
    "複勝最高オッズ": "Float64",
    "複勝人気": "Int64",
}


# 開催スケジュール情報テーブルの型定義辞書
def _generate_schedule_types() -> dict[str, str]:
    """開催スケジュール情報テーブルの型定義辞書を生成する."""
    types: dict[str, str] = {
        "開催コード": "object",
        "開催年": "object",
        "開催月日": "object",
        "競馬場": "object",
        "開催回": "Int64",
        "開催日目": "Int64",
        "曜日": "object",
    }

    for i in range(1, 4):
        types[f"重賞{i}特別競走番号"] = "Int64"
        types[f"重賞{i}競走名本題"] = "object"
        types[f"重賞{i}競走名略称10文字"] = "object"
        types[f"重賞{i}競走名略称6文字"] = "object"
        types[f"重賞{i}競走名略称3文字"] = "object"
        types[f"重賞{i}重賞回次"] = "Int64"
        types[f"重賞{i}グレード"] = "object"
        types[f"重賞{i}競走種別"] = "object"
        types[f"重賞{i}競走記号"] = "object"
        types[f"重賞{i}重量種別"] = "object"
        types[f"重賞{i}距離"] = "Int64"
        types[f"重賞{i}トラック"] = "object"

    return types


SCHEDULE_TYPES: dict[str, str] = _generate_schedule_types()
