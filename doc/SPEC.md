# keiba-data-interface 仕様書

## 概要

競馬データを取得する複数のデータソース（netkeiba、JRA-VAN）を統一的なインターフェースで扱うためのライブラリ。

### 目的

- 無料だが不安定なnetkeibaからのスクレイピング（keiba-scraping）から有料で安定したJRA-VAN（mykeibadb-python）への移行を容易にする
- データソースの違いを意識せずに同じコードでデータ取得ができる

### アーキテクチャ

```
mykeibadb-python (JRA-VAN式スキーマ)
        ↓ MykeibaDBProvider (アダプター)
keiba-data-interface (mykeibadbベースの統一スキーマ)
        ↑ ScrapingProvider (アダプター)
keiba-scraping (netkeiba式スキーマ)
```

---

## 1. 責務の分離

### 各ライブラリの担当範囲

| 責務 | 担当ライブラリ |
|---|---|
| データの取得（HTTP/DB） | keiba-scraping / mykeibadb-python |
| データソース固有の整形 | keiba-scraping / mykeibadb-python |
| スキーマ統一 | keiba-data-interface |
| データソース切り替え | keiba-data-interface |

### 1.1 keiba-scrapingの整形範囲

**担当すべき整形**

- HTMLの構造に依存したパース処理
- netkeibaの表現形式に固有のフォーマット変換
  - 例：`"牡3"` → 性別・年齢に分割
  - 例：`"1-3-2-4"` → 1コーナー通過順〜4コーナー通過順に分割
- IDの抽出（馬ID、騎手ID、厩舎ID）

**実装方針**

- netkeibaのHTML固有の表現をアプリケーションで扱いやすい形に変換する処理
- **mykeibadb形式への変換は行わない**（独立性を保つため）

### 1.2 mykeibadb-pythonの整形範囲

**担当すべき整形**

- JRA-VANのコード体系に依存したデータ取得
- コード変換処理（`convert_codes=True`時）
  - 例：`keibajo_code` → 競馬場名
  - 例：`seibetsu_code` → 性別名

### 1.3 keiba-data-interfaceの整形範囲

**担当すべき整形**

- 両ソース間のカラム名マッピング
  - 例：keiba-scrapingの`競馬場` → 統一スキーマの`競馬場`（KEIBAJO_CODE→競馬場名）
- データ型の統一
  - 例：走破タイムの"M:SS.S"形式への統一
  - 例：負担重量の0.1kg→kg変換
- 不足カラムのNaN埋め
  - 例：keiba-scrapingで取得できない「品種」「毛色」等のカラム

---

## 2. スキーマ設計

### 2.1 設計方針

**mykeibadbのテーブル構造をベースとし、スクレイピングの効率を考慮して分割する**

**mykeibadbベースの理由**
- JRA-VANは一次ソースであり、netkeibaの情報もJRA-VANから提供されたもの
- 基本的に mykeibadbの情報量 > netkeibaのスクレイピング情報量
- mykeibadbで取得できる情報を欠落させないため

**テーブル分割の方針**
- mykeibadbのテーブル（RACE_SHOSAI等）をスクレイピングのページ単位に合わせて分割
- RACE_SHOSAIは「レース基本情報（EntryPageScraper対応）」と「レース結果情報（ResultPageScraper対応）」に分割

**カラム設計の方針**
- カラム名はmykeibadbのローマ字名を日本語に変更
- コード変換後のカラムのみを残す（コード変換前の初期カラムは削除）
- カラムは常に固定。scrapingで取得できないカラムはNaNを入れる

詳細は [SCHEMA.md](SCHEMA.md) を参照。

---

## 3. インターフェース設計

### 3.1 DataProvider Protocol

```python
from typing import Protocol
import pandas as pd

class DataProvider(Protocol):
    """データソースの抽象インターフェース"""

    def get_race_info(self, race_code: str) -> pd.DataFrame:
        """レース基本情報を取得"""
        ...

    def get_entry(self, race_code: str) -> pd.DataFrame:
        """出馬表を取得"""
        ...

    def get_odds(self, race_code: str) -> pd.DataFrame:
        """単複オッズを取得"""
        ...

    def get_result(self, race_code: str) -> pd.DataFrame:
        """レース結果（馬毎）を取得"""
        ...

    def get_race_result_info(self, race_code: str) -> pd.DataFrame:
        """レース結果情報（ラップ・コーナー通過順）を取得"""
        ...

    def get_payoff(self, race_code: str) -> pd.DataFrame:
        """払戻情報を取得"""
        ...

    def get_past_performances(self, horse_id: str) -> pd.DataFrame:
        """過去成績（馬柱）を取得"""
        ...

    def get_schedule(self, start_date: str, end_date: str) -> pd.DataFrame:
        """開催スケジュールを取得"""
        ...
```

### 3.2 Provider実装

```python
class ScrapingProvider:
    """keiba-scrapingを使用したデータ取得"""

    def get_race_info(self, race_code: str) -> pd.DataFrame:
        # EntryPageScraperで取得
        # 統一スキーマに変換
        # 不足カラムをNaNで埋める
        ...

class MykeibaDBProvider:
    """mykeibadb-pythonを使用したデータ取得"""

    def get_race_info(self, race_code: str) -> pd.DataFrame:
        # RACE_SHOSAIを取得
        # 統一スキーマに変換
        ...
```

### 3.3 利用者向けAPI

```python
# 利用例
from keiba_data_interface import DataInterface

# データソースを選択（環境変数や設定ファイルで切り替え可能）
interface = DataInterface(provider='scraping')  # or 'mykeibadb'

# 統一されたインターフェースでデータ取得
# レースコードは16桁（JRA-VAN式）で統一して渡す
# ScrapingProvider使用時は内部で12桁に変換して呼び出す（利用者は意識不要）
race_info = interface.get_race_info('2023010105010101')
entry = interface.get_entry('2023010105010101')
odds = interface.get_odds('2023010105010101')
result = interface.get_result('2023010105010101')
payoff = interface.get_payoff('2023010105010101')
past = interface.get_past_performances('2022105102')
schedule = interface.get_schedule('2025-01-01', '2025-01-31')
```

---

## 4. データ取得関数仕様

### 4.1 レース基本情報を取得する関数

| 項目 | 内容 |
|------|------|
| 関数名 | `get_race_info` |
| 引数 | `race_code: str`（レースコード） |
| 戻り値 | `pd.DataFrame`（1行） |
| テーブル | レース基本情報（SCHEMA.md テーブル1） |

#### Provider別実装

| Provider | 取得方法 |
|----------|---------|
| ScrapingProvider | 受け取った16桁レースコードを12桁に変換して`EntryPageScraper`に渡す。取得結果を統一スキーマに変換し、レースコードは引数の16桁をそのまま格納する |
| MykeibaDBProvider | `RaceGetter`を使用し、`get_race_shosai()`でレース詳細を取得。RECORD_SHUBETSU_ID〜DIRT_BABAJOTAI_CODEの範囲を統一スキーマに変換 |

#### 変換詳細

**ScrapingProviderの変換**

| scraping出力カラム | 統一スキーマカラム | 変換内容 |
|-------------------|-------------------|---------|
| レースID | レースコード | 引数の16桁レースコードをそのまま使用（scrapingの出力は使わない） |
| 日付 | 開催年 + 開催月日 | 日付→年と月日に分割 |
| 回 | 開催回 | そのまま |
| 開催日 | 開催日目 | そのまま |
| レース名 | 競走名本題 | そのまま |
| 競走条件 | 競走条件名称 | そのまま |
| 芝ダ, 左右 | トラック | 芝ダ+左右を結合してトラック文字列を構成 |
| コース, 内外 | コース区分 | コース+内外を結合 |
| 1着賞金〜5着賞金 | 本賞金1着〜5着 | 万円→百円単位に変換 |
| 頭数 | 出走頭数 | そのまま |
| 馬場 | 芝馬場状態 / ダート馬場状態 | 芝ダに応じて適切なカラムに格納 |
| （不足カラム） | 特別競走番号, 競走名副題, ... | NaN |

**MykeibaDBProviderの変換**

| mykeibadb出力カラム | 統一スキーマカラム | 変換内容 |
|-------------------|-------------------|---------|
| HASSO_JIKOKU | 発走時刻 | "1540"→"15:40"に変換 |
| コード変換済みカラム | 対応する日本語カラム | カラム名をリネーム |

---

### 4.2 出馬表を取得する関数

| 項目 | 内容 |
|------|------|
| 関数名 | `get_entry` |
| 引数 | `race_code: str`（レースコード） |
| 戻り値 | `pd.DataFrame`（出走頭数行） |
| テーブル | 馬毎レース情報（SCHEMA.md テーブル3） |

#### Provider別実装

| Provider | 取得方法 |
|----------|---------|
| ScrapingProvider | `EntryPageScraper`を使用し、`get_entry()`で出馬表を取得。統一スキーマに変換 |
| MykeibaDBProvider | `RaceGetter`を使用し、`get_umagoto_race_joho()`で馬毎レース情報をレースコード指定で取得。統一スキーマに変換 |

#### 変換詳細

**ScrapingProviderの変換**

| scraping出力カラム | 統一スキーマカラム | 変換内容 |
|-------------------|-------------------|---------|
| レースID | レースコード | 引数の16桁レースコードをそのまま使用（scrapingの出力は使わない） |
| 枠 | 枠番 | そのまま |
| 馬ID | 血統登録番号 | そのまま |
| 年齢 | 馬齢 | そのまま |
| 斤量 | 負担重量 | そのまま（kg単位） |
| 騎手 | 騎手名略称 | そのまま |
| 騎手ID | 騎手コード | そのまま |
| 厩舎 | 調教師名略称 | そのまま |
| 厩舎ID | 調教師コード | そのまま |
| 増減 | 増減符号 + 増減差 | 符号付き整数→符号と差に分離 |
| 出走区分 | 異常区分 | "出走"→""、"取消"→"取消"、"除外"→"除外" |
| （不足カラム） | 品種, 毛色, 馬主コード, ... | NaN |

**MykeibaDBProviderの変換**

| mykeibadb出力カラム | 統一スキーマカラム | 変換内容 |
|-------------------|-------------------|---------|
| FUTAN_JURYO | 負担重量 | 0.1kg単位→kg単位 |
| コード変換済みカラム | 対応する日本語カラム | カラム名をリネーム |

---

### 4.3 オッズを取得する関数

| 項目 | 内容 |
|------|------|
| 関数名 | `get_odds` |
| 引数 | `race_code: str`（レースコード） |
| 戻り値 | `pd.DataFrame`（出走頭数行） |
| テーブル | 単複オッズ情報（SCHEMA.md テーブル5） |

#### Provider別実装

| Provider | 取得方法 |
|----------|---------|
| ScrapingProvider | `scrape_odds_from_jra()`を使用してオッズを取得。統一スキーマに変換 |
| MykeibaDBProvider | `OddsGetter`を使用し、`get_odds1_tansho()`と`get_odds1_fukusho()`でそれぞれ取得・合体して統一スキーマに変換 |

#### 変換詳細

**ScrapingProviderの変換**

| scraping出力カラム | 統一スキーマカラム | 変換内容 |
|-------------------|-------------------|---------|
| 複勝最小オッズ | 複勝最低オッズ | そのまま |
| 複勝最大オッズ | 複勝最高オッズ | そのまま |
| （不足カラム） | レースコード, 開催年, ... | レースコードから導出 or NaN |

**MykeibaDBProviderの変換**

| mykeibadb出力カラム | 統一スキーマカラム | 変換内容 |
|-------------------|-------------------|---------|
| ODDS | 単勝オッズ | 0.1倍単位→倍単位 |
| ODDS_SAITEI | 複勝最低オッズ | 0.1倍単位→倍単位 |
| ODDS_SAIKOU | 複勝最高オッズ | 0.1倍単位→倍単位 |

---

### 4.4 レース結果（馬毎）を取得する関数

| 項目 | 内容 |
|------|------|
| 関数名 | `get_result` |
| 引数 | `race_code: str`（レースコード） |
| 戻り値 | `pd.DataFrame`（出走頭数行） |
| テーブル | 馬毎レース情報（SCHEMA.md テーブル3） |

#### Provider別実装

| Provider | 取得方法 |
|----------|---------|
| ScrapingProvider | `ResultPageScraper`を使用し、`get_result()`でレース結果を取得。統一スキーマに変換 |
| MykeibaDBProvider | `RaceGetter`を使用し、`get_umagoto_race_joho()`で馬毎レース情報をレースコード指定で取得。統一スキーマに変換 |

#### 変換詳細

**ScrapingProviderの変換**

`get_entry`と同様のカラムマッピングに加え、以下の結果固有カラム：

| scraping出力カラム | 統一スキーマカラム | 変換内容 |
|-------------------|-------------------|---------|
| 着順 | 確定着順 | そのまま |
| タイム | 走破タイム | そのまま（"M:SS.S"形式） |
| 着差 | 着差1 | そのまま（降着情報は異常区分で処理） |
| 人気 | 単勝人気順 | そのまま |
| 後3F | 後3ハロン | そのまま |
| 1〜4コーナー通過順 | 1〜4コーナー順位 | そのまま |
| 異常区分 | 異常区分 | "除外"は一律"除外"（="3"相当）として統一 |
| （タイムから算出） | タイム差 | 1着タイムとの差を計算 |
| （着順+RaceInfo賞金） | 獲得本賞金 | 着順とRaceInfoの1〜5着賞金から導出 |
| （不足カラム） | 後4ハロン, 脚質判定, ... | NaN |

**MykeibaDBProviderの変換**

`get_entry`と同じ変換に加え、結果カラムが追加で含まれる。mykeibadbでは出馬表と結果が同じテーブル（UMAGOTO_RACE_JOHO）に格納されており、DATA_KUBUNで区別される。

---

### 4.5 レース結果情報（ラップ・コーナー通過順）を取得する関数

| 項目 | 内容 |
|------|------|
| 関数名 | `get_race_result_info` |
| 引数 | `race_code: str`（レースコード） |
| 戻り値 | `pd.DataFrame`（1行） |
| テーブル | レース結果情報（SCHEMA.md テーブル2） |

#### Provider別実装

| Provider | 取得方法 |
|----------|---------|
| ScrapingProvider | `ResultPageScraper`を使用し、`get_lap_time()`と`get_corner()`でラップタイムとコーナー通過順を取得。統一スキーマに変換 |
| MykeibaDBProvider | `RaceGetter`を使用し、`get_race_shosai()`でレース詳細を取得。LAP_TIME1〜RECORD_KOSHIN_KUBUNの範囲を統一スキーマに変換 |

#### 変換詳細

**ScrapingProviderの変換**

| scraping出力カラム | 統一スキーマカラム | 変換内容 |
|-------------------|-------------------|---------|
| 100m〜5000m | 100m〜5000m | そのまま（100m刻み） |
| ペース | （対応なし） | 統一スキーマには含まない |
| レース前3F | 前3ハロン | ラップタイムから算出可能な場合 |
| レース後3F | 後3ハロン | ラップタイムから算出可能な場合 |
| （不足カラム） | 前4ハロン, 後4ハロン, 周回数, ... | NaN |

**MykeibaDBProviderの変換**

| mykeibadb出力カラム | 統一スキーマカラム | 変換内容 |
|-------------------|-------------------|---------|
| LAP_TIME1〜25 | 100m〜5000m | 200m刻み→100m刻みに展開。0.1秒→秒に変換 |
| ZENHAN_3F | 前3ハロン | 0.1秒→秒に変換 |
| ZENHAN_4F | 前4ハロン | 0.1秒→秒に変換 |
| KOHAN_3F | 後3ハロン | 0.1秒→秒に変換 |
| KOHAN_4F | 後4ハロン | 0.1秒→秒に変換 |

---

### 4.6 レースの払戻情報を取得する関数

| 項目 | 内容 |
|------|------|
| 関数名 | `get_payoff` |
| 引数 | `race_code: str`（レースコード） |
| 戻り値 | `pd.DataFrame`（1行） |
| テーブル | 払戻情報（SCHEMA.md テーブル4） |

#### Provider別実装

| Provider | 取得方法 |
|----------|---------|
| ScrapingProvider | `ResultPageScraper`を使用し、各券種の`get_*_payoff()`で払戻情報を取得。全券種を1行に結合して統一スキーマに変換 |
| MykeibaDBProvider | `RaceGetter`を使用し、`get_haraimodoshi()`で払戻情報を取得。統一スキーマに変換 |

#### 変換詳細

**ScrapingProviderの変換**

| scraping出力カラム | 統一スキーマカラム | 変換内容 |
|-------------------|-------------------|---------|
| 各券種の馬番/組番/払戻金/人気 | 対応する統一スキーマカラム | カラム名をリネーム |
| （不足カラム） | 不成立フラグ, 特払フラグ, 返還フラグ, ... | NaN |

scrapingでは以下の関数から券種別に取得し、1行のDataFrameに結合する：
- `get_win_payoff()` → 単勝
- `get_show_payoff()` → 複勝
- `get_bracket_payoff()` → 枠連
- `get_quinella_payoff()` → 馬連
- `get_quinella_place_payoff()` → ワイド
- `get_exacta_payoff()` → 馬単
- `get_trio_payoff()` → 3連複
- `get_trifecta_payoff()` → 3連単

**MykeibaDBProviderの変換**

| mykeibadb出力カラム | 統一スキーマカラム | 変換内容 |
|-------------------|-------------------|---------|
| 各券種カラム | 対応する日本語カラム | カラム名をリネーム |

---

### 4.7 馬柱（過去成績）を取得する関数

| 項目 | 内容 |
|------|------|
| 関数名 | `get_past_performances` |
| 引数 | `horse_id: str`（馬ID = 血統登録番号） |
| 戻り値 | `pd.DataFrame`（出走回数行。新馬の場合は0行） |
| テーブル | 馬毎レース情報（SCHEMA.md テーブル3） |

#### Provider別実装

| Provider | 取得方法 |
|----------|---------|
| ScrapingProvider | `PastPerformancesScraper`を使用し、`get_past_performances()`で過去成績を取得。統一スキーマに変換 |
| MykeibaDBProvider | `RaceGetter`を使用し、`get_umagoto_race_joho()`で馬毎レース情報を馬ID指定で取得。統一スキーマに変換 |

#### 変換詳細

**ScrapingProviderの変換**

`get_result`と類似の変換に加え、過去成績固有のカラム：

| scraping出力カラム | 統一スキーマカラム | 変換内容 |
|-------------------|-------------------|---------|
| 日付 | 開催年 + 開催月日 | 日付→年と月日に分割 |
| 回 | 開催回 | そのまま |
| 開催日 | 開催日目 | そのまま |
| R | レース番号 | そのまま |
| 賞金 | 獲得本賞金 | 万円→百円単位に変換 |
| 勝ち馬(2着馬) | 相手1馬名 | そのまま |
| （不足カラム） | 相手2〜3馬名, 馬主コード, ... | NaN |

**MykeibaDBProviderの変換**

`get_result`と同じ変換を適用。

---

### 4.8 開催スケジュールを取得する関数

| 項目 | 内容 |
|------|------|
| 関数名 | `get_schedule` |
| 引数 | `start_date: str`（開始日 "YYYY-MM-DD"）, `end_date: str`（終了日 "YYYY-MM-DD"） |
| 戻り値 | `pd.DataFrame`（開催場数行） |
| テーブル | 開催スケジュール情報（SCHEMA.md テーブル6） |

#### Provider別実装

| Provider | 取得方法 |
|----------|---------|
| ScrapingProvider | `RaceScheduleScraper`を使用し、`get_race_schedule()`で開催スケジュールを取得。レース情報を開催場単位に集約して統一スキーマに変換 |
| MykeibaDBProvider | `RaceGetter`を使用し、`get_kaisai_schedule()`で開催スケジュールを日付の範囲指定で取得。統一スキーマに変換 |

#### 変換詳細

**ScrapingProviderの変換**

scrapingの`get_race_schedule()`は各レース単位で情報を返すため、開催場単位に集約する必要がある。

| scraping出力カラム | 統一スキーマカラム | 変換内容 |
|-------------------|-------------------|---------|
| レースID | 開催コード | レースIDから開催コードを導出 |
| 日付 | 開催年 + 開催月日 | 日付→年と月日に分割 |
| 回 | 開催回 | そのまま |
| 開催日 | 開催日目 | そのまま |
| （不足カラム） | 曜日, 重賞1〜3情報 | NaN |

**MykeibaDBProviderの変換**

| mykeibadb出力カラム | 統一スキーマカラム | 変換内容 |
|-------------------|-------------------|---------|
| コード変換済みカラム | 対応する日本語カラム | カラム名をリネーム |
