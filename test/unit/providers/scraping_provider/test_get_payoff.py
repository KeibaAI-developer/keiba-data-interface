"""ScrapingProvider.get_payoff関数のテスト."""

from unittest.mock import MagicMock

import pandas as pd

from keiba_data_interface.providers.scraping_provider import ScrapingProvider
from keiba_data_interface.schema.columns import PAYOFF_COLUMNS


def _create_win_payoff() -> pd.DataFrame:
    """単勝払い戻しのモックDataFrameを生成する."""
    return pd.DataFrame(
        [
            {
                "レースID": "202506021211",
                "単勝払戻金_1": 350,
                "単勝馬番_1": 3,
                "単勝人気_1": 1,
                "単勝払戻金_2": None,
                "単勝馬番_2": None,
                "単勝人気_2": None,
                "単勝払戻金_3": None,
                "単勝馬番_3": None,
                "単勝人気_3": None,
            }
        ]
    )


def _create_show_payoff() -> pd.DataFrame:
    """複勝払い戻しのモックDataFrameを生成する."""
    data: dict[str, object] = {"レースID": "202506021211"}
    for i in range(1, 6):
        data[f"複勝払戻金_{i}"] = 150 * i if i <= 3 else None
        data[f"複勝馬番_{i}"] = i if i <= 3 else None
        data[f"複勝人気_{i}"] = i if i <= 3 else None
    return pd.DataFrame([data])


def _create_bracket_payoff() -> pd.DataFrame:
    """枠連払い戻しのモックDataFrameを生成する."""
    data: dict[str, object] = {"レースID": "202506021211"}
    for i in range(1, 4):
        data[f"枠連払戻金_{i}"] = 1200 if i == 1 else None
        data[f"枠連組番_{i}_1"] = 1 if i == 1 else None
        data[f"枠連組番_{i}_2"] = 2 if i == 1 else None
        data[f"枠連人気_{i}"] = 1 if i == 1 else None
    return pd.DataFrame([data])


def _create_quinella_payoff() -> pd.DataFrame:
    """馬連払い戻しのモックDataFrameを生成する."""
    data: dict[str, object] = {"レースID": "202506021211"}
    for i in range(1, 4):
        data[f"馬連払戻金_{i}"] = 2500 if i == 1 else None
        data[f"馬連組番_{i}_1"] = 1 if i == 1 else None
        data[f"馬連組番_{i}_2"] = 3 if i == 1 else None
        data[f"馬連人気_{i}"] = 2 if i == 1 else None
    return pd.DataFrame([data])


def _create_quinella_place_payoff() -> pd.DataFrame:
    """ワイド払い戻しのモックDataFrameを生成する."""
    data: dict[str, object] = {"レースID": "202506021211"}
    for i in range(1, 8):
        data[f"ワイド払戻金_{i}"] = 500 * i if i <= 3 else None
        data[f"ワイド組番_{i}_1"] = i if i <= 3 else None
        data[f"ワイド組番_{i}_2"] = i + 1 if i <= 3 else None
        data[f"ワイド人気_{i}"] = i if i <= 3 else None
    return pd.DataFrame([data])


def _create_exacta_payoff() -> pd.DataFrame:
    """馬単払い戻しのモックDataFrameを生成する."""
    data: dict[str, object] = {"レースID": "202506021211"}
    for i in range(1, 7):
        data[f"馬単払戻金_{i}"] = 5000 if i == 1 else None
        data[f"馬単組番_{i}_1"] = 3 if i == 1 else None
        data[f"馬単組番_{i}_2"] = 1 if i == 1 else None
        data[f"馬単人気_{i}"] = 3 if i == 1 else None
    return pd.DataFrame([data])


def _create_trio_payoff() -> pd.DataFrame:
    """3連複払い戻しのモックDataFrameを生成する."""
    data: dict[str, object] = {"レースID": "202506021211"}
    for i in range(1, 4):
        data[f"3連複払戻金_{i}"] = 8000 if i == 1 else None
        data[f"3連複組番_{i}_1"] = 1 if i == 1 else None
        data[f"3連複組番_{i}_2"] = 2 if i == 1 else None
        data[f"3連複組番_{i}_3"] = 3 if i == 1 else None
        data[f"3連複人気_{i}"] = 5 if i == 1 else None
    return pd.DataFrame([data])


def _create_trifecta_payoff() -> pd.DataFrame:
    """3連単払い戻しのモックDataFrameを生成する."""
    data: dict[str, object] = {"レースID": "202506021211"}
    for i in range(1, 7):
        data[f"3連単払戻金_{i}"] = 50000 if i == 1 else None
        data[f"3連単組番_{i}_1"] = 3 if i == 1 else None
        data[f"3連単組番_{i}_2"] = 1 if i == 1 else None
        data[f"3連単組番_{i}_3"] = 2 if i == 1 else None
        data[f"3連単人気_{i}"] = 10 if i == 1 else None
    return pd.DataFrame([data])


def _setup_all_payoff_mocks(mock_result_scraper: MagicMock) -> None:
    """全8券種の払い戻しモックをセットアップする."""
    mock_result_scraper.get_win_payoff.return_value = _create_win_payoff()
    mock_result_scraper.get_show_payoff.return_value = _create_show_payoff()
    mock_result_scraper.get_bracket_payoff.return_value = _create_bracket_payoff()
    mock_result_scraper.get_quinella_payoff.return_value = _create_quinella_payoff()
    mock_result_scraper.get_quinella_place_payoff.return_value = _create_quinella_place_payoff()
    mock_result_scraper.get_exacta_payoff.return_value = _create_exacta_payoff()
    mock_result_scraper.get_trio_payoff.return_value = _create_trio_payoff()
    mock_result_scraper.get_trifecta_payoff.return_value = _create_trifecta_payoff()


# 正常系
def test_output_columns_match_schema(
    provider_full: ScrapingProvider,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """出力DataFrameのカラム構成がPAYOFF_COLUMNSと一致する."""
    _setup_all_payoff_mocks(mock_result_scraper)

    result = provider_full.get_payoff(race_code)

    assert list(result.columns) == PAYOFF_COLUMNS


def test_output_is_single_row(
    provider_full: ScrapingProvider,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """出力DataFrameが1行である."""
    _setup_all_payoff_mocks(mock_result_scraper)

    result = provider_full.get_payoff(race_code)

    assert len(result) == 1


def test_win_payoff_values(
    provider_full: ScrapingProvider,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """単勝払い戻しのデータが正しく格納される."""
    _setup_all_payoff_mocks(mock_result_scraper)

    result = provider_full.get_payoff(race_code)

    row = result.iloc[0]
    assert row["単勝1馬番"] == 3
    assert row["単勝1払戻金"] == 350
    assert row["単勝1人気順"] == 1
    assert pd.isna(row["単勝2馬番"])


def test_show_payoff_values(
    provider_full: ScrapingProvider,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """複勝払い戻しのデータが正しく格納される."""
    _setup_all_payoff_mocks(mock_result_scraper)

    result = provider_full.get_payoff(race_code)

    row = result.iloc[0]
    assert row["複勝1馬番"] == 1
    assert row["複勝1払戻金"] == 150
    assert row["複勝2馬番"] == 2
    assert row["複勝3馬番"] == 3
    assert pd.isna(row["複勝4馬番"])


def test_combination_payoff_values(
    provider_full: ScrapingProvider,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """組み合わせ券種の払い戻しが正しく格納される."""
    _setup_all_payoff_mocks(mock_result_scraper)

    result = provider_full.get_payoff(race_code)

    row = result.iloc[0]
    # 枠連
    assert row["枠連1組番1"] == 1
    assert row["枠連1組番2"] == 2
    assert row["枠連1払戻金"] == 1200
    assert row["枠連1人気順"] == 1

    # 馬連
    assert row["馬連1組番1"] == 1
    assert row["馬連1組番2"] == 3
    assert row["馬連1払戻金"] == 2500

    # 3連複
    assert row["3連複1組番1"] == 1
    assert row["3連複1組番2"] == 2
    assert row["3連複1組番3"] == 3
    assert row["3連複1払戻金"] == 8000

    # 3連単
    assert row["3連単1組番1"] == 3
    assert row["3連単1組番2"] == 1
    assert row["3連単1組番3"] == 2
    assert row["3連単1払戻金"] == 50000


def test_doochaku_multiple_groups(
    provider_full: ScrapingProvider,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """同着時の複数組データが正しく格納される."""
    # 単勝が2組（同着）
    win_payoff = _create_win_payoff()
    win_payoff.loc[0, "単勝払戻金_2"] = 350
    win_payoff.loc[0, "単勝馬番_2"] = 5
    win_payoff.loc[0, "単勝人気_2"] = 1
    mock_result_scraper.get_win_payoff.return_value = win_payoff
    mock_result_scraper.get_show_payoff.return_value = _create_show_payoff()
    mock_result_scraper.get_bracket_payoff.return_value = _create_bracket_payoff()
    mock_result_scraper.get_quinella_payoff.return_value = _create_quinella_payoff()
    mock_result_scraper.get_quinella_place_payoff.return_value = _create_quinella_place_payoff()
    mock_result_scraper.get_exacta_payoff.return_value = _create_exacta_payoff()
    mock_result_scraper.get_trio_payoff.return_value = _create_trio_payoff()
    mock_result_scraper.get_trifecta_payoff.return_value = _create_trifecta_payoff()

    result = provider_full.get_payoff(race_code)

    row = result.iloc[0]
    assert row["単勝1馬番"] == 3
    assert row["単勝2馬番"] == 5
    assert row["単勝2払戻金"] == 350


def test_header_columns_from_race_code(
    provider_full: ScrapingProvider,
    mock_result_scraper: MagicMock,
    race_code: str,
) -> None:
    """ヘッダカラムがレースコードから正しく導出される."""
    _setup_all_payoff_mocks(mock_result_scraper)

    result = provider_full.get_payoff(race_code)

    row = result.iloc[0]
    assert row["レースコード"] == race_code
    assert row["開催年"] == "2025"
    assert row["開催月日"] == "0502"
    assert row["競馬場"] == "中山"
    assert row["開催回"] == 2
    assert row["開催日目"] == 12
    assert row["レース番号"] == 11
