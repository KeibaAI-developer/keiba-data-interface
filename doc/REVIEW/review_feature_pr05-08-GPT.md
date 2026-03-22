# レビュー: feature/pr05-08

## 概要

- **対象**: develop → feature/pr05-08
- **レビュー日**: 2026-03-22
- **レビュー対象ファイル数**: 9ファイル

## 指摘事項

### 1. `get_entry` / `get_result` / `get_win_show_odds` / `get_payoff` が統一スキーマの共通ヘッダ列を埋めていない

| 項目 | 内容 |
|------|------|
| 重要度 | Critical |
| 場所 | `keiba_data_interface/providers/scraping_provider.py` L329, L373, L509, L542 |

**指摘内容**

SCHEMA では馬毎レース情報・単複オッズ情報・払戻情報の `競馬場` / `開催回` / `開催日目` は scraping でも `○` です。ところが実装を見ると、

- `_convert_entry()` は `開催年` / `開催月日` / `レース番号` だけを入れており、`競馬場` / `開催回` / `開催日目` を一切設定していません
- `_convert_result()` も同様に `競馬場` / `開催回` / `開催日目` を設定していません
- `_convert_odds()` は `開催回` / `開催日目` までは入れていますが、`競馬場` は未設定です
- `_convert_payoff()` は `開催年` / `開催月日` / `レース番号` しか入れておらず、`競馬場` / `開催回` / `開催日目` が落ちています

このままだと `ensure_columns()` によってそれらの列は `NaN` になり、Provider 間で共通ヘッダを揃えるというインターフェース契約を満たしません。`PLAN.md` の PR-12 で予定している Provider 出力一致テストでも、このヘッダ欠落がそのまま不一致要因になります。

既存テストも `test_get_entry.py` と `test_get_payoff.py` では `開催年` / `開催月日` / `レース番号` までしか見ておらず、この欠落を検知できていません。

**修正案**

`race_code` から `開催回` / `開催日目` を導出し、`競馬場` は keiba-scraping 側の `race_id_to_race_info()` あるいは `ID_TO_KEIBAJO_DICT` 相当の変換を使って埋めてください。少なくとも `SCHEMA.md` で scraping `○` のヘッダ列は、全メソッドで同じ規則で埋まるように揃えるべきです。

### 2. `get_result` が `獲得本賞金` をまったく導出しておらず、PR-6 の主要要件を未実装のまま通している

| 項目 | 内容 |
|------|------|
| 重要度 | Critical |
| 場所 | `keiba_data_interface/providers/scraping_provider.py` L373 |

**指摘内容**

`PLAN.md` の PR-6 と `SPEC.md` 4.4 では、`get_result()` で「着順 + RaceInfo の 1〜5着賞金から `獲得本賞金` を導出する」ことが明記されています。しかし `_convert_result()` では `確定着順`・`走破タイム`・`タイム差` などは設定している一方、`獲得本賞金` を代入する処理が存在しません。

そのため、1着から5着までを含む通常レースでも `獲得本賞金` はすべて `NaN` になります。`SCHEMA.md` でも `獲得本賞金` は scraping `○` なので、これは単なる追加改善ではなく、統一スキーマの欠落です。

さらに、`test_get_result.py` は `確定着順` や `走破タイム` までは確認していますが、`獲得本賞金` の期待値を1件も検証していないため、この未実装がテストで完全に見逃されています。

**修正案**

`get_result()` の中で一度 `get_race_info()` 相当の賞金情報を取得し、`_convert_result()` に賞金マップを渡して 1〜5着の `獲得本賞金` を埋めてください。6着以下や異常区分該当馬は `NaN` のままで問題ありません。

### 3. `get_past_performances` が識別子を落としており、返却行を馬・レースに結び付けられない

| 項目 | 内容 |
|------|------|
| 重要度 | Warning |
| 場所 | `keiba_data_interface/providers/scraping_provider.py` L205, L216, L618 |

**指摘内容**

`get_past_performances()` は引数で `horse_id` を受け取っていますが、その値を `_convert_past_performances()` に渡していないため、変換後の DataFrame では `血統登録番号` が全行 `NaN` になります。また、fixture には `レースID` が含まれているのに、`レースコード` への変換も行っていません。

馬毎レース情報テーブルでは `レースコード` と `血統登録番号` はどちらも scraping `○` です。ここが落ちると、返却された過去成績を「どの馬の、どのレースの行か」で後段処理が参照できません。統一スキーマを返す API としては識別子欠落が痛いです。

`test_get_past_performances.py` も賞金変換や相手馬名しか見ておらず、識別子が埋まるかどうかを確認していません。

**修正案**

`_convert_past_performances()` に `horse_id` を渡して `血統登録番号` を全行に設定し、`レースID` と `日付` から 16桁の `レースコード` を構成して格納してください。これで馬毎レース情報テーブルとして最低限の join key が揃います。

## まとめ

| 重要度 | 件数 |
|--------|------|
| Critical | 2 |
| Warning | 1 |
| Suggestion | 0 |

---

## 再レビュー（2026-03-23）

前回の指摘に対する修正状況:

- [x] 指摘1: `get_entry` / `get_result` / `get_win_show_odds` / `get_payoff` で `競馬場` / `開催回` / `開催日目` を `race_code` から導出して設定するようになった
- [x] 指摘2: `get_result()` がレース情報から賞金マップを構築し、`獲得本賞金` を着順に応じて設定するようになった
- [x] 指摘3: `get_past_performances()` が `horse_id` を変換処理に渡し、`血統登録番号` と `レースコード` を格納するようになった

確認した主な反映箇所:

- `競馬場` / `開催回` / `開催日目` の設定: `scraping_provider.py` L349, L416, L571, L602
- `獲得本賞金` の導出: `scraping_provider.py` L181, L505
- `血統登録番号` / `レースコード` の設定: `scraping_provider.py` L674, L687, L697
- 対応テスト追加: `test_get_entry.py` L242, `test_get_result.py` L200, `test_get_win_show_odds.py` L58, `test_get_payoff.py` L260, `test_get_past_performances.py` L131, L146

### 追加指摘

追加の問題は見つかりませんでした。