# keiba-data-interface

## 概要

`keiba-data-interface`は、複数の競馬データソース（netkeibaスクレイピング、JRA-VANデータベース）を**統一されたインターフェース**で扱うためのPythonライブラリです。

`DataInterface`クラスにプロバイダー名を渡すだけで、データソースを切り替えながら同一のAPIで`pandas.DataFrame`としてデータを取得できます。

以下のデータを取得できます：

- レース基本情報（レース名、距離、コース、天候、馬場状態等）
- 出馬表（枠番、馬番、馬名、騎手、斤量、馬体重等）
- 単複オッズ（単勝・複勝オッズ）
- レース結果（確定着順、走破タイム、着差、コーナー通過順等）
- レース結果情報（ラップタイム、コーナー通過順）
- 払戻情報（単勝・複勝・枠連・馬連・ワイド・馬単・3連複・3連単）
- 過去成績・馬柱（馬ID指定で取得）
- 競走馬情報（生年月日、血統、調教師、累計成績等）
- 開催スケジュール（日別の開催レース一覧）


## 動作要件

- Python 3.12以上


## 依存パッケージ

- `pandas>=2.0.0`

プロバイダーに応じて追加の依存パッケージが必要です：

| プロバイダー | 追加依存パッケージ |
|---|---|
| `scraping` | `keiba-scraping`（netkeibaおよびJRA公式サイトのスクレイピング） |
| `mykeibadb` | `mykeibadb-python`（JRA-VAN PostgreSQLデータベース接続） |


## インストール

`keiba-scraping`・`mykeibadb-python`はPyPIに公開されていないため、事前にリポジトリをcloneしてインストールする必要があります。

### 1. 依存ライブラリのインストール

```bash
# scrapingプロバイダーを使用する場合
git clone https://github.com/KeibaAI-developer/keiba-scraping
pip install -e ./keiba-scraping

# mykeibadbプロバイダーを使用する場合
git clone https://github.com/KeibaAI-developer/mykeibadb-python
pip install -e ./mykeibadb-python
```

### 2. keiba-data-interfaceのインストール

```bash
# 基本インストール（DataInterfaceクラスのみ）
pip install -e "/path/to/keiba-data-interface"

# scrapingプロバイダーを使用する場合
pip install -e "/path/to/keiba-data-interface[scraping]"

# mykeibadbプロバイダーを使用する場合
pip install -e "/path/to/keiba-data-interface[mykeibadb]"
```


## セットアップ

### scrapingプロバイダーを使用する場合

keiba-scrapingが利用する外部ツール（ChromeDriver、Playwright等）のセットアップが必要です。
詳細は[keiba-scraping の README](https://github.com/KeibaAI-developer/keiba-scraping/blob/main/README.md)を参照してください。

### mykeibadbプロバイダーを使用する場合

mykeibadb-pythonが利用するPostgreSQLサーバーへの接続設定が必要です。
詳細は[mykeibadb-python の README](https://github.com/KeibaAI-developer/mykeibadb-python/blob/main/README.md)を参照してください。


## 使い方

### 基本的な使い方

`DataInterface`にプロバイダー名（`'scraping'` または `'mykeibadb'`）を渡してインスタンス化し、メソッドを呼ぶだけでデータを取得できます。

```python
from keiba_data_interface import DataInterface

# scrapingプロバイダーを使用
di = DataInterface("scraping")

# 16桁レースコードを指定してレース基本情報を取得
race_code = "2025060105021211"
df = di.get_race_basic_info(race_code)
print(df)
```

### プロバイダーの切り替え

プロバイダー名を変えるだけで、同じAPIでデータソースを切り替えられます。

```python
from keiba_data_interface import DataInterface

race_code = "2025060105021211"

# scrapingプロバイダー（netkeiba / JRA公式スクレイピング）
di_scraping = DataInterface("scraping")
df_scraping = di_scraping.get_race_basic_info(race_code)

# mykeibadbプロバイダー（JRA-VAN PostgreSQLデータベース）
di_mydb = DataInterface("mykeibadb")
df_mydb = di_mydb.get_race_basic_info(race_code)

# 返却される統一スキーマは同一
assert list(df_scraping.columns) == list(df_mydb.columns)
```


## API一覧

`DataInterface`クラスが提供するメソッドの一覧です。すべてのメソッドで統一スキーマの`pandas.DataFrame`が返されます。

| メソッド | 引数 | 戻り値の行数 | サンプルコード |
|---|---|---|---|
| `get_race_basic_info(race_code)` | 16桁レースコード | 1行 | [example_race_info.py](example/example_race_info.py) |
| `get_entry(race_code)` | 16桁レースコード | 出走頭数行 | [example_entry.py](example/example_entry.py) |
| `get_win_show_odds(race_code)` | 16桁レースコード | 出走頭数行 | [example_win_show_odds.py](example/example_win_show_odds.py) |
| `get_result(race_code)` | 16桁レースコード | 出走頭数行 | [example_result.py](example/example_result.py) |
| `get_race_result_info(race_code)` | 16桁レースコード | 1行 | [example_race_result_info.py](example/example_race_result_info.py) |
| `get_payoff(race_code)` | 16桁レースコード | 1行 | [example_payoff.py](example/example_payoff.py) |
| `get_past_performances(horse_id)` | 血統登録番号 | 出走回数行 | [example_past_performances.py](example/example_past_performances.py) |
| `get_horse_master(horse_id)` | 血統登録番号 | 1行 | [example_horse_master.py](example/example_horse_master.py) |
| `get_schedule(start_date, end_date)` | 開始日・終了日（YYYY-MM-DD） | 開催レース数行 | [example_schedule.py](example/example_schedule.py) |


## プロバイダーの違い

| 項目 | `scraping` | `mykeibadb` |
|---|---|---|
| データソース | netkeiba / JRA公式サイト | JRA-VAN PostgreSQLデータベース |
| リアルタイム性 | 高い（サイトの更新に追従） | mykeibadbの取込タイミングに依存 |
| 安定性 | サイト構造変更で壊れる可能性あり | スキーマが安定 |
| オフライン利用 | 不可 | 可（DB接続があれば） |
| 取得可能な過去データ | ネットに残っている範囲 | mykeibadbが保持している範囲 |


## ドキュメント

### スキーマ定義

各メソッドが返す`DataFrame`のカラム定義は以下を参照してください：

- [レース基本情報（RACE_BASIC_INFO.md）](doc/SCHEMA/RACE_BASIC_INFO.md)
- [馬毎レース情報 / 出馬表・結果（RACE_INFO_BY_HORSE.md）](doc/SCHEMA/RACE_INFO_BY_HORSE.md)
- [レース結果情報（RACE_RESULT_INFO.md）](doc/SCHEMA/RACE_RESULT_INFO.md)
- [単複オッズ（WIN_SHOW_ODDS.md）](doc/SCHEMA/WIN_SHOW_ODDS.md)
- [払戻情報（PAYOFF.md）](doc/SCHEMA/PAYOFF.md)
- [競走馬情報（HORSE_MASTER.md）](doc/SCHEMA/HORSE_MASTER.md)
- [開催スケジュール（SCHEDULE.md）](doc/SCHEMA/SCHEDULE.md)
