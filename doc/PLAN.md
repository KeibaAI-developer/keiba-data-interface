# keiba-data-interface 実装計画

本ドキュメントは、SPEC.md と SCHEMA.md に基づいた keiba-data-interface ライブラリの実装計画である。
レビュー可能な単位で PR を分割し、各 PR に単体テストの実装を含める。

---

## 前提

- keiba-scraping および mykeibadb-python は既に実装済み
- keiba-data-interface は新規ライブラリとして作成する
- テストフレームワークは pytest を使用する
- Provider の外部依存（scraping/mykeibadb）はモック化して単体テストを行う

---

## PR-1: プロジェクト初期構成 + スキーマ定義

**目的**: パッケージの土台とスキーマ定義を整備する

**実装内容**

- `pyproject.toml` の作成（パッケージ名、依存関係、ビルド設定）
- パッケージディレクトリ構成の作成
  ```
  keiba_data_interface/
      __init__.py
      schema/
          __init__.py
          columns.py        # 各テーブルのカラム名定数リスト
          types.py           # 各テーブルの型定義辞書
      providers/
          __init__.py
      utils/
          __init__.py
  test/
      __init__.py
      unit/
          __init__.py
          schema/
              __init__.py
  ```
- `schema/columns.py`: SCHEMA.md に基づく 6 テーブル分のカラム名リスト定数を定義
  - `RACE_INFO_COLUMNS`: レース基本情報（65 カラム）
  - `RACE_RESULT_INFO_COLUMNS`: レース結果情報（69 カラム）
  - `HORSE_RACE_INFO_COLUMNS`: 馬毎レース情報（67 カラム）
  - `PAYOFF_COLUMNS`: 払戻情報（222 カラム）
  - `ODDS_COLUMNS`: 単複オッズ情報（13 カラム）
  - `SCHEDULE_COLUMNS`: 開催スケジュール情報（43 カラム）
- `schema/types.py`: 各カラムの型定義辞書（DataFrame 生成時に使用）

**テスト**

- 各テーブルのカラム数が SCHEMA.md と一致すること
- カラム名に重複がないこと
- 型定義辞書のキーがカラム名リストと一致すること

---

## PR-2: ユーティリティ実装

**目的**: レースコード変換・DataFrame 整形・データ変換の各ユーティリティを実装する

**実装内容**

- `utils/race_code.py`: レースコード変換関数
  - `race_code_to_race_id(race_code: str) -> str`: 16 桁 → 12 桁変換（月日部分を除去）
  - `race_code_to_kaisai_code(race_code: str) -> str`: 16 桁レースコード → 開催コード導出
  - `extract_race_code_parts(race_code: str) -> dict`: レースコードから年・月日・競馬場・回・日目・R を抽出
- バリデーション: 桁数チェック、数値チェック
- `utils/dataframe.py`: DataFrame 整形用ユーティリティ
  - `ensure_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame`: 指定カラムリストに合わせて過不足を調整（不足カラムは NaN 埋め、余分なカラムは削除、順序を統一）
  - `apply_types(df: pd.DataFrame, type_dict: dict) -> pd.DataFrame`: 型定義辞書に基づいて型変換
- `utils/converters.py`: データ変換関数
  - `convert_time_msss_to_display(value: str) -> str`: 走破タイム "MSSS" → "M:SS.S" 変換
  - `convert_hhmm_to_display(value: str) -> str`: 発走時刻 "HHMM" → "HH:MM" 変換
  - `convert_tenth_to_unit(value: int, unit: float) -> float`: 0.1 単位 → 実単位変換（負担重量、オッズ、ハロンタイム等）
  - `convert_manyen_to_hyakuyen(value: int) -> int`: 万円 → 百円単位変換（賞金）
  - `split_zogen(value: int) -> tuple[str, int]`: 増減（符号付き整数）→ 増減符号 + 増減差に分離

**テスト**

- 正常ケース: 16 桁 → 12 桁変換の入出力検証
- 正常ケース: レースコードからの各要素抽出
- 異常ケース: 不正な桁数、非数値文字列でのエラー
- `ensure_columns`: 不足カラムの NaN 埋め、余分カラムの除去、カラム順序の統一
- `apply_types`: 型変換の正確性
- 各変換関数: 正常ケース・境界値（0, 負値）・NaN/空文字の扱い

---

## PR-3: DataProvider Protocol + DataInterface クラス

**目的**: Provider の抽象インターフェースと、利用者向け API のファサードクラスを実装する

**実装内容**

- `protocols.py`: `DataProvider` Protocol の定義（SPEC.md 3.1 に準拠）
  - `get_race_info(race_code: str) -> pd.DataFrame`
  - `get_entry(race_code: str) -> pd.DataFrame`
  - `get_win_show_odds(race_code: str) -> pd.DataFrame`
  - `get_result(race_code: str) -> pd.DataFrame`
  - `get_race_result_info(race_code: str) -> pd.DataFrame`
  - `get_payoff(race_code: str) -> pd.DataFrame`
  - `get_past_performances(horse_id: str) -> pd.DataFrame`
  - `get_schedule(start_date: str, end_date: str) -> pd.DataFrame`
- `interface.py`: `DataInterface` クラスの実装
  - コンストラクタで provider 名（`'scraping'` or `'mykeibadb'`）を受け取り、対応する Provider を生成
  - 各メソッドは Provider に委譲するだけ
- `__init__.py` の公開 API 設定（`DataInterface`, `DataProvider` のエクスポート）

**テスト**

- Protocol を満たすモック Provider を作成し、DataInterface 経由での呼び出しが正しく委譲されること
- 不正な provider 名を渡した場合のエラーハンドリング

---

## PR-4: ScrapingProvider — get_race_info

**目的**: ScrapingProvider の `get_race_info` を実装する（最初の Provider メソッド）

**実装内容**

- `providers/scraping_provider.py`: ScrapingProvider クラスの骨組み + `get_race_info` の実装
  - 16 桁レースコード → 12 桁変換して `EntryPageScraper` に渡す
  - scraping 出力 → 統一スキーマへの変換（SPEC.md 4.1 の変換表に準拠）
    - 日付 → 開催年 + 開催月日 分割
    - 芝ダ + 左右 → トラック結合
    - コース + 内外 → コース区分結合
    - 賞金: 万円 → 百円単位変換
    - 馬場 → 芝馬場状態 / ダート馬場状態の振り分け
  - `ensure_columns` で不足カラムを NaN 埋め

**テスト**

- EntryPageScraper をモック化し、scraping 出力の典型データから統一スキーマへの変換を検証
- 芝レース / ダートレースで馬場状態カラムの振り分けが正しいこと
- 賞金の単位変換が正しいこと
- 出力 DataFrame のカラム構成が SCHEMA.md テーブル 1 と一致すること

---

## PR-5: ScrapingProvider — get_entry

**目的**: ScrapingProvider の `get_entry`（出馬表取得）を実装する

**実装内容**

- `providers/scraping_provider.py` に `get_entry` を追加
  - `EntryPageScraper.get_entry()` で取得
  - カラム名マッピング（馬 ID → 血統登録番号、斤量 → 負担重量、騎手 ID → 騎手コード 等）
  - 増減（符号付き整数）→ 増減符号 + 増減差 分離
  - 出走区分 → 異常区分 変換（"出走" → ""、"取消" → "出走取消"、"除外" → "競走除外"）

**テスト**

- scraping 出力の典型データから変換結果を検証
- 増減分離のパターン検証（プラス、マイナス、ゼロ、前計不）
- 異常区分変換の全パターン検証
- 出力 DataFrame のカラム構成が SCHEMA.md テーブル 3 と一致すること

---

## PR-6: ScrapingProvider — get_result + get_race_result_info

**目的**: ScrapingProvider のレース結果系メソッドを実装する

**実装内容**

- `providers/scraping_provider.py` に `get_result` を追加
  - `ResultPageScraper.get_result()` で取得
  - `get_entry` と共通のカラムマッピングに加え、結果固有カラムの変換
    - タイム差の算出（1 着タイムとの差）
    - 獲得本賞金の導出（着順 + RaceInfo 賞金から）
    - 異常区分の変換（降着の検出を含む）
- `providers/scraping_provider.py` に `get_race_result_info` を追加
  - `ResultPageScraper.get_lap_time()` + `get_corner()` で取得
  - ラップタイムの 100m 刻みカラムへの格納
  - 前 3 ハロン / 後 3 ハロンのラップタイムからの算出

**テスト**

- タイム差計算の検証（通常ケース、競走中止馬の除外）
- 獲得本賞金の導出検証（1 着〜5 着、6 着以下）
- 降着を含む異常区分の変換検証
- ラップタイム格納の検証（200m 割り切れるレース / 割り切れないレース）
- コーナー通過順文字列のフォーマット検証
- 出力 DataFrame のカラム構成がそれぞれ SCHEMA.md テーブル 2・3 に一致すること

---

## PR-7: ScrapingProvider — get_win_show_odds + get_payoff

**目的**: ScrapingProvider のオッズ・払戻系メソッドを実装する

**実装内容**

- `providers/scraping_provider.py` に `get_win_show_odds` を追加
  - `scrape_odds_from_jra()` で取得
  - 複勝最小/最大オッズ → 複勝最低/最高オッズのリネーム
  - レースコードからヘッダカラム（開催年等）を導出
- `providers/scraping_provider.py` に `get_payoff` を追加
  - `ResultPageScraper` の各券種 `get_*_payoff()` で取得
  - 8 券種の払戻データを 1 行の DataFrame に結合
  - 統一スキーマへのカラム名変換

**テスト**

- オッズ: レースコードからのヘッダカラム導出が正しいこと
- オッズ: 出走取消馬のオッズが NaN であること
- 払戻: 8 券種の結合が正しく 1 行になること
- 払戻: 同着時の複数組データが正しく格納されること
- 出力 DataFrame のカラム構成がそれぞれ SCHEMA.md テーブル 4・5 に一致すること

---

## PR-8: ScrapingProvider — get_past_performances + get_schedule

**目的**: ScrapingProvider の残りのメソッドを実装し、Provider を完成させる

**実装内容**

- `providers/scraping_provider.py` に `get_past_performances` を追加
  - `PastPerformancesScraper.get_past_performances()` で取得
  - `get_result` と類似の変換に加え、過去成績固有カラムの変換
    - 日付 → 開催年 + 開催月日 分割
    - 賞金: 万円 → 百円単位変換
    - 相手 1 馬名の格納
- `providers/scraping_provider.py` に `get_schedule` を追加
  - `RaceScheduleScraper.get_race_schedule()` で取得
  - レース単位 → 開催場単位への集約
  - レース ID → 開催コード導出

**テスト**

- 過去成績: 新馬（0 行）の場合の挙動
- 過去成績: 賞金の単位変換、日付分割の検証
- 過去成績: 出力 DataFrame のカラム構成が SCHEMA.md テーブル 3 に一致すること
- スケジュール: レース単位から開催場単位への集約が正しいこと
- スケジュール: 複数日の日付範囲での動作検証
- スケジュール: 出力 DataFrame のカラム構成が SCHEMA.md テーブル 6 に一致すること

---

## PR-9: MykeibaDBProvider — get_race_info + get_entry

**目的**: MykeibaDBProvider の基本的なレース情報・出馬表取得を実装する

**実装内容**

- `providers/mykeibadb_provider.py`: MykeibaDBProvider クラスの骨組み + `get_race_info` + `get_entry` の実装
  - `get_race_info`: `RaceGetter.get_race_shosai()` から取得、統一スキーマに変換
    - 発走時刻 "1540" → "15:40" 変換
    - コード変換済みカラムのリネーム
  - `get_entry`: `RaceGetter.get_umagoto_race_joho()` から取得、統一スキーマに変換
    - 負担重量 0.1kg → kg 変換
    - コード変換済みカラムのリネーム

**テスト**

- RaceGetter をモック化し、mykeibadb 出力の典型データから統一スキーマへの変換を検証
- 発走時刻変換の検証
- 負担重量変換の検証
- 出力 DataFrame のカラム構成がそれぞれ SCHEMA.md テーブル 1・3 に一致すること

---

## PR-10: MykeibaDBProvider — get_result + get_race_result_info

**目的**: MykeibaDBProvider のレース結果系メソッドを実装する

**実装内容**

- `providers/mykeibadb_provider.py` に `get_result` を追加
  - `RaceGetter.get_umagoto_race_joho()` から取得（DATA_KUBUN で結果データを選択）
  - `get_entry` と共通の変換に加え、結果カラムの追加変換
    - 走破タイム "MSSS" → "M:SS.S" 変換
    - 後 3F/後 4F の 0.1 秒 → 秒変換
    - 単勝オッズの 0.1 倍 → 倍変換
- `providers/mykeibadb_provider.py` に `get_race_result_info` を追加
  - `RaceGetter.get_race_shosai()` から取得（LAP_TIME1〜RECORD_KOSHIN_KUBUN 範囲）
  - ラップタイムの 200m 刻み → 100m 刻み展開
  - ハロンタイムの 0.1 秒 → 秒変換

**テスト**

- 走破タイム変換の検証（複数パターン）
- ラップタイム展開の検証（200m 刻み → 100m 刻み、距離超過分の NaN）
- 出力 DataFrame のカラム構成がそれぞれ SCHEMA.md テーブル 2・3 に一致すること

---

## PR-11: MykeibaDBProvider — 残りのメソッド

**目的**: MykeibaDBProvider の残りのメソッドを実装し、Provider を完成させる

**実装内容**

- `get_win_show_odds`: `OddsGetter.get_odds1_tansho()` + `get_odds1_fukusho()` から取得・合体
  - オッズの 0.1 倍 → 倍変換
- `get_payoff`: `RaceGetter.get_haraimodoshi()` から取得
  - カラム名リネーム
- `get_past_performances`: `RaceGetter.get_umagoto_race_joho()` を馬 ID 指定で取得
  - `get_result` と同じ変換
- `get_schedule`: `RaceGetter.get_kaisai_schedule()` から取得
  - カラム名リネーム

**テスト**

- オッズ: 単勝・複勝の合体と変換の検証
- 払戻: カラム名リネームの対応が正しいこと
- 過去成績: 馬 ID 指定での取得・変換が正しいこと
- スケジュール: 日付範囲指定での取得が正しいこと
- 各メソッドの出力 DataFrame のカラム構成が SCHEMA.md の対応テーブルに一致すること

---

## PR-12: 両 Provider の出力一致テスト

**目的**: ScrapingProvider と MykeibaDBProvider の出力がスキーマレベルで一致することを検証する

**実装内容**

- 両 Provider の共通カラム（scraping ○ のカラム）で出力スキーマが一致することを検証するテストを追加
- テストフィクスチャとして、同一レースの scraping/mykeibadb 双方のモックデータを用意

**テストケースの選定**

- テストケースとなるレース・馬は `keiba-scraping/test/fixtures/race_test_cases.yml`、`test_horse_case.yml` から適切なケースもしくはすべてを選択する

**モックデータの準備**

- スクレイピング側のモックは keiba-scraping にある既存のモック（fixtures）をそのままコピペしてもよいし、HTML などからデータフレームに変換したものを新たに作成してもよい
- mykeibadb 側のモックはこれから取得すること。スクレイピング側と同じレース・馬のデータを取得すること
- スクレイピング側で使用しているレース ID を mykeibadb および統合スキーマで使用しているレースコードに変換するには日付情報が追加で必要。`entry_*.html` に日付情報もあるのでそこから取得すること

**注意事項**

- mykeibadb 側はDB更新ミスによりデータが完全に揃っていない可能性がある。テストが失敗しその原因が DB にそもそもデータが無いことであれば報告すること

**テスト**

- 全 8 メソッドについて、両 Provider の出力 DataFrame が同一カラム構成を持つこと
- 共通カラム（scraping ○ のカラム）の型と値が一致すること
- scraping で × のカラムが NaN であること

---

## PR-13: `__init__.py` 整備 + README + パッケージ公開準備

**目的**: パッケージとしての仕上げを行う

**実装内容**

- 各 `__init__.py` のエクスポート整備
- `README.md` の更新（インストール方法、使用方法、コード例）
- CI 設定（静的解析: isort, flake8, mypy + テスト実行）

**テスト**

- `from keiba_data_interface import DataInterface` のインポートが成功すること
- CI パイプラインが全てパスすること
