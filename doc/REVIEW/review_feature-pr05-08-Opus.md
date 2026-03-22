# レビュー: feature/pr05-08

## 概要

- **対象**: `develop` → `feature/pr05-08`
- **レビュー日**: 2026-03-23
- **対応PR**: PLAN.md PR-05〜PR-08（ScrapingProvider 全メソッド実装）
- **レビュー対象ファイル数**: 9ファイル（変更4 + 新規5）

### 変更ファイル

| ファイル | 変更種別 |
|----------|----------|
| `keiba_data_interface/providers/scraping_provider.py` | 変更 |
| `keiba_data_interface/utils/race_code.py` | 変更 |
| `keiba_data_interface/utils/__init__.py` | 変更 |
| `test/unit/providers/scraping_provider/conftest.py` | 変更 |
| `test/unit/providers/scraping_provider/test_get_entry.py` | 新規 |
| `test/unit/providers/scraping_provider/test_get_result.py` | 新規 |
| `test/unit/providers/scraping_provider/test_get_race_result_info.py` | 新規 |
| `test/unit/providers/scraping_provider/test_get_win_show_odds.py` | 新規 |
| `test/unit/providers/scraping_provider/test_get_payoff.py` | 新規 |
| `test/unit/providers/scraping_provider/test_get_past_performances.py` | 新規 |
| `test/unit/providers/scraping_provider/test_get_schedule.py` | 新規 |
| `test/unit/utils/race_code/test_keibajo_code_to_name.py` | 新規 |

---

## 指摘事項

### 1. SPEC.md の異常区分マッピングと実装の不一致

| 項目 | 内容 |
|------|------|
| 重要度 | Warning |
| 場所 | `keiba_data_interface/providers/scraping_provider.py` L36〜41 |

**指摘内容**

[SPEC.md L263](../SPEC.md) では `get_entry` の異常区分変換を以下と定義している:

> "出走"→""、"取消"→"取消"、"除外"→"除外"

しかし実装では PLAN.md に従い以下のマッピングになっている:

```python
_IJO_KUBUN_MAP: dict[str, str] = {
    "出走": "",
    "取消": "出走取消",   # SPEC では "取消"
    "除外": "競走除外",   # SPEC では "除外"
    "中止": "競走中止",
    "失格": "失格",
}
```

実装自体は JRA-VAN 慣習に沿った正しい判断だが、SPEC.md が古いままになっているため、今後の開発者が混乱する可能性がある。

**修正案**

SPEC.md の変換表を実装に合わせて更新する。

```markdown
<!-- 修正前 -->
| 出走区分 | 異常区分 | "出走"→""、"取消"→"取消"、"除外"→"除外" |

<!-- 修正後 -->
| 出走区分 | 異常区分 | "出走"→""、"取消"→"出走取消"、"除外"→"競走除外"、"中止"→"競走中止"、"失格"→"失格" |
```

---

### 2. `get_schedule` の空ケースで `apply_types` が未呼出

| 項目 | 内容 |
|------|------|
| 重要度 | Warning |
| 場所 | `keiba_data_interface/providers/scraping_provider.py` L252〜253 |

**指摘内容**

`all_rows` が空の場合（開催なし）に返す空 DataFrame に `apply_types` が呼ばれていない。

```python
# 現在
if not all_rows:
    return ensure_columns(pd.DataFrame(), SCHEDULE_COLUMNS)
```

一方 `_convert_schedule` 内の空ケース（L840前後）では `apply_types` も呼んでいる:

```python
return apply_types(
    ensure_columns(pd.DataFrame(), SCHEDULE_COLUMNS),
    SCHEDULE_TYPES,
)
```

`_convert_past_performances` の空ケース処理も `apply_types` を呼んでおり、`get_schedule` だけが不統一。型が揃わずダウンストリームで型チェックが落ちる可能性がある。

**修正案**

```python
# 修正後
if not all_rows:
    return apply_types(ensure_columns(pd.DataFrame(), SCHEDULE_COLUMNS), SCHEDULE_TYPES)
```

---

### 3. `_convert_entry` / `_convert_result` / `_convert_past_performances` のコード重複

| 項目 | 内容 |
|------|------|
| 重要度 | Warning |
| 場所 | `keiba_data_interface/providers/scraping_provider.py` L335〜, L388〜, L679〜 |

**指摘内容**

3つの変換メソッドで以下のブロックがほぼ同一のまま繰り返されている:

- ヘッダカラムの設定（レースコード、開催年、開催月日、競馬場、開催回、開催日目、レース番号）
- 増減 → 増減符号 + 増減差 の分離ロジック
- 降着判定 + 異常区分の変換ロジック

DRY 原則に反しており、将来カラム名や変換ルールが変わった場合に 3 箇所を修正する必要がある。

**修正案**

共通部分をプライベートメソッドとして抽出する:

```python
def _set_header_columns(
    self, converted: dict[str, object], race_code: str, parts: dict[str, str]
) -> None:
    """レースコードからヘッダカラムを設定する."""
    converted["レースコード"] = race_code
    converted["開催年"] = parts["年"]
    converted["開催月日"] = parts["月日"]
    converted["競馬場"] = keibajo_code_to_name(parts["競馬場"])
    converted["開催回"] = int(parts["回"])
    converted["開催日目"] = int(parts["日目"])
    converted["レース番号"] = int(parts["R"])

@staticmethod
def _set_zogen(converted: dict[str, object], row: pd.Series) -> None:  # type: ignore[type-arg]
    """増減符号と増減差を設定する."""
    zogen = row.get("増減") if hasattr(row, "get") else row["増減"]
    if pd.notna(zogen):
        fugo, sa = split_zogen(int(zogen))
        converted["増減符号"] = fugo
        converted["増減差"] = sa

@staticmethod
def _set_ijo_kubun(
    converted: dict[str, object], row: pd.Series  # type: ignore[type-arg]
) -> bool:
    """異常区分を設定し、降着かどうかを返す."""
    ijo_kubun = row.get("異常区分", "")
    chakusa = row.get("着差", "")
    is_kokaku = (
        pd.notna(chakusa)
        and isinstance(chakusa, str)
        and re.search(r"\d+位降着", chakusa) is not None
    )
    if is_kokaku:
        converted["異常区分"] = "降着"
    elif pd.notna(ijo_kubun) and str(ijo_kubun) in _IJO_KUBUN_MAP:
        converted["異常区分"] = _IJO_KUBUN_MAP[str(ijo_kubun)]
    elif pd.notna(ijo_kubun) and str(ijo_kubun):
        converted["異常区分"] = str(ijo_kubun)
    else:
        converted["異常区分"] = ""
    return is_kokaku
```

---

### 4. `get_win_show_odds` 内のメソッドローカルインポートと `asyncio.run()` の問題

| 項目 | 内容 |
|------|------|
| 重要度 | Warning |
| 場所 | `keiba_data_interface/providers/scraping_provider.py` L157〜164 |

**指摘内容**

```python
import asyncio
import inspect

race_id = race_code_to_race_id(race_code)
result = self._odds_func(race_id)
if inspect.iscoroutine(result):
    raw: pd.DataFrame = asyncio.run(result)
else:
    raw = result
```

`asyncio.run()` は既存のイベントループ（Jupyter Notebook 等）が実行中の環境では `RuntimeError` になる。また `asyncio` と `inspect` のインポートをメソッド内に配置するのはコーディング規約上好ましくない（標準ライブラリはファイル先頭でインポートする）。

**修正案**

`scrape_odds_from_jra` が同期関数か非同期関数かを事前にインターフェースとして明確化する。非同期が前提なら初期化時に確認して対処方針を決める:

```python
# ファイル先頭に移動
import asyncio
import inspect

# コンストラクタ内でasync対応を確認しても良い
# あるいは scrape_odds_from_jra を同期ラッパーに変更することを検討する
```

---

### 5. `ensure_columns` の PerformanceWarning（494 件）

| 項目 | 内容 |
|------|------|
| 重要度 | Suggestion |
| 場所 | `keiba_data_interface/utils/dataframe.py` L26 |

**指摘内容**

テスト実行時に以下の警告が 494 件出ている:

```
PerformanceWarning: DataFrame is highly fragmented. This is usually the result of
calling `frame.insert` many times, which has poor performance. Consider joining
all columns at once using pd.concat(axis=1) instead.
```

PAYOFF テーブルは 222 カラムと非常に多く、1 カラムずつ `result[col] = pd.NA` で追加しているため断片化が起きている。

**修正案**

```python
def ensure_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    result = df.copy()
    missing = [col for col in columns if col not in result.columns]
    if missing:
        missing_df = pd.DataFrame(
            {col: pd.NA for col in missing}, index=result.index
        )
        result = pd.concat([result, missing_df], axis=1)
    return result[columns].copy()
```

---

### 6. インスタンス変数の型アノテーションが不統一

| 項目 | 内容 |
|------|------|
| 重要度 | Suggestion |
| 場所 | `keiba_data_interface/providers/scraping_provider.py` L92〜L113 |

**指摘内容**

`self._odds_func: Any` のみ型アノテーションが付いており、他の `self._scraper_class`、`self._result_scraper_class` 等には付いていない。一貫性のため全インスタンス変数に型アノテーションを付けるべき。

**修正案**

```python
self._scraper_class: type[Any] = scraper_class
self._result_scraper_class: type[Any] = result_scraper_class
self._odds_func: Any = odds_func
self._past_performances_scraper_class: type[Any] = past_performances_scraper_class
self._race_schedule_scraper_class: type[Any] = race_schedule_scraper_class
```

---

### 7. `test_kaisai_code_derived` のアサーションが弱い

| 項目 | 内容 |
|------|------|
| 重要度 | Suggestion |
| 場所 | `test/unit/providers/scraping_provider/test_get_schedule.py` L55〜57 |

**指摘内容**

```python
codes = set(result["開催コード"].tolist())
assert "20250105050101" in codes or any("0501" in c for c in codes)
```

`or any("0501" in c for c in codes)` の条件は常に True になりやすく、テストとしての検証力が非常に弱い。

**修正案**

期待値を具体的に指定する:

```python
codes = set(result["開催コード"].tolist())
# 中山: レースID=202505010101 → 開催コード=20250105050101
# 京都: レースID=202506020101 → 開催コード=20250105060201
assert codes == {"20250105050101", "20250105060201"}
```

---

### 8. `_parse_time_to_seconds` の不正入力テストが不足

| 項目 | 内容 |
|------|------|
| 重要度 | Suggestion |
| 場所 | `test/unit/providers/scraping_provider/` |

**指摘内容**

`_parse_time_to_seconds` はモジュールレベル関数として定義されており、不正なタイム文字列（例: `"abc"`, `""`, `"1:2"` など）を渡した場合に `ValueError` を発生させる。この関数はテストされていない。

また `get_result` で全馬競走中止など 1 着馬のタイムが存在しないケースにおける `first_time=None` のとき、`タイム差` が全行で NaN になることを確認するテストも存在しない。

**修正案**

```python
# test/unit/providers/scraping_provider/test_get_result.py に追加

def test_time_sa_when_no_winner(provider_full, mock_result_scraper, race_code):
    """1着タイムが存在しない場合、全行のタイム差がNaNになる."""
    raw = _create_scraping_result()
    raw.loc[0, "着順"] = "中止"
    raw.loc[0, "タイム"] = None
    raw.loc[0, "異常区分"] = "中止"
    raw.loc[1, "着順"] = "中止"
    raw.loc[1, "タイム"] = None
    raw.loc[1, "異常区分"] = "中止"
    mock_result_scraper.get_result.return_value = raw

    result = provider_full.get_result(race_code)

    assert pd.isna(result.iloc[0]["タイム差"])
    assert pd.isna(result.iloc[1]["タイム差"])
```

---

## テストカバレッジ評価

PLAN.md で要求されたテストケースの充足状況:

| PR | 要求テスト | 充足 |
|----|-----------|------|
| PR-05 get_entry | 異常区分全パターン、増減分離（+/-/0/前計不） | ✅ |
| PR-06 get_result | タイム差計算、降着検出、獲得本賞金導出 | ✅ |
| PR-06 get_race_result_info | ラップタイム格納、距離超過NaN、コーナー通過順 | ✅ |
| PR-07 get_win_show_odds | オッズリネーム、出走取消NaN、ヘッダカラム | ✅ |
| PR-07 get_payoff | 8券種結合、同着複数組 | ✅ |
| PR-08 get_past_performances | 新馬0行、賞金変換、日付分割 | ✅ |
| PR-08 get_schedule | 開催場集約、複数日、空スケジュール | ✅ |

---

## まとめ

| 重要度 | 件数 |
|--------|------|
| Critical | 0 |
| Warning | 4 |
| Suggestion | 4 |

全体として SPEC・PLAN に忠実な実装であり、設計上の大きな問題はない。
Warning の指摘のうち、**指摘2（空ケースの `apply_types` 抜け）** は動作に影響する可能性があるため優先して修正することを推奨する。
**指摘1（SPEC.md の記述更新）** はドキュメントの整合性維持のため、このブランチでまとめて対応するのが望ましい。

---

## 再レビュー（2026-03-23）

対象コミット: `4bab035..c58dd1d`（"GPTの指摘に対応"）

### 前回の指摘に対する修正状況

- [x] 指摘1: SPEC.md の異常区分マッピング → 実装に合わせて更新済み（`"出走取消"`, `"競走除外"` 等）
- [x] 指摘2: `get_schedule` の空ケースで `apply_types` 未呼出 → `apply_types` 追加済み
- [x] 指摘3: コード重複 → `_set_header_columns`, `_set_zogen`, `_set_ijo_kubun` ヘルパーメソッドを追加し、`_convert_entry` / `_convert_result` で使用。`_convert_past_performances` はレースコード構築ロジックが特殊なため `_set_header_columns` は未使用だが、`_set_zogen` と `_set_ijo_kubun` は共通化済み。設計として妥当
- [x] 指摘4: `asyncio`/`inspect` のメソッドローカルインポート → ファイル先頭に移動済み
- [x] 指摘5: `ensure_columns` の PerformanceWarning → `pd.concat(axis=1)` ベースに改修済み
- [x] 指摘6: インスタンス変数の型アノテーション不統一 → 全変数に `type[Any]` / `Any` を付与済み
- [x] 指摘7: `test_kaisai_code_derived` のアサーションが弱い → 具体的な期待値セットとの比較に変更済み
- [ ] 指摘8: `_parse_time_to_seconds` の不正入力テスト / 全馬中止テスト → 未追加。獲得本賞金関連テスト（`test_kakutoku_honshokin_derived` 等 3 件）は追加済み

### 追加指摘

なし。修正コミットで新たな問題は見つからなかった。

### 再レビューまとめ

| 状態 | 件数 |
|------|------|
| 修正済み | 7 |
| 未修正 | 1（Suggestion: テスト追加の一部） |
| 新規指摘 | 0 |

未修正の指摘8は Suggestion レベルであり、マージをブロックするものではない。
