"""Provider出力差異分析スクリプト.

extract_fixtures.pyで抽出したフィクスチャを使って
ScrapingProviderとMykeibaDBProviderの出力差異を分析し、
Markdownレポートを出力する。

column_definitions.pyのscraping○カラム定義と既知差異定義を使い、
- scraping○カラムのみを比較対象にする
- 既知差異(KNOWN_DIFF_*)は別セクションに分離する
- 未知の差異のみを「要対応」として報告する

使用方法:
    python test/integration/analyze_diff.py
"""

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402
from column_definitions import (  # noqa: E402
    ENTRY_ONLY_EXCLUDE,
    HORSE_MASTER_SCRAPING_COLUMNS,
    HORSE_RACE_INFO_SCRAPING_COLUMNS,
    KNOWN_DIFF_HORSE_MASTER,
    KNOWN_DIFF_HORSE_RACE,
    KNOWN_DIFF_ODDS,
    KNOWN_DIFF_PAYOFF,
    KNOWN_DIFF_RACE_INFO,
    KNOWN_DIFF_RACE_RESULT_INFO,
    KNOWN_DIFF_SCHEDULE,
    ODDS_SCRAPING_COLUMNS,
    PAST_PERF_ADDITIONAL_SCRAPING_COLUMNS,
    PAST_PERF_EXCLUDE,
    PAYOFF_SCRAPING_COLUMNS,
    RACE_INFO_SCRAPING_COLUMNS,
    RACE_RESULT_INFO_SCRAPING_COLUMNS,
    SCHEDULE_SCRAPING_COLUMNS,
)

from keiba_data_interface.providers.mykeibadb_provider import MykeibaDBProvider  # noqa: E402
from keiba_data_interface.providers.scraping_provider import ScrapingProvider  # noqa: E402

# メソッドごとのscraping○カラム
SCRAPING_COLUMNS_BY_METHOD: dict[str, list[str]] = {
    "get_race_info": RACE_INFO_SCRAPING_COLUMNS,
    "get_entry": [c for c in HORSE_RACE_INFO_SCRAPING_COLUMNS if c not in ENTRY_ONLY_EXCLUDE],
    "get_result": HORSE_RACE_INFO_SCRAPING_COLUMNS,
    "get_race_result_info": RACE_RESULT_INFO_SCRAPING_COLUMNS,
    "get_payoff": PAYOFF_SCRAPING_COLUMNS,
    "get_win_show_odds": ODDS_SCRAPING_COLUMNS,
    "get_past_performances": (
        [c for c in HORSE_RACE_INFO_SCRAPING_COLUMNS if c not in PAST_PERF_EXCLUDE]
        + PAST_PERF_ADDITIONAL_SCRAPING_COLUMNS
    ),
    "get_horse_master": HORSE_MASTER_SCRAPING_COLUMNS,
    "get_schedule": SCHEDULE_SCRAPING_COLUMNS,
}

# メソッドごとの既知差異カラム
KNOWN_DIFF_BY_METHOD: dict[str, set[str]] = {
    "get_race_info": KNOWN_DIFF_RACE_INFO,
    "get_entry": KNOWN_DIFF_HORSE_RACE,
    "get_result": KNOWN_DIFF_HORSE_RACE,
    "get_race_result_info": KNOWN_DIFF_RACE_RESULT_INFO,
    "get_payoff": KNOWN_DIFF_PAYOFF,
    "get_win_show_odds": KNOWN_DIFF_ODDS,
    "get_past_performances": KNOWN_DIFF_HORSE_RACE,
    "get_horse_master": KNOWN_DIFF_HORSE_MASTER,
    "get_schedule": KNOWN_DIFF_SCHEDULE,
}

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
REPORT_DIR = Path(__file__).resolve().parent / "report"
REPORT_PATH = REPORT_DIR / "provider_diff_report.md"

# 中央競馬の競馬場コード（レースコード[8:10]が該当する場合、中央レースと判定）
_JRA_KEIBAJO_CODES = {f"{i:02d}" for i in range(1, 11)}


def _load_pkl(path: Path) -> pd.DataFrame:
    return pd.read_pickle(path)


def _load_test_cases() -> dict[str, Any]:
    with open(FIXTURES_DIR / "test_cases.json") as f:
        return json.load(f)


# ============================================================================
# Provider生成（rawフィクスチャからモック経由でProvider出力を取得）
# ============================================================================


def _get_scraping_race_outputs(
    race_code: str,
    race_dir: Path,
) -> dict[str, pd.DataFrame | str]:
    """ScrapingProviderの各メソッド出力を取得する."""
    outputs: dict[str, pd.DataFrame | str] = {}

    raw_race_info = _load_pkl(race_dir / "scraping_race_info.pkl")
    has_entry_pkl = (race_dir / "scraping_entry.pkl").exists()

    mock_entry = MagicMock()
    mock_entry.get_race_info.return_value = raw_race_info
    if has_entry_pkl:
        mock_entry.get_entry.return_value = _load_pkl(race_dir / "scraping_entry.pkl")

    mock_result = MagicMock()
    if (race_dir / "scraping_result.pkl").exists():
        mock_result.get_result.return_value = _load_pkl(race_dir / "scraping_result.pkl")
        mock_result.get_lap_time.return_value = _load_pkl(race_dir / "scraping_lap_time.pkl")
        mock_result.get_corner.return_value = _load_pkl(race_dir / "scraping_corner.pkl")
        mock_result.get_win_payoff.return_value = _load_pkl(
            race_dir / "scraping_payoff_win.pkl",
        )
        mock_result.get_show_payoff.return_value = _load_pkl(
            race_dir / "scraping_payoff_show.pkl",
        )
        mock_result.get_bracket_payoff.return_value = _load_pkl(
            race_dir / "scraping_payoff_bracket.pkl",
        )
        mock_result.get_quinella_payoff.return_value = _load_pkl(
            race_dir / "scraping_payoff_quinella.pkl",
        )
        mock_result.get_quinella_place_payoff.return_value = _load_pkl(
            race_dir / "scraping_payoff_quinella_place.pkl",
        )
        mock_result.get_exacta_payoff.return_value = _load_pkl(
            race_dir / "scraping_payoff_exacta.pkl",
        )
        mock_result.get_trio_payoff.return_value = _load_pkl(
            race_dir / "scraping_payoff_trio.pkl",
        )
        mock_result.get_trifecta_payoff.return_value = _load_pkl(
            race_dir / "scraping_payoff_trifecta.pkl",
        )

    raw_odds = _load_pkl(race_dir / "scraping_odds.pkl")
    mock_scrape_odds = AsyncMock(return_value=raw_odds)

    with (
        patch(
            "keiba_data_interface.providers.scraping_provider.EntryPageScraper",
            return_value=mock_entry,
        ),
        patch(
            "keiba_data_interface.providers.scraping_provider.ResultPageScraper",
            return_value=mock_result,
        ),
        patch(
            "keiba_data_interface.providers.scraping_provider.scrape_odds_from_jra",
            mock_scrape_odds,
        ),
    ):
        provider = ScrapingProvider()
        try:
            outputs["get_race_info"] = provider.get_race_info(race_code)
        except Exception as e:
            outputs["get_race_info_error"] = str(e)

        if has_entry_pkl:
            try:
                outputs["get_entry"] = provider.get_entry(race_code)
            except Exception as e:
                outputs["get_entry_error"] = str(e)

        if (race_dir / "scraping_result.pkl").exists():
            try:
                outputs["get_result"] = provider.get_result(race_code)
            except Exception as e:
                outputs["get_result_error"] = str(e)
            try:
                outputs["get_race_result_info"] = provider.get_race_result_info(race_code)
            except Exception as e:
                outputs["get_race_result_info_error"] = str(e)
            try:
                outputs["get_payoff"] = provider.get_payoff(race_code)
            except Exception as e:
                outputs["get_payoff_error"] = str(e)

        try:
            outputs["get_win_show_odds"] = provider.get_win_show_odds(race_code)
        except Exception as e:
            outputs["get_win_show_odds_error"] = str(e)

    return outputs


def _get_mykeibadb_race_outputs(
    race_code: str,
    race_dir: Path,
) -> dict[str, pd.DataFrame | str]:
    """MykeibaDBProviderの各メソッド出力を取得する."""
    outputs: dict[str, pd.DataFrame | str] = {}

    mock_race_getter = MagicMock()
    mock_race_getter.get_race_shosai.return_value = _load_pkl(
        race_dir / "mykeibadb_race_shosai.pkl",
    )
    mock_race_getter.get_umagoto_race_joho.return_value = _load_pkl(
        race_dir / "mykeibadb_umagoto_race_joho.pkl",
    )
    mock_race_getter.get_haraimodoshi.return_value = _load_pkl(
        race_dir / "mykeibadb_haraimodoshi.pkl",
    )

    mock_odds_getter = MagicMock()
    mock_odds_getter.get_odds1_tansho.return_value = _load_pkl(
        race_dir / "mykeibadb_odds1_tansho.pkl",
    )
    mock_odds_getter.get_odds1_fukusho.return_value = _load_pkl(
        race_dir / "mykeibadb_odds1_fukusho.pkl",
    )

    with (
        patch(
            "keiba_data_interface.providers.mykeibadb_provider.RaceGetter",
            return_value=mock_race_getter,
        ),
        patch(
            "keiba_data_interface.providers.mykeibadb_provider.OddsGetter",
            return_value=mock_odds_getter,
        ),
    ):
        provider = MykeibaDBProvider()
        try:
            outputs["get_race_info"] = provider.get_race_info(race_code)
        except Exception as e:
            outputs["get_race_info_error"] = str(e)
        try:
            outputs["get_entry"] = provider.get_entry(race_code)
        except Exception as e:
            outputs["get_entry_error"] = str(e)
        try:
            outputs["get_result"] = provider.get_result(race_code)
        except Exception as e:
            outputs["get_result_error"] = str(e)
        try:
            outputs["get_race_result_info"] = provider.get_race_result_info(race_code)
        except Exception as e:
            outputs["get_race_result_info_error"] = str(e)
        try:
            outputs["get_payoff"] = provider.get_payoff(race_code)
        except Exception as e:
            outputs["get_payoff_error"] = str(e)
        try:
            outputs["get_win_show_odds"] = provider.get_win_show_odds(race_code)
        except Exception as e:
            outputs["get_win_show_odds_error"] = str(e)

    return outputs


def _get_scraping_horse_outputs(
    horse_id: str,
    horse_dir: Path,
) -> dict[str, pd.DataFrame | str]:
    """ScrapingProviderのhorse系メソッド出力を取得する."""
    outputs: dict[str, pd.DataFrame | str] = {}
    if not (horse_dir / "scraping_past_performances.pkl").exists():
        return outputs

    mock_pp_scraper = MagicMock()
    mock_pp_scraper.get_past_performances.return_value = _load_pkl(
        horse_dir / "scraping_past_performances.pkl",
    )
    mock_pp_scraper.get_horse_basic_info.return_value = _load_pkl(
        horse_dir / "scraping_horse_basic_info.pkl",
    )

    with patch(
        "keiba_data_interface.providers.scraping_provider.HorsePageScraper",
        return_value=mock_pp_scraper,
    ):
        provider = ScrapingProvider()
        try:
            outputs["get_past_performances"] = provider.get_past_performances(horse_id)
        except Exception as e:
            outputs["get_past_performances_error"] = str(e)
        try:
            outputs["get_horse_master"] = provider.get_horse_master(horse_id)
        except Exception as e:
            outputs["get_horse_master_error"] = str(e)

    return outputs


def _get_mykeibadb_horse_outputs(
    horse_id: str,
    horse_dir: Path,
) -> dict[str, pd.DataFrame | str]:
    """MykeibaDBProviderのhorse系メソッド出力を取得する."""
    outputs: dict[str, pd.DataFrame | str] = {}

    mock_race_getter = MagicMock()
    mock_race_getter.get_umagoto_race_joho.return_value = _load_pkl(
        horse_dir / "mykeibadb_umagoto_race_joho.pkl",
    )

    mock_master_getter = MagicMock()
    mock_master_getter.get_kyosoba_master2.return_value = _load_pkl(
        horse_dir / "mykeibadb_kyosoba_master2.pkl",
    )

    with (
        patch(
            "keiba_data_interface.providers.mykeibadb_provider.RaceGetter",
            return_value=mock_race_getter,
        ),
        patch(
            "keiba_data_interface.providers.mykeibadb_provider.OddsGetter",
            return_value=MagicMock(),
        ),
        patch(
            "keiba_data_interface.providers.mykeibadb_provider.MasterGetter",
            return_value=mock_master_getter,
        ),
    ):
        provider = MykeibaDBProvider()
        try:
            outputs["get_past_performances"] = provider.get_past_performances(horse_id)
        except Exception as e:
            outputs["get_past_performances_error"] = str(e)
        try:
            outputs["get_horse_master"] = provider.get_horse_master(horse_id)
        except Exception as e:
            outputs["get_horse_master_error"] = str(e)

    return outputs


def _get_scraping_schedule_outputs(
    target_date: str,
    sched_dir: Path,
) -> dict[str, pd.DataFrame | str]:
    """ScrapingProviderのget_schedule出力を取得する."""
    outputs: dict[str, pd.DataFrame | str] = {}

    mock_schedule_scraper = MagicMock()
    mock_schedule_scraper.get_race_schedule.return_value = _load_pkl(
        sched_dir / "scraping_schedule.pkl",
    )

    with patch(
        "keiba_data_interface.providers.scraping_provider.RaceScheduleScraper",
        return_value=mock_schedule_scraper,
    ):
        provider = ScrapingProvider()
        try:
            outputs["get_schedule"] = provider.get_schedule(target_date, target_date)
        except Exception as e:
            outputs["get_schedule_error"] = str(e)

    return outputs


def _get_mykeibadb_schedule_outputs(
    target_date: str,
    sched_dir: Path,
) -> dict[str, pd.DataFrame | str]:
    """MykeibaDBProviderのget_schedule出力を取得する."""
    outputs: dict[str, pd.DataFrame | str] = {}

    mock_race_getter = MagicMock()
    mock_race_getter.get_kaisai_schedule.return_value = _load_pkl(
        sched_dir / "mykeibadb_kaisai_schedule.pkl",
    )

    with (
        patch(
            "keiba_data_interface.providers.mykeibadb_provider.RaceGetter",
            return_value=mock_race_getter,
        ),
        patch(
            "keiba_data_interface.providers.mykeibadb_provider.OddsGetter",
            return_value=MagicMock(),
        ),
    ):
        provider = MykeibaDBProvider()
        try:
            outputs["get_schedule"] = provider.get_schedule(target_date, target_date)
        except Exception as e:
            outputs["get_schedule_error"] = str(e)

    return outputs


# ============================================================================
# 差異分析
# ============================================================================


class DiffRecord:
    """1つの差異を表すレコード."""

    def __init__(
        self,
        test_case: str,
        method: str,
        column: str,
        diff_type: str,
        scraping_value: str,
        mykeibadb_value: str,
        row_info: str = "",
    ) -> None:
        self.test_case = test_case
        self.method = method
        self.column = column
        self.diff_type = diff_type
        self.scraping_value = scraping_value
        self.mykeibadb_value = mykeibadb_value
        self.row_info = row_info


def _compare_dataframes(
    s_df: pd.DataFrame,
    m_df: pd.DataFrame,
    test_case: str,
    method: str,
    sort_by: str | None = None,
) -> list[DiffRecord]:
    """2つのDataFrameを比較して差異リストを返す.

    scraping○カラムのみを比較対象にする。
    """
    diffs: list[DiffRecord] = []

    # scraping○カラムでフィルタ
    target_cols = SCRAPING_COLUMNS_BY_METHOD.get(method)
    if target_cols is None:
        return diffs

    s_cols = set(s_df.columns)
    m_cols = set(m_df.columns)
    target_set = set(target_cols)

    # scraping○カラムのうち両方に存在するもの
    common_cols = sorted(target_set & s_cols & m_cols)

    # scraping○カラムなのに片方にないカラム
    for col in sorted(target_set - s_cols):
        if col in m_cols:
            diffs.append(
                DiffRecord(
                    test_case,
                    method,
                    col,
                    "カラム欠落(scraping側)",
                    "なし",
                    "存在",
                )
            )
    for col in sorted(target_set - m_cols):
        if col in s_cols:
            diffs.append(
                DiffRecord(
                    test_case,
                    method,
                    col,
                    "カラム欠落(mykeibadb側)",
                    "存在",
                    "なし",
                )
            )

    # ソート
    s = s_df.copy()
    m = m_df.copy()
    if sort_by and sort_by in s.columns and sort_by in m.columns:
        s = s.sort_values(sort_by).reset_index(drop=True)
        m = m.sort_values(sort_by).reset_index(drop=True)

    # 行数差異
    if len(s) != len(m):
        diffs.append(
            DiffRecord(
                test_case,
                method,
                "(行数)",
                "行数不一致",
                str(len(s)),
                str(len(m)),
            )
        )
        return diffs  # 行数が違う場合はカラム比較スキップ

    # 型差異
    for col in common_cols:
        s_dtype = str(s[col].dtype)
        m_dtype = str(m[col].dtype)
        if s_dtype != m_dtype:
            diffs.append(
                DiffRecord(
                    test_case,
                    method,
                    col,
                    "型不一致",
                    s_dtype,
                    m_dtype,
                )
            )

    # 値差異（行ごと）
    for col in common_cols:
        col_diffs: list[DiffRecord] = []
        for idx in range(len(s)):
            s_val: Any = s[col].iloc[idx]
            m_val: Any = m[col].iloc[idx]

            s_na = pd.isna(s_val)
            m_na = pd.isna(m_val)

            if s_na and m_na:
                continue

            # 行ラベルを決定
            if method == "get_past_performances" and "レースコード" in s.columns:
                row_label = f"レースコード={s['レースコード'].iloc[idx]}"
            elif method == "get_horse_master":
                # 1馬1行のためケース名で識別済み、行情報不要
                row_label = ""
            elif "馬番" in s.columns:
                row_label = f"馬番={s['馬番'].iloc[idx]}"
            elif "馬名" in s.columns:
                row_label = f"馬名={s['馬名'].iloc[idx]}"
            else:
                row_label = ""

            if s_na != m_na:
                col_diffs.append(
                    DiffRecord(
                        test_case,
                        method,
                        col,
                        "NaN不一致",
                        _fmt(s_val),
                        _fmt(m_val),
                        row_label,
                    )
                )
                continue

            if isinstance(s_val, float) and isinstance(m_val, float):
                if abs(s_val - m_val) >= 0.01:
                    col_diffs.append(
                        DiffRecord(
                            test_case,
                            method,
                            col,
                            "値不一致",
                            _fmt(s_val),
                            _fmt(m_val),
                            row_label,
                        )
                    )
            else:
                if s_val != m_val:
                    col_diffs.append(
                        DiffRecord(
                            test_case,
                            method,
                            col,
                            "値不一致",
                            _fmt(s_val),
                            _fmt(m_val),
                            row_label,
                        )
                    )

        # 同一カラムの差異が多すぎる場合は代表例のみ
        if len(col_diffs) > 5:
            kept = col_diffs[:3]
            kept.append(
                DiffRecord(
                    test_case,
                    method,
                    col,
                    f"他{len(col_diffs) - 3}件省略",
                    "...",
                    "...",
                )
            )
            diffs.extend(kept)
        else:
            diffs.extend(col_diffs)

    return diffs


def _fmt(val: Any) -> str:
    """値をレポート用文字列にフォーマットする."""
    if pd.isna(val):
        return "NaN"
    if isinstance(val, float):
        return f"{val:.4f}" if val != int(val) else str(int(val))
    return repr(val)


# ============================================================================
# メイン分析
# ============================================================================


def analyze_races(test_cases: dict[str, Any]) -> list[DiffRecord]:
    """全レースの差異を分析する."""
    all_diffs: list[DiffRecord] = []

    for race_info in test_cases["races"]:
        race_code = race_info["race_code"]
        race_name = race_info["name"]
        race_dir = FIXTURES_DIR / "races" / race_code
        label = f"{race_name}({race_code})"

        print(f"分析中: {label}")

        s_out = _get_scraping_race_outputs(race_code, race_dir)
        m_out = _get_mykeibadb_race_outputs(race_code, race_dir)

        # 各メソッドの比較
        methods_config = [
            ("get_race_info", None),
            ("get_entry", "馬番"),
            ("get_result", "馬番"),
            ("get_race_result_info", None),
            ("get_payoff", None),
            ("get_win_show_odds", "馬番"),
        ]
        for method, sort_by in methods_config:
            s_key = method
            m_key = method
            s_err = f"{method}_error"
            m_err = f"{method}_error"

            if s_err in s_out or m_err in m_out:
                all_diffs.append(
                    DiffRecord(
                        label,
                        method,
                        "(エラー)",
                        "変換エラー",
                        str(s_out.get(s_err, "OK")),
                        str(m_out.get(m_err, "OK")),
                    )
                )
                continue

            if s_key not in s_out or m_key not in m_out:
                continue

            s_df = s_out[s_key]
            m_df = m_out[m_key]
            if not isinstance(s_df, pd.DataFrame) or not isinstance(m_df, pd.DataFrame):
                continue

            diffs = _compare_dataframes(s_df, m_df, label, method, sort_by)
            all_diffs.extend(diffs)

    return all_diffs


def analyze_horses(test_cases: dict[str, Any]) -> list[DiffRecord]:
    """全馬の差異を分析する."""
    all_diffs: list[DiffRecord] = []

    for horse_info in test_cases["horses"]:
        horse_id = horse_info["horse_id"]
        horse_name = horse_info["name"]
        horse_dir = FIXTURES_DIR / "horses" / horse_id
        label = f"{horse_name}({horse_id})"

        print(f"分析中: {label}")

        s_out = _get_scraping_horse_outputs(horse_id, horse_dir)
        m_out = _get_mykeibadb_horse_outputs(horse_id, horse_dir)

        # get_horse_master の比較
        hi_method = "get_horse_master"
        hi_s_err = f"{hi_method}_error"
        hi_m_err = f"{hi_method}_error"

        if hi_s_err in s_out or hi_m_err in m_out:
            all_diffs.append(
                DiffRecord(
                    label,
                    hi_method,
                    "(エラー)",
                    "変換エラー",
                    str(s_out.get(hi_s_err, "OK")),
                    str(m_out.get(hi_m_err, "OK")),
                )
            )
        elif hi_method in s_out and hi_method in m_out:
            s_hi_df = s_out[hi_method]
            m_hi_df = m_out[hi_method]
            if isinstance(s_hi_df, pd.DataFrame) and isinstance(m_hi_df, pd.DataFrame):
                hi_diffs = _compare_dataframes(s_hi_df, m_hi_df, label, hi_method)
                all_diffs.extend(hi_diffs)

        method = "get_past_performances"
        s_err = f"{method}_error"
        m_err = f"{method}_error"

        if s_err in s_out or m_err in m_out:
            all_diffs.append(
                DiffRecord(
                    label,
                    method,
                    "(エラー)",
                    "変換エラー",
                    str(s_out.get(s_err, "OK")),
                    str(m_out.get(m_err, "OK")),
                )
            )
            continue

        if method in s_out and method in m_out:
            # 過去成績は行数が異なる場合がある（scrapingはHTML上の件数、mykeibadbは全件）
            s_df = s_out[method]
            m_df = m_out[method]
            if not isinstance(s_df, pd.DataFrame) or not isinstance(m_df, pd.DataFrame):
                continue

            if "レースコード" in s_df.columns and "レースコード" in m_df.columns:
                # 中央レース判定: 競馬場コードはレースコード(16桁)の9-10文字目(0-indexed: 8:10)。
                # NaN・空文字列・16桁未満の不正コード（海外レース等）はすべて「その他」に分類する。
                def _to_keibajo(series: pd.Series) -> pd.Series:
                    """レースコードから競馬場コード(2桁)を抽出する. 不正値はNaNとして返す."""
                    codes = series.where(series.notna(), other=pd.NA)
                    extracted = codes.astype(str).str[8:10]
                    # 16桁未満のレースコード(海外レース等)はstr[8:10]が2桁にならないのでNaN扱い
                    invalid_mask = series.isna() | (series.astype(str).str.len() < 16)
                    return extracted.where(~invalid_mask, other=pd.NA)

                s_keibajo = _to_keibajo(s_df["レースコード"])
                m_keibajo = _to_keibajo(m_df["レースコード"])
                # NaN は JRA コードに含まれないため自動的に「その他」に分類される
                s_jra_mask = s_keibajo.isin(_JRA_KEIBAJO_CODES)
                m_jra_mask = m_keibajo.isin(_JRA_KEIBAJO_CODES)

                # 中央/その他それぞれの行数差分を記録
                s_jra_count = int(s_jra_mask.sum())
                m_jra_count = int(m_jra_mask.sum())
                s_other_count = int((~s_jra_mask).sum())
                m_other_count = int((~m_jra_mask).sum())

                if s_jra_count != m_jra_count:
                    all_diffs.append(
                        DiffRecord(
                            label,
                            method,
                            "(行数)",
                            "行数不一致(中央)",
                            str(s_jra_count),
                            str(m_jra_count),
                        )
                    )
                if s_other_count != m_other_count:
                    all_diffs.append(
                        DiffRecord(
                            label,
                            method,
                            "(行数)",
                            "行数不一致(その他)",
                            str(s_other_count),
                            str(m_other_count),
                        )
                    )

                # 値/型比較: 両方に存在する中央レースコードのみを対象
                s_jra_codes = set(s_df.loc[s_jra_mask, "レースコード"].dropna().astype(str))
                m_jra_codes = set(m_df.loc[m_jra_mask, "レースコード"].dropna().astype(str))
                common_jra_codes = s_jra_codes & m_jra_codes
                s_df = s_df[s_df["レースコード"].astype(str).isin(common_jra_codes)].copy()
                m_df = m_df[m_df["レースコード"].astype(str).isin(common_jra_codes)].copy()

            diffs = _compare_dataframes(
                s_df,
                m_df,
                label,
                method,
                sort_by="レースコード",
            )
            all_diffs.extend(diffs)

    return all_diffs


def analyze_schedules(test_cases: dict[str, Any]) -> list[DiffRecord]:
    """全スケジュールの差異を分析する."""
    all_diffs: list[DiffRecord] = []

    for sched_info in test_cases.get("schedules", []):
        target_date = sched_info["date"]
        date_str = target_date.replace("-", "")
        sched_dir = FIXTURES_DIR / "schedules" / date_str
        label = f"スケジュール({target_date})"

        print(f"分析中: {label}")

        s_out = _get_scraping_schedule_outputs(target_date, sched_dir)
        m_out = _get_mykeibadb_schedule_outputs(target_date, sched_dir)

        method = "get_schedule"
        s_err = f"{method}_error"
        m_err = f"{method}_error"

        if s_err in s_out or m_err in m_out:
            all_diffs.append(
                DiffRecord(
                    label,
                    method,
                    "(エラー)",
                    "変換エラー",
                    str(s_out.get(s_err, "OK")),
                    str(m_out.get(m_err, "OK")),
                )
            )
            continue

        if method in s_out and method in m_out:
            s_df = s_out[method]
            m_df = m_out[method]
            if isinstance(s_df, pd.DataFrame) and isinstance(m_df, pd.DataFrame):
                diffs = _compare_dataframes(s_df, m_df, label, method, sort_by="開催コード")
                all_diffs.extend(diffs)

    return all_diffs


# ============================================================================
# レポート生成
# ============================================================================


def generate_report(
    race_diffs: list[DiffRecord],
    horse_diffs: list[DiffRecord],
    schedule_diffs: list[DiffRecord],
) -> str:
    """Markdownレポートを生成する.

    既知差異(KNOWN_DIFF_*)と未知差異を分離して報告する。
    """
    all_diffs = [d for d in race_diffs + horse_diffs + schedule_diffs if "省略" not in d.diff_type]

    # 既知差異 / 未知差異の振り分け
    known_diffs: list[DiffRecord] = []
    unknown_diffs: list[DiffRecord] = []
    for d in all_diffs:
        known_set = KNOWN_DIFF_BY_METHOD.get(d.method, set())
        if d.column in known_set:
            known_diffs.append(d)
        else:
            unknown_diffs.append(d)

    lines: list[str] = []
    lines.append("# Provider出力差異レポート\n")
    lines.append("scraping○カラムのみを比較対象とし、既知差異と未知差異を分離。\n")
    lines.append(
        f"テスト対象: レース{len(set(d.test_case for d in race_diffs))}件, "
        f"馬{len(set(d.test_case for d in horse_diffs))}件\n"
    )
    lines.append(f"検出差異総数: **{len(all_diffs)}件**\n")
    lines.append(f"- 未知差異（要対応）: **{len(unknown_diffs)}件**")
    lines.append(f"- 既知差異（KNOWN_DIFF_*で許容済み）: {len(known_diffs)}件\n")

    # ============================================================
    # 1. 未知差異（要対応）
    # ============================================================
    lines.append("---\n")
    lines.append("## 1. 未知差異（要対応）\n")
    lines.append(
        "統合テストで検証すべき差異。KNOWN_DIFF_*に追加するか、converter修正が必要。\n",
    )

    if not unknown_diffs:
        lines.append("**未知差異なし** - 全差異が既知差異として登録済み。\n")
    else:
        # カテゴリ別に分類
        unk_value = [d for d in unknown_diffs if d.diff_type == "値不一致"]
        unk_nan = [d for d in unknown_diffs if d.diff_type == "NaN不一致"]
        unk_row_central = [d for d in unknown_diffs if d.diff_type == "行数不一致(中央)"]
        unk_row_other = [d for d in unknown_diffs if d.diff_type == "行数不一致(その他)"]
        unk_row_plain = [d for d in unknown_diffs if d.diff_type == "行数不一致"]
        unk_error = [d for d in unknown_diffs if d.diff_type == "変換エラー"]
        unk_other = [
            d
            for d in unknown_diffs
            if d.diff_type
            not in {
                "値不一致",
                "NaN不一致",
                "行数不一致",
                "行数不一致(中央)",
                "行数不一致(その他)",
                "変換エラー",
            }
        ]

        lines.append(f"- 値不一致: {len(unk_value)}件")
        lines.append(f"- NaN不一致: {len(unk_nan)}件")
        lines.append(f"- 行数不一致(中央): {len(unk_row_central)}件")
        lines.append(f"- 行数不一致(その他): {len(unk_row_other)}件")
        if unk_row_plain:
            lines.append(f"- 行数不一致: {len(unk_row_plain)}件")
        lines.append(f"- 変換エラー: {len(unk_error)}件")
        if unk_other:
            lines.append(f"- その他: {len(unk_other)}件")
        lines.append("")

        # 値不一致
        if unk_value:
            lines.append("### 1a. 値不一致\n")
            lines.append(_build_value_diff_table(unk_value))
            lines.append("")

        # NaN不一致
        if unk_nan:
            lines.append("### 1b. NaN不一致\n")
            scraping_nan = [d for d in unk_nan if d.scraping_value == "NaN"]
            mykeibadb_nan = [d for d in unk_nan if d.mykeibadb_value == "NaN"]
            if scraping_nan:
                lines.append(f"#### scraping=NaN, mykeibadb=値 ({len(scraping_nan)}件)\n")
                lines.append(_build_nan_table(scraping_nan, "mykeibadb"))
                lines.append("")
            if mykeibadb_nan:
                lines.append(f"#### scraping=値, mykeibadb=NaN ({len(mykeibadb_nan)}件)\n")
                lines.append(_build_nan_table(mykeibadb_nan, "scraping"))
                lines.append("")

        # 行数不一致
        all_row_diffs = unk_row_central + unk_row_other + unk_row_plain
        if all_row_diffs:
            lines.append("### 1c. 行数不一致\n")
            lines.append("| テストケース | メソッド | 種別 | scraping行数 | mykeibadb行数 |")
            lines.append("|-------------|----------|------|-------------|---------------|")
            for d in all_row_diffs:
                kind = d.diff_type.replace("行数不一致", "").strip("()") or "全体"
                lines.append(
                    f"| {d.test_case[:40]} | {d.method} | {kind} "
                    f"| {d.scraping_value} | {d.mykeibadb_value} |",
                )
            lines.append("")

        # 変換エラー
        if unk_error:
            lines.append("### 1d. 変換エラー\n")
            lines.append("| テストケース | メソッド | scraping | mykeibadb |")
            lines.append("|-------------|----------|----------|-----------|")
            for d in unk_error:
                lines.append(
                    f"| {d.test_case[:40]} | {d.method} "
                    f"| {d.scraping_value[:50]} | {d.mykeibadb_value[:50]} |",
                )
            lines.append("")

    # ============================================================
    # 2. 既知差異サマリー
    # ============================================================
    lines.append("---\n")
    lines.append("## 2. 既知差異サマリー（KNOWN_DIFF_*で許容済み）\n")
    lines.append("これらはデータソースの仕様差異であり、テストでは許容される。\n")

    if not known_diffs:
        lines.append("既知差異なし。\n")
    else:
        lines.append(_build_known_diff_summary(known_diffs))

    return "\n".join(lines)


def _build_value_diff_table(diffs: list[DiffRecord]) -> str:
    """値不一致テーブルを構築する."""
    patterns: dict[tuple[str, str], dict[str, Any]] = {}
    for d in diffs:
        key = (d.column, d.method)
        if key not in patterns:
            patterns[key] = {"count": 0, "test_cases": set(), "examples": []}
        patterns[key]["count"] += 1
        patterns[key]["test_cases"].add(d.test_case)
        if len(patterns[key]["examples"]) < 2:
            patterns[key]["examples"].append(d)

    lines = [
        "| カラム | メソッド | 影響ケース数 | 発生行数 " "| scraping例 | mykeibadb例 |",
        "|--------|----------|-------------|----------" "|------------|-------------|",
    ]
    for (col, method), info in sorted(patterns.items()):
        tc = len(info["test_cases"])
        cnt = info["count"]
        ex = info["examples"][0]
        s = ex.scraping_value[:30]
        m = ex.mykeibadb_value[:30]
        lines.append(f"| {col} | {method} | {tc} | {cnt} | {s} | {m} |")
    return "\n".join(lines)


def _build_nan_table(diffs: list[DiffRecord], has_value_side: str) -> str:
    """NaN不一致テーブルを構築する."""
    patterns: dict[tuple[str, str], dict[str, Any]] = {}
    for d in diffs:
        key = (d.column, d.method)
        if key not in patterns:
            patterns[key] = {"count": 0, "test_cases": set(), "example": ""}
        patterns[key]["count"] += 1
        patterns[key]["test_cases"].add(d.test_case)
        if not patterns[key]["example"]:
            patterns[key]["example"] = (
                d.mykeibadb_value if has_value_side == "mykeibadb" else d.scraping_value
            )

    val_label = f"{has_value_side}例"
    lines = [
        f"| カラム | メソッド | 影響ケース数 | 発生行数 | {val_label} |",
        "|--------|----------|-------------|----------|-------------|",
    ]
    for (col, method), info in sorted(patterns.items()):
        tc = len(info["test_cases"])
        cnt = info["count"]
        val = str(info["example"])[:35]
        lines.append(f"| {col} | {method} | {tc} | {cnt} | {val} |")
    return "\n".join(lines)


def _build_known_diff_summary(diffs: list[DiffRecord]) -> str:
    """既知差異のサマリーテーブルを構築する."""
    patterns: dict[tuple[str, str, str], dict[str, Any]] = {}
    for d in diffs:
        key = (d.column, d.method, d.diff_type)
        if key not in patterns:
            patterns[key] = {
                "count": 0,
                "test_cases": set(),
                "example_s": d.scraping_value,
                "example_m": d.mykeibadb_value,
            }
        patterns[key]["count"] += 1
        patterns[key]["test_cases"].add(d.test_case)

    lines = [
        "| カラム | メソッド | 差異種別 | 影響ケース数 | 発生行数 " "| scraping例 | mykeibadb例 |",
        "|--------|----------|----------|-------------|----------" "|------------|-------------|",
    ]
    for (col, method, dtype), info in sorted(patterns.items()):
        tc = len(info["test_cases"])
        cnt = info["count"]
        s = str(info["example_s"])[:25]
        m = str(info["example_m"])[:25]
        lines.append(f"| {col} | {method} | {dtype} | {tc} | {cnt} | {s} | {m} |")
    return "\n".join(lines)


def main() -> None:
    """差異分析を実行しレポートを出力する."""
    test_cases = _load_test_cases()
    print(
        f"レース: {len(test_cases['races'])}件, "
        f"馬: {len(test_cases['horses'])}件, "
        f"スケジュール: {len(test_cases.get('schedules', []))}件"
    )

    print("\n=== レース分析 ===")
    race_diffs = analyze_races(test_cases)

    print("\n=== 馬分析 ===")
    horse_diffs = analyze_horses(test_cases)

    print("\n=== スケジュール分析 ===")
    schedule_diffs = analyze_schedules(test_cases)

    # サマリーレポート
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = generate_report(race_diffs, horse_diffs, schedule_diffs)
    with open(REPORT_PATH, "w") as f:
        f.write(report)
    print(f"\nサマリーレポート出力: {REPORT_PATH}")

    # メソッド別詳細レポート
    all_diffs = race_diffs + horse_diffs + schedule_diffs
    generate_method_detail_reports(all_diffs)

    print(f"差異総数: {len(all_diffs)}件")


def generate_method_detail_reports(all_diffs: list[DiffRecord]) -> None:
    """メソッドごとの詳細差異レポートを生成する."""
    report_dir = REPORT_DIR

    # メソッドごとにグループ化
    method_diffs: dict[str, list[DiffRecord]] = {}
    for d in all_diffs:
        if "省略" in d.diff_type:
            continue
        if d.method not in method_diffs:
            method_diffs[d.method] = []
        method_diffs[d.method].append(d)

    for method, diffs in sorted(method_diffs.items()):
        report_path = report_dir / f"provider_diff_{method}_report.md"
        content = _build_method_detail_report(method, diffs)
        with open(report_path, "w") as f:
            f.write(content)
        print(f"詳細レポート出力: {report_path} ({len(diffs)}件)")


def _build_method_detail_report(method: str, diffs: list[DiffRecord]) -> str:
    """1メソッド分の詳細差異レポートを構築する."""
    known_set = KNOWN_DIFF_BY_METHOD.get(method, set())

    lines: list[str] = []
    lines.append(f"# {method} 差異詳細レポート\n")

    known_count = sum(1 for d in diffs if d.column in known_set)
    unknown_count = len(diffs) - known_count
    lines.append(f"差異総数: {len(diffs)}件（既知: {known_count}件, 未知: {unknown_count}件）\n")

    # カラムごとにグループ化
    col_diffs: dict[str, list[DiffRecord]] = {}
    for d in diffs:
        if d.column not in col_diffs:
            col_diffs[d.column] = []
        col_diffs[d.column].append(d)

    for col in sorted(col_diffs.keys()):
        records = col_diffs[col]
        is_known = col in known_set
        known_label = "（既知差異）" if is_known else ""

        lines.append(f"## {col}{known_label}\n")

        # 差異種別ごとにグループ化
        type_diffs: dict[str, list[DiffRecord]] = {}
        for d in records:
            if d.diff_type not in type_diffs:
                type_diffs[d.diff_type] = []
            type_diffs[d.diff_type].append(d)

        for diff_type in [
            "値不一致",
            "NaN不一致",
            "型不一致",
            "行数不一致",
            "行数不一致(中央)",
            "行数不一致(その他)",
            "変換エラー",
            "カラム欠落(scraping側)",
            "カラム欠落(mykeibadb側)",
        ]:
            if diff_type not in type_diffs:
                continue
            type_records = type_diffs[diff_type]

            lines.append(f"### {diff_type}（{len(type_records)}件）\n")

            # テーブルヘッダ
            id_label = _get_id_label(method)
            show_row_info = method != "get_horse_master"
            if show_row_info:
                lines.append(f"| {id_label} | scraping値 | mykeibadb値 | 行情報 |")
                lines.append("|------|------------|-------------|--------|")
            else:
                lines.append(f"| {id_label} | scraping値 | mykeibadb値 |")
                lines.append("|------|------------|-------------|")

            for d in type_records:
                case_id = _extract_case_id(d.test_case)
                s_val = d.scraping_value[:50]
                m_val = d.mykeibadb_value[:50]
                if show_row_info:
                    lines.append(f"| {case_id} | {s_val} | {m_val} | {d.row_info} |")
                else:
                    lines.append(f"| {case_id} | {s_val} | {m_val} |")

            lines.append("")

    return "\n".join(lines)


def _get_id_label(method: str) -> str:
    """メソッドに応じたID列ラベルを返す."""
    if method in ("get_past_performances", "get_horse_master"):
        return "馬ID"
    if method == "get_schedule":
        return "日付"
    return "レースコード"


def _extract_case_id(test_case: str) -> str:
    """テストケースラベルからIDを抽出する.

    例: "有馬記念2023(2023122406050811)" → "2023122406050811"
         "ミュージアムマイル(2022105081)" → "2022105081"
    """
    start = test_case.rfind("(")
    end = test_case.rfind(")")
    if start != -1 and end != -1:
        return test_case[start + 1 : end]
    return test_case


if __name__ == "__main__":
    main()
