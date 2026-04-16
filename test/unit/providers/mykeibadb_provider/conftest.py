"""MykeibaDBProviderテスト用のfixture."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider

# テスト用レースコード: 2025年05月02日 中山 5回 8日目 11R
RACE_CODE = "2025050206050811"


@pytest.fixture
def race_code() -> str:
    """テスト用16桁レースコード."""
    return RACE_CODE


@pytest.fixture()
def mock_race_getter() -> MagicMock:
    """RaceGetterインスタンスのモックを返すfixture."""
    return MagicMock()


@pytest.fixture()
def mock_odds_getter() -> MagicMock:
    """OddsGetterインスタンスのモックを返すfixture."""
    return MagicMock()


@pytest.fixture()
def mock_race_getter_cls(mock_race_getter: MagicMock) -> Generator[MagicMock, None, None]:
    """RaceGetterをパッチしたモッククラスを返すfixture.

    Yields:
        MagicMock: RaceGetterクラスのパッチモック。
    """
    with patch(
        "keiba_data_interface.providers.mykeibadb_provider.RaceGetter",
        return_value=mock_race_getter,
    ) as mock_cls:
        yield mock_cls


@pytest.fixture()
def mock_odds_getter_cls(mock_odds_getter: MagicMock) -> Generator[MagicMock, None, None]:
    """OddsGetterをパッチしたモッククラスを返すfixture.

    Yields:
        MagicMock: OddsGetterクラスのパッチモック。
    """
    with patch(
        "keiba_data_interface.providers.mykeibadb_provider.OddsGetter",
        return_value=mock_odds_getter,
    ) as mock_cls:
        yield mock_cls


@pytest.fixture()
def provider(
    mock_race_getter_cls: MagicMock,
    mock_odds_getter_cls: MagicMock,
) -> MykeibaDBProvider:
    """テスト用MykeibaDBProviderインスタンス."""
    return MykeibaDBProvider()


def create_race_shosai_df(
    hasso_jikoku: str = "1540",
    henkomae_hasso_jikoku: str = "",
) -> pd.DataFrame:
    """mykeibadb RACE_SHOSAI出力の典型データを生成する.

    Args:
        hasso_jikoku (str): 発走時刻（HHMM形式）
        henkomae_hasso_jikoku (str): 変更前発走時刻

    Returns:
        pd.DataFrame: convert_codes=True時のRACE_SHOSAI出力形式
    """
    return pd.DataFrame(
        [
            {
                "record_shubetsu_id": "RA",
                "data_kubun": "7",
                "data_sakusei_nengappi": "20250502",
                "race_code": RACE_CODE,
                "kaisai_nen": "2025",
                "kaisai_gappi": "0502",
                "keibajo_code": "06",
                "kaisai_kai": 5,
                "kaisai_nichime": 8,
                "race_bango": 11,
                "yobi_code": "1",
                "tokubetsu_kyoso_bango": 8,
                "kyosomei_hondai": "有馬記念",
                "kyosomei_fukudai": "",
                "kyosomei_kakkonai": "グランプリ",
                "kyosomei_hondai_eng": "THE ARIMA KINEN",
                "kyosomei_fukudai_eng": "",
                "kyosomei_kakkonai_eng": "",
                "kyosomei_ryakusho_10": "有馬記念",
                "kyosomei_ryakusho_6": "有馬記念",
                "kyosomei_ryakusho_3": "有馬記",
                "kyosomei_kubun": "3",
                "jusho_kaiji": 70,
                "grade_code": "A",
                "henkomae_grade_code": "",
                "kyoso_shubetsu_code": "13",
                "kyoso_kigo_code": "N01",
                "juryo_shubetsu_code": "4",
                "kyoso_joken_code_2sai": "000",
                "kyoso_joken_code_3sai": "999",
                "kyoso_joken_code_4sai": "999",
                "kyoso_joken_code_5sai_ijo": "999",
                "kyoso_joken_code_saijakunen": "999",
                "kyoso_joken_meisho": "",
                "kyori": 2500,
                "henkomae_kyori": 0,
                "track_code": "17",
                "henkomae_track_code": "00",
                "course_kubun": "A",
                "henkomae_course_kubun": "",
                "honshokin1": 50000000,
                "honshokin2": 20000000,
                "honshokin3": 12500000,
                "honshokin4": 7500000,
                "honshokin5": 5000000,
                "honshokin6": 0,
                "honshokin7": 0,
                "henkomae_honshokin1": 0,
                "henkomae_honshokin2": 0,
                "henkomae_honshokin3": 0,
                "henkomae_honshokin4": 0,
                "henkomae_honshokin5": 0,
                "fukashokin1": 0,
                "fukashokin2": 0,
                "fukashokin3": 0,
                "fukashokin4": 0,
                "fukashokin5": 0,
                "henkomae_fukashokin1": 0,
                "henkomae_fukashokin2": 0,
                "henkomae_fukashokin3": 0,
                "hasso_jikoku": hasso_jikoku,
                "henkomae_hasso_jikoku": henkomae_hasso_jikoku,
                "toroku_tosu": 16,
                "shusso_tosu": 16,
                "nyusen_tosu": 16,
                "tenko_code": "1",
                "shiba_babajotai_code": "1",
                "dirt_babajotai_code": "0",
                # convert_codes=True で追加されるカラム
                "keibajo": "中山",
                "yobi": "日",
                "grade": "GI",
                "kyoso_shubetsu": "サラ系３歳以上",
                "kyoso_kigo": "(国際)(指定)",
                "juryo_shubetsu": "定量",
                "track": "芝・右",
                "tenko": "晴",
                "shiba_babajotai": "良",
                "dirt_babajotai": "",
            }
        ]
    )


def create_umagoto_race_joho_df() -> pd.DataFrame:
    """mykeibadb UMAGOTO_RACE_JOHO出力の典型データを生成する.

    Returns:
        pd.DataFrame: convert_codes=True時のUMAGOTO_RACE_JOHO出力形式（2頭分）
    """
    base = {
        "record_shubetsu_id": "SE",
        "data_kubun": "7",
        "data_sakusei_nengappi": "20250502",
        "race_code": RACE_CODE,
        "kaisai_nen": "2025",
        "kaisai_gappi": "0502",
        "keibajo_code": "06",
        "kaisai_kaiji": 5,
        "kaisai_nichiji": 8,
        "race_bango": 11,
    }
    horse1 = {
        **base,
        "wakuban": 1,
        "umaban": 1,
        "ketto_toroku_bango": "2021105001",
        "bamei": "テスト馬1",
        "umakigo_code": "00",
        "seibetsu_code": "1",
        "hinshu_code": "1",
        "moshoku_code": "04",
        "barei": 4,
        "tozai_shozoku_code": "2",
        "chokyoshi_code": "01159",
        "chokyoshimei_ryakusho": "テスト調教師1",
        "banushi_code": "226800",
        "banushimei_hojinkaku_nashi": "テスト馬主1",
        "fukushoku_hyoji": "黒，赤十字襷",
        "futan_juryo": 580,
        "henkomae_futan_juryo": 0,
        "blinker_shiyo_kubun": "0",
        "kishu_code": "05473",
        "henkomae_kishu_code": "00000",
        "kishumei_ryakusho": "テスト騎手1",
        "henkomae_kishumei_ryakusho": "",
        "kishu_minarai_code": "0",
        "henkomae_kishu_minarai_code": "0",
        "bataiju": 502,
        "zogen_fugo": "+",
        "zogen_sa": 2,
        "ijo_kubun_code": "0",
        "nyusen_juni": 1,
        "kakutei_chakujun": 1,
        "dochaku_kubun": "0",
        "dochaku_tosu": 0,
        "soha_time": "2315",
        "chakusa_code1": "",
        "chakusa_code2": "",
        "chakusa_code3": "",
        "corner1_juni": 11,
        "corner2_juni": 11,
        "corner3_juni": 8,
        "corner4_juni": 3,
        "tansho_odds": 38,
        "tansho_ninkijun": 3,
        "kakutoku_honshokin": 50000000,
        "kakutoku_fukashokin": 35280,
        "kohan_4f": 479,
        "kohan_3f": 346,
        "aite1_ketto_toroku_bango": "2021106787",
        "aite1_bamei": "テスト相手馬",
        "aite2_ketto_toroku_bango": "",
        "aite2_bamei": "",
        "aite3_ketto_toroku_bango": "",
        "aite3_bamei": "",
        "time_sa": -0.1,
        "record_koshin_kubun": "0",
        "mining_kubun": "3",
        "mining_yoso_soha_time": "23324",
        "mining_yoso_gosa_plus": "0066",
        "mining_yoso_gosa_minus": "0088",
        "mining_yoso_juni": 4,
        "kyakushitsu_hantei": "4",
        # convert_codes=True で追加されるカラム
        "keibajo": "中山",
        "umakigo": "",
        "seibetsu": "牡",
        "hinshu": "サラブレッド",
        "moshoku": "鹿毛",
        "tozai_shozoku": "栗東",
        "kishu_minarai": "",
        "ijo_kubun": "",
        "chakusa1": "",
        "chakusa2": "",
        "chakusa3": "",
        "kyakushitsu": "差",
    }
    horse2 = {
        **base,
        "wakuban": 2,
        "umaban": 3,
        "ketto_toroku_bango": "2021105002",
        "bamei": "テスト馬2",
        "umakigo_code": "00",
        "seibetsu_code": "2",
        "hinshu_code": "1",
        "moshoku_code": "01",
        "barei": 4,
        "tozai_shozoku_code": "1",
        "chokyoshi_code": "01160",
        "chokyoshimei_ryakusho": "テスト調教師2",
        "banushi_code": "123456",
        "banushimei_hojinkaku_nashi": "テスト馬主2",
        "fukushoku_hyoji": "白，青菱山形",
        "futan_juryo": 560,
        "henkomae_futan_juryo": 0,
        "blinker_shiyo_kubun": "0",
        "kishu_code": "05474",
        "henkomae_kishu_code": "00000",
        "kishumei_ryakusho": "テスト騎手2",
        "henkomae_kishumei_ryakusho": "",
        "kishu_minarai_code": "0",
        "henkomae_kishu_minarai_code": "0",
        "bataiju": 480,
        "zogen_fugo": "-",
        "zogen_sa": 4,
        "ijo_kubun_code": "0",
        "nyusen_juni": 2,
        "kakutei_chakujun": 2,
        "dochaku_kubun": "0",
        "dochaku_tosu": 0,
        "soha_time": "2316",
        "chakusa_code1": "K__",
        "chakusa_code2": "",
        "chakusa_code3": "",
        "corner1_juni": 5,
        "corner2_juni": 5,
        "corner3_juni": 4,
        "corner4_juni": 2,
        "tansho_odds": 125,
        "tansho_ninkijun": 8,
        "kakutoku_honshokin": 20000000,
        "kakutoku_fukashokin": 0,
        "kohan_4f": 481,
        "kohan_3f": 348,
        "aite1_ketto_toroku_bango": "2021105001",
        "aite1_bamei": "テスト馬1",
        "aite2_ketto_toroku_bango": "",
        "aite2_bamei": "",
        "aite3_ketto_toroku_bango": "",
        "aite3_bamei": "",
        "time_sa": 0.1,
        "record_koshin_kubun": "0",
        "mining_kubun": "3",
        "mining_yoso_soha_time": "23400",
        "mining_yoso_gosa_plus": "0070",
        "mining_yoso_gosa_minus": "0090",
        "mining_yoso_juni": 5,
        "kyakushitsu_hantei": "2",
        # convert_codes=True で追加されるカラム
        "keibajo": "中山",
        "umakigo": "",
        "seibetsu": "牝",
        "hinshu": "サラブレッド",
        "moshoku": "栗毛",
        "tozai_shozoku": "美浦",
        "kishu_minarai": "",
        "ijo_kubun": "",
        "chakusa1": "クビ",
        "chakusa2": "",
        "chakusa3": "",
        "kyakushitsu": "先",
    }
    return pd.DataFrame([horse1, horse2])


def create_race_shosai_with_result_info_df(
    kyori: int = 2000,
) -> pd.DataFrame:
    """mykeibadb RACE_SHOSAI出力のレース結果情報付き典型データを生成する.

    get_race_result_info()テスト用に、ラップタイム・コーナー情報を含む
    RACE_SHOSAIデータを生成する。

    Args:
        kyori (int): レース距離（メートル）

    Returns:
        pd.DataFrame: RACE_SHOSAI出力形式（ラップタイム・コーナー情報付き）
    """
    df = create_race_shosai_df()
    data = df.iloc[0].to_dict()
    data["kyori"] = kyori

    # ラップタイム（0.1秒単位）
    if kyori == 2000:
        # 10ハロン（各200m）
        laps = [129, 118, 119, 121, 120, 119, 121, 119, 118, 116]
    elif kyori == 2500:
        # 先頭100m + 12ハロン（各200m）
        laps = [73, 118, 119, 121, 120, 119, 121, 119, 118, 116, 118, 119, 121]
    else:
        laps = []

    for i in range(1, 26):
        data[f"lap_time{i}"] = laps[i - 1] if i <= len(laps) else 0

    # ハロンタイム（0.1秒単位）
    data["zenhan_3f"] = 366
    data["zenhan_4f"] = 487
    data["kohan_3f"] = 353
    data["kohan_4f"] = 474

    # コーナー情報
    # corner{i}: スロットiに収録されているのが実際に第何コーナーかを示す数値文字列
    # "0"はデータなし。このレースは3,4コーナーのみ（直線コースを持つ短距離など）
    data["corner1"] = "3"
    data["shukaisu1"] = 1
    data["kaku_tsuka_juni1"] = "5-3(1,8)-2-4-6"
    data["corner2"] = "4"
    data["shukaisu2"] = 1
    data["kaku_tsuka_juni2"] = "1-3-5-8-2-4-6"
    data["corner3"] = "0"
    data["shukaisu3"] = 0
    data["kaku_tsuka_juni3"] = "      "
    data["corner4"] = "0"
    data["shukaisu4"] = 0
    data["kaku_tsuka_juni4"] = "      "

    # レコード更新区分
    data["record_koshin_kubun"] = "1"

    return pd.DataFrame([data])


def create_odds1_tansho_df() -> pd.DataFrame:
    """mykeibadb ODDS1_TANSHO出力の典型データを生成する.

    Returns:
        pd.DataFrame: convert_codes=True時のODDS1_TANSHO出力形式（2頭分）
    """
    base = {
        "race_code": RACE_CODE,
        "kaisai_nen": "2025",
        "kaisai_gappi": "0502",
        "keibajo_code": "06",
        "kaisai_kaiji": 5,
        "kaisai_nichiji": 8,
        "race_bango": 11,
        "keibajo": "中山",
    }
    return pd.DataFrame(
        [
            {**base, "umaban": 1, "odds": 38, "ninki": 3},
            {**base, "umaban": 3, "odds": 125, "ninki": 8},
        ]
    )


def create_odds1_fukusho_df() -> pd.DataFrame:
    """mykeibadb ODDS1_FUKUSHO出力の典型データを生成する.

    Returns:
        pd.DataFrame: convert_codes=True時のODDS1_FUKUSHO出力形式（2頭分）
    """
    base = {
        "race_code": RACE_CODE,
        "kaisai_nen": "2025",
        "kaisai_gappi": "0502",
        "keibajo_code": "06",
        "kaisai_kaiji": 5,
        "kaisai_nichiji": 8,
        "race_bango": 11,
        "keibajo": "中山",
    }
    return pd.DataFrame(
        [
            {**base, "umaban": 1, "odds_saitei": 15, "odds_saikou": 22, "ninki": 2},
            {**base, "umaban": 3, "odds_saitei": 45, "odds_saikou": 78, "ninki": 7},
        ]
    )


def create_haraimodoshi_df() -> pd.DataFrame:
    """mykeibadb HARAIMODOSHI出力の典型データを生成する.

    Returns:
        pd.DataFrame: convert_codes=True時のHARAIMODOSHI出力形式（1行）
    """
    data: dict[str, object] = {
        "race_code": RACE_CODE,
        "kaisai_nen": "2025",
        "kaisai_gappi": "0502",
        "keibajo_code": "06",
        "keibajo": "中山",
        "kaisai_kaiji": 5,
        "kaisai_nichiji": 8,
        "race_bango": 11,
        "toroku_tosu": 16,
        "shusso_tosu": 16,
        # 不成立フラグ
        "fuseiritsu_flag_tansho": "0",
        "fuseiritsu_flag_fukusho": "0",
        "fuseiritsu_flag_wakuren": "0",
        "fuseiritsu_flag_umaren": "0",
        "fuseiritsu_flag_wide": "0",
        "fuseiritsu_flag_umatan": "0",
        "fuseiritsu_flag_sanrenpuku": "0",
        "fuseiritsu_flag_sanrentan": "0",
        # 特払フラグ
        "tokubarai_flag_tansho": "0",
        "tokubarai_flag_fukusho": "0",
        "tokubarai_flag_wakuren": "0",
        "tokubarai_flag_umaren": "0",
        "tokubarai_flag_wide": "0",
        "tokubarai_flag_umatan": "0",
        "tokubarai_flag_sanrenpuku": "0",
        "tokubarai_flag_sanrentan": "0",
        # 返還フラグ
        "henkan_flag_tansho": "0",
        "henkan_flag_fukusho": "0",
        "henkan_flag_wakuren": "0",
        "henkan_flag_umaren": "0",
        "henkan_flag_wide": "0",
        "henkan_flag_umatan": "0",
        "henkan_flag_sanrenpuku": "0",
        "henkan_flag_sanrentan": "0",
        # 単勝
        "tansho1_umaban": 5,
        "tansho1_haraimodoshikin": 380,
        "tansho1_ninkijun": 1,
        # 複勝
        "fukusho1_umaban": 5,
        "fukusho1_haraimodoshikin": 150,
        "fukusho1_ninkijun": 1,
        "fukusho2_umaban": 3,
        "fukusho2_haraimodoshikin": 450,
        "fukusho2_ninkijun": 5,
        "fukusho3_umaban": 8,
        "fukusho3_haraimodoshikin": 210,
        "fukusho3_ninkijun": 3,
        # 馬連
        "umaren1_kumiban1": 3,
        "umaren1_kumiban2": 5,
        "umaren1_haraimodoshikin": 2530,
        "umaren1_ninkijun": 7,
        # 3連単
        "sanrentan1_kumiban1": 5,
        "sanrentan1_kumiban2": 3,
        "sanrentan1_kumiban3": 8,
        "sanrentan1_haraimodoshikin": 45680,
        "sanrentan1_ninkijun": 42,
    }
    return pd.DataFrame([data])


def create_kaisai_schedule_df() -> pd.DataFrame:
    """mykeibadb KAISAI_SCHEDULE出力の典型データを生成する.

    Returns:
        pd.DataFrame: convert_codes=True時のKAISAI_SCHEDULE出力形式（2行）
    """
    return pd.DataFrame(
        [
            {
                "kaisai_code": "2025050206050800",
                "kaisai_nen": "2025",
                "kaisai_gappi": "0502",
                "keibajo_code": "06",
                "keibajo": "中山",
                "kaisai_kaiji": 5,
                "kaisai_nichiji": 8,
                "yobi_code": "0",
                "yobi": "日",
                "jusho1_tokubetsu_kyoso_bango": 1234,
                "jusho1_kyosomei_hondai": "皐月賞",
                "jusho1_kyosomei_ryakusho_10": "皐月賞",
                "jusho1_kyosomei_ryakusho_6": "皐月賞",
                "jusho1_kyosomei_ryakusho_3": "皐月",
                "jusho1_jusho_kaiji": 85,
                "jusho1_grade_code": "A",
                "jusho1_kyoso_shubetsu_code": "12",
                "jusho1_kyoso_kigo_code": "N01",
                "jusho1_juryo_shubetsu_code": "4",
                "jusho1_kyori": 2000,
                "jusho1_track_code": "17",
            },
            {
                "kaisai_code": "2025050205050800",
                "kaisai_nen": "2025",
                "kaisai_gappi": "0502",
                "keibajo_code": "05",
                "keibajo": "東京",
                "kaisai_kaiji": 5,
                "kaisai_nichiji": 8,
                "yobi_code": "0",
                "yobi": "日",
            },
        ]
    )
