# レース時刻表

指定した日付の全レースの時刻表。レース数の行数のDataFrame（レースコード昇順）。開催が無い日は0行。

関数: `DataInterface.get_race_schedule()`

対応元:
- mykeibadb: `RACE_SHOSAI`（データ区分が9のレース中止は含めない）
- scraping: `RaceScheduleScraper.get_race_schedule()`（netkeibaのレース一覧ページに載っているレース）

| カラム名 | 型 | scraping | mykeibadb | 説明 | 例 | 差分A | 差分B |
|----------|----|----------|-----------|------|----|------|------|
| レースコード | str | ○ | ○ | 年+月日+競馬場コード+回次+日次+レース番号の16桁 | "2025040609020411" | | |
| 競馬場コード | str | ○ | ○ | 該当レース施行競馬場。[コード表2001](../CODE_TABLE.md#KEIBAJO_CODE)参照 | "09" | | |
| レース番号 | int | ○ | ○ | 1〜12 | 11 | | |
| 発走時刻 | str | ○ | ○ | "HH:MM"形式。未設定は欠損 | "15:40" | | |
| 競走名 | str | ○ | ○ | mykeibadbは競走名本題、scrapingはレース一覧ページのレース名 | "大阪杯" | A1 | |

## 差分A: プロバイダー間の既知差分

- A1: 競走名の表記が異なる。mykeibadbは競走名本題（全角30文字）、scrapingはレース一覧ページの表記

## 差分B: mykeibadbテーブルとの差分

なし
