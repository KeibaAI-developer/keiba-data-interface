# 統一スキーマ定義

## 概要

keiba-data-interfaceは、keiba-scraping（netkeiba）とmykeibadb-python（JRA-VAN）の出力を統一スキーマに変換する。
本ドキュメントは、各テーブルのカラム定義・データ型・Provider対応状況・マッピングルールを定義する。

### 設計方針

- **mykeibadbのテーブル構造をベースとする**: JRA-VANは一次ソースであり、netkeibaに公開されている情報もJRA-VANから提供されたものであるため、mykeibadbで取得できる情報を欠落させない
- **カラム名は日本語に変更する**: mykeibadbのローマ字カラム名を日本語に変換し読みやすくする
- **テーブル分割はスクレイピングの効率を考慮する**: mykeibadbのテーブルをスクレイピングのページ単位に合わせて分割する
- **カラムは常に固定**: scrapingで取得できないカラムはNaNを入れる

---

## ID体系

| ID種別 | scraping形式 | mykeibadb形式 | 備考 |
|--------|-------------|---------------|------|
| レースコード | netkeiba式 12桁<br>年(4)+競馬場(2)+回(2)+日目(2)+R(2)<br>例: `202505021211` | JRA-VAN式 16桁<br>年(4)+月日(4)+競馬場(2)+回(2)+日目(2)+R(2)<br>例: `2025050206021211` | 統一スキーマでは16桁（JRA-VAN式）で管理する。 |
| 血統登録番号 | 10桁<br>生年(4)+品種(1)+連番(5) | 10桁<br>生年(4)+品種(1)+連番(5) | 両Providerで同一 |
| 騎手コード | JRA騎手コード 5桁 | JRA騎手コード 5桁 | 両Providerで同一 |
| 調教師コード | JRA調教師コード 5桁 | JRA調教師コード 5桁 | 両Providerで同一 |
| 馬主コード | JRA馬主コード 6桁 | JRA馬主コード 6桁 | 両Providerで同一 |
| 生産者コード | JRA生産者コード 6桁<br>例: `373126`（ノーザンファーム） | JRA生産者コード 8桁<br>例: `37312600`（ノーザンファーム） | 先頭6桁は同一。mykeibadbのコードは末尾に`00`が付加された8桁形式。 |

---

## テーブル一覧

| テーブル名 | 関数 | 行数 |
|:----------|:-----|:-----|
| [レース基本情報](./SCHEMA/RACE_BASIC_INFO.md) | `get_race_basic_info()` | 1行 |
| [レース結果情報](./SCHEMA/RACE_RESULT_INFO.md) | `get_race_result_info()` | 1行 |
| [馬毎レース情報](./SCHEMA/RACE_INFO_BY_HORSE.md) | `get_entry()` / `get_result()` / `get_past_performances()` | 出走頭数/過去レース分の行数 |
| [競走馬マスタ](./SCHEMA/HORSE_MASTER.md) | `get_horse_master()` | 1行 |
| [払戻情報](./SCHEMA/PAYOFF.md) | `get_payoff()` | 1行 |
| [単複オッズ情報](./SCHEMA/WIN_SHOW_ODDS.md) | `get_win_show_odds()` | 出走頭数分の行数 |
| [開催スケジュール情報](./SCHEMA/SCHEDULE.md) | `get_schedule()` | 開催場数の行数 |
