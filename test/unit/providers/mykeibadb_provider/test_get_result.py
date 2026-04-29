"""MykeibaDBProvider.get_result関数のテスト."""

from unittest.mock import MagicMock

import pandas as pd

from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider
from keiba_data_interface.schema.columns import RACE_INFO_BY_HORSE_COLUMNS

from .conftest import RACE_CODE, create_umagoto_race_joho_df


def _create_niigata_straight_joho_df() -> pd.DataFrame:
    """新潟芝直線1000m レースのUMAGOTO_RACE_JOHO出力を生成する（3頭分）.

    soha_time - kohan_3f の昇順ランクで4コーナー順位を算出する検証用。
    前半タイム: 馬A=210, 馬B=220, 馬B'=220, 馬C=230 → ランク: 1,2,2,4
    """
    base = {
        "record_shubetsu_id": "SE",
        "data_kubun": "7",
        "data_sakusei_nengappi": "20250803",
        "race_code": RACE_CODE,
        "kaisai_nen": "2025",
        "kaisai_gappi": "0803",
        "keibajo_code": "04",  # 新潟
        "kaisai_kaiji": 2,
        "kaisai_nichiji": 4,
        "race_bango": 7,
        "wakuban": 1,
        "umaban": 1,
        "ketto_toroku_bango": "2021000001",
        "bamei": "テスト馬A",
        "umakigo_code": "00",
        "seibetsu_code": "1",
        "hinshu_code": "1",
        "moshoku_code": "01",
        "barei": 3,
        "tozai_shozoku_code": "1",
        "chokyoshi_code": "01001",
        "chokyoshimei_ryakusho": "テスト調教師",
        "banushi_code": "111111",
        "banushimei_hojinkaku_nashi": "テスト馬主",
        "fukushoku_hyoji": "白",
        "futan_juryo": 540,
        "henkomae_futan_juryo": 0,
        "blinker_shiyo_kubun": "0",
        "kishu_code": "05001",
        "henkomae_kishu_code": "00000",
        "kishumei_ryakusho": "テスト騎手",
        "henkomae_kishumei_ryakusho": "",
        "kishu_minarai_code": "0",
        "henkomae_kishu_minarai_code": "0",
        "bataiju": 450,
        "zogen_fugo": "0",
        "zogen_sa": 0,
        "ijo_kubun_code": "0",
        "nyusen_juni": 1,
        "kakutei_chakujun": 1,
        "dochaku_kubun": "0",
        "dochaku_tosu": 0,
        "chakusa_code1": "",
        "chakusa_code2": "",
        "chakusa_code3": "",
        # 直線コース: コーナー通過順位は全て"00"
        "corner1_juni": "00",
        "corner2_juni": "00",
        "corner3_juni": "00",
        "corner4_juni": "00",
        "tansho_odds": 80,
        "tansho_ninkijun": 1,
        "kakutoku_honshokin": 3000000,
        "kakutoku_fukashokin": 0,
        "kohan_4f": 420,
        "aite1_ketto_toroku_bango": "",
        "aite1_bamei": "",
        "aite2_ketto_toroku_bango": "",
        "aite2_bamei": "",
        "aite3_ketto_toroku_bango": "",
        "aite3_bamei": "",
        "time_sa": 0,
        "record_koshin_kubun": "0",
        "mining_kubun": "0",
        "mining_yoso_soha_time": "0",
        "mining_yoso_gosa_plus": "0",
        "mining_yoso_gosa_minus": "0",
        "mining_yoso_juni": 0,
        "kyakushitsu_hantei": "1",
    }
    rows = [
        # 馬A: soha_time=530, kohan_3f=320 → 前半=210 → ランク1
        {**base, "umaban": 1, "kakutei_chakujun": 1, "soha_time": "0530", "kohan_3f": 320},
        # 馬B: soha_time=540, kohan_3f=320 → 前半=220 → ランク2（B'と同着）
        {**base, "umaban": 2, "kakutei_chakujun": 2, "soha_time": "0540", "kohan_3f": 320},
        # 馬B': soha_time=545, kohan_3f=325 → 前半=220 → ランク2（Bと同着）
        {**base, "umaban": 3, "kakutei_chakujun": 3, "soha_time": "0545", "kohan_3f": 325},
        # 馬C: soha_time=550, kohan_3f=320 → 前半=230 → ランク4
        {**base, "umaban": 4, "kakutei_chakujun": 4, "soha_time": "0550", "kohan_3f": 320},
    ]
    return pd.DataFrame(rows)


# 正常系
def test_output_columns_match_schema(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """出力DataFrameのカラム構成がHORSE_RACE_INFO_COLUMNSと一致する."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    result = provider.get_result(race_code)

    assert list(result.columns) == RACE_INFO_BY_HORSE_COLUMNS


def test_output_row_count(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """出力DataFrameの行数が入力と一致する."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    result = provider.get_result(race_code)

    assert len(result) == 2


def test_race_getter_called_with_correct_args(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """RaceGetter.get_umagoto_race_joho()が正しい引数で呼ばれる."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    provider.get_result(race_code)

    mock_race_getter.get_umagoto_race_joho.assert_called_once_with(
        race_code=race_code, convert_codes=False
    )


def test_soha_time_converted(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """走破タイムが"MSSS"から"M:SS.S"に変換される."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    result = provider.get_result(race_code)

    assert result.iloc[0]["走破タイム"] == "2:31.5"
    assert result.iloc[1]["走破タイム"] == "2:31.6"


def test_soha_time_zero_not_converted(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """走破タイムが"0000"の場合はNaNに変換される."""
    raw = create_umagoto_race_joho_df()
    raw.at[0, "soha_time"] = "0000"
    mock_race_getter.get_umagoto_race_joho.return_value = raw

    result = provider.get_result(race_code)

    # "0000"はint値で0と扱われ、タイム未計測（競走中止等）としてNaNに変換される
    assert pd.isna(result.iloc[0]["走破タイム"])


def test_soha_time_nan_preserved(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """走破タイムがNaNの場合はそのまま保持される."""
    raw = create_umagoto_race_joho_df()
    raw.at[0, "soha_time"] = pd.NA
    mock_race_getter.get_umagoto_race_joho.return_value = raw

    result = provider.get_result(race_code)

    assert pd.isna(result.iloc[0]["走破タイム"])


def test_futan_juryo_converted(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """負担重量の変換がget_entryと同様に行われる."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    result = provider.get_result(race_code)

    assert result.iloc[0]["負担重量"] == 58.0
    assert result.iloc[1]["負担重量"] == 56.0


def test_tansho_odds_converted(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """単勝オッズの変換がget_entryと同様に行われる."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    result = provider.get_result(race_code)

    assert result.iloc[0]["単勝オッズ"] == 3.8
    assert result.iloc[1]["単勝オッズ"] == 12.5


def test_kohan_3f_converted(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """後3ハロンの変換がget_entryと同様に行われる."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    result = provider.get_result(race_code)

    assert result.iloc[0]["後3ハロン"] == 34.6
    assert result.iloc[1]["後3ハロン"] == 34.8


def test_kohan_4f_converted(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """後4ハロンが0.1秒単位から秒単位に変換される."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    result = provider.get_result(race_code)

    assert result.iloc[0]["後4ハロン"] == 47.9
    assert result.iloc[1]["後4ハロン"] == 48.1


def test_kohan_4f_zero_to_nan(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """後4ハロンが0（データなし）の場合はNaNに変換される."""
    raw = create_umagoto_race_joho_df()
    raw.at[0, "kohan_4f"] = 0
    mock_race_getter.get_umagoto_race_joho.return_value = raw

    result = provider.get_result(race_code)

    assert pd.isna(result.iloc[0]["後4ハロン"])
    assert result.iloc[1]["後4ハロン"] == 48.1


def test_result_specific_columns(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """結果固有のカラム（着順・コーナー順位等）が正しく変換される."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    result = provider.get_result(race_code)

    row = result.iloc[0]
    assert row["確定着順"] == 1
    assert row["1コーナー順位"] == 11
    assert row["4コーナー順位"] == 3
    assert row["単勝人気順"] == 1
    assert row["獲得本賞金"] == 50000000


def test_kakutei_chakujun_zero_to_nan(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """確定着順が0のDB値（出走取消等）はNaNに変換される."""
    raw = create_umagoto_race_joho_df()
    raw.at[0, "kakutei_chakujun"] = 0
    mock_race_getter.get_umagoto_race_joho.return_value = raw

    result = provider.get_result(race_code)

    # kakutei_chakujun=0の馬（馬番1）のみNaNに変換される
    horse1_chakujun = result.loc[result["馬番"] == 1, "確定着順"].iloc[0]
    assert pd.isna(horse1_chakujun)


# ---------------------------------------------------------------------------
# 正常系: 新潟芝直線1000m の4コーナー順位
# ---------------------------------------------------------------------------


def test_niigata_straight_4corner_rank_calc(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """新潟芝直線1000mでは4コーナー順位が前半タイム（走破タイム-後3ハロン）の昇順ランクで算出される."""
    mock_race_getter.get_umagoto_race_joho.return_value = _create_niigata_straight_joho_df()

    result = provider.get_result(race_code)

    # 前半タイム: 馬A=210 → 1位, 馬B=220 → 2位(同着), 馬B'=220 → 2位(同着), 馬C=230 → 4位
    assert result[result["馬番"] == 1].iloc[0]["4コーナー順位"] == 1
    assert result[result["馬番"] == 2].iloc[0]["4コーナー順位"] == 2
    assert result[result["馬番"] == 3].iloc[0]["4コーナー順位"] == 2
    assert result[result["馬番"] == 4].iloc[0]["4コーナー順位"] == 4


def test_niigata_straight_1to3corner_nan(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """新潟芝直線1000mでは1〜3コーナー順位がNaNになる."""
    mock_race_getter.get_umagoto_race_joho.return_value = _create_niigata_straight_joho_df()

    result = provider.get_result(race_code)

    for col in ["1コーナー順位", "2コーナー順位", "3コーナー順位"]:
        assert result[col].isna().all(), f"{col} がNaNではありません"


def test_non_niigata_corner_not_affected(
    provider: MykeibaDBProvider,
    mock_race_getter: MagicMock,
    race_code: str,
) -> None:
    """新潟以外のレースでは4コーナー順位が前半タイム計算の影響を受けない."""
    mock_race_getter.get_umagoto_race_joho.return_value = create_umagoto_race_joho_df()

    result = provider.get_result(race_code)

    # keibajo_code="06"（中山）のレースは通常の変換（0→NaN以外は元の値）
    assert result.iloc[0]["4コーナー順位"] == 3
