# 統一スキーマ定義

## 概要

keiba-data-interfaceは、keiba-scraping（netkeiba）とmykeibadb-python（JRA-VAN）の出力を統一スキーマに変換する。
本ドキュメントは、各テーブルのカラム定義・データ型・Provider対応状況・マッピングルールを定義する。

### 設計方針

- **mykeibadbのテーブル構造をベースとする**: JRA-VANは一次ソースであり、netkeibaに公開されている情報もJRA-VANから提供されたものであるため、mykeibadbで取得できる情報を欠落させない
- **カラム名は日本語に変更する**: mykeibadbのローマ字カラム名を日本語に変換し、利用者にとって扱いやすくする
- **コード変換後のカラムのみを残す**: mykeibadb側で`convert_codes=True`によりコード→名称に変換されるカラムは、変換後のカラムだけを残し、コード変換前の初期カラムは削除する
- **テーブル分割はスクレイピングの効率を考慮する**: mykeibadbのテーブル（RACE_SHOSAI等）をスクレイピングのページ単位に合わせて分割する
- **カラムは常に固定**: scrapingで取得できないカラムはNaNを入れる

### 凡例

| 記号 | 意味 |
|------|------|
| ○ | 対応あり（Providerがデータを供給可能） |
| × | 対応なし（NaN埋め） |

---

## ID体系

| ID種別 | scraping形式 | mykeibadb形式 | 変換要否 | 備考 |
|--------|-------------|---------------|---------|------|
| レースコード | netkeiba式 12桁<br>年(4)+競馬場(2)+回(2)+日目(2)+R(2)<br>例: `202505021211` | JRA-VAN式 16桁<br>年(4)+月日(4)+競馬場(2)+回(2)+日目(2)+R(2)<br>例: `2025050206021211` | **要変換** | **統一スキーマでは16桁（JRA-VAN式）で管理する。** ScrapingProviderへ渡す際は月日部分(4桁)を除去して12桁のレースIDに変換する |
| 馬ID（血統登録番号） | 10桁<br>生年(4)+品種(1)+連番(5)<br>例: `2022105102` | 10桁<br>生年(4)+品種(1)+連番(5)<br>例: `2022105102` | 不要 | 両Providerで同一 |
| 騎手コード | JRA騎手コード 5桁 | JRA騎手コード 5桁 | 不要 | 両Providerで同一 |
| 調教師コード | JRA調教師コード 5桁 | JRA調教師コード 5桁 | 不要 | 両Providerで同一 |
| 馬主コード | 6桁<br>例: `226800`（サンデーレーシング） | 6桁<br>例: `226800`（サンデーレーシング） | 不要 | 両Providerで同一 |
| 生産者コード | 6桁<br>例: `373126`（ノーザンファーム） | 8桁<br>例: `37312600`（ノーザンファーム） | **要注意** | 先頭6桁は同一体系。mykeibadbのコードは末尾に`00`が付加された8桁形式。scrapingの6桁はmykeibadbの先頭6桁に対応 |

---

## テーブル定義

### 1. レース基本情報

RACE_SHOSAIテーブルのうち、EntryPageScraperで取得できる範囲（レース基本情報〜馬場状態）に対応する。1行のDataFrame。

対応元:
- mykeibadb: `RACE_SHOSAI`（RECORD_SHUBETSU_ID〜DIRT_BABAJOTAI_CODE）
- scraping: `EntryPageScraper.get_race_info()`

| # | カラム名 | 型 | scraping | mykeibadb元カラム | 備考 |
|---|----------|------|----------|-------------------|------|
| 1 | レースコード | str | ○ | RACE_CODE | 16桁（JRA-VAN式）で統一。scrapingから取得した場合は12桁→16桁に変換 |
| 2 | 開催年 | str | ○ | KAISAI_NEN | |
| 3 | 開催月日 | str | ○ | KAISAI_GAPPI | |
| 4 | 競馬場 | str | ○ | KEIBAJO_CODE→競馬場名 | "東京","中山"等。コード変換後 |
| 5 | 開催回 | int | ○ | KAISAI_KAI | 第N回 |
| 6 | 開催日目 | int | ○ | KAISAI_NICHIME | N日目 |
| 7 | レース番号 | int | ○ | RACE_BANGO | |
| 8 | 曜日 | str | ○ | YOBI_CODE→曜日名 | "日","月",...,"土"。コード変換後 |
| 9 | 特別競走番号 | int | × | TOKUBETSU_KYOSO_BANGO | |
| 10 | 競走名本題 | str | ○ | KYOSOMEI_HONDAI | |
| 11 | 競走名副題 | str | × | KYOSOMEI_FUKUDAI | スポンサー名等 |
| 12 | 競走名カッコ内 | str | × | KYOSOMEI_KAKKONAI | 条件やトライアル対象等 |
| 13 | 競走名本題欧字 | str | × | KYOSOMEI_HONDAI_ENG | |
| 14 | 競走名副題欧字 | str | × | KYOSOMEI_FUKUDAI_ENG | |
| 15 | 競走名カッコ内欧字 | str | × | KYOSOMEI_KAKKONAI_ENG | |
| 16 | 競走名略称10文字 | str | × | KYOSOMEI_RYAKUSHO_10 | |
| 17 | 競走名略称6文字 | str | × | KYOSOMEI_RYAKUSHO_6 | |
| 18 | 競走名略称3文字 | str | × | KYOSOMEI_RYAKUSHO_3 | |
| 19 | 競走名区分 | str | × | KYOSOMEI_KUBUN | |
| 20 | 重賞回次 | int | × | JUSHO_KAIJI | 第N回 |
| 21 | グレードコード | str | ○ | GRADE_CODE | "A"=G1,"B"=G2,"C"=G3,"F"=JG1,"L"=L,"E"=特別,"_"=一般競走。コードで保持。scraping側はG1→A等に変換 |
| 22 | 変更前グレードコード | str | × | HENKOMAE_GRADE_CODE | コードで保持 |
| 23 | 競走種別 | str | ○ | KYOSO_SHUBETSU_CODE→競走種別名 | "サラ系３歳以上"等。コード変換後 |
| 24 | 競走記号 | str | ○ | KYOSO_KIGO_CODE→競走記号名 | "(国際)(指)"等。コード変換後 |
| 25 | 重量種別 | str | ○ | JURYO_SHUBETSU_CODE→重量種別名 | "定量","別定","ハンデ","馬齢"。コード変換後 |
| 26 | 競走条件2歳 | str | × | KYOSO_JOKEN_CODE_2SAI | |
| 27 | 競走条件3歳 | str | × | KYOSO_JOKEN_CODE_3SAI | |
| 28 | 競走条件4歳 | str | × | KYOSO_JOKEN_CODE_4SAI | |
| 29 | 競走条件5歳以上 | str | × | KYOSO_JOKEN_CODE_5SAI_IJO | |
| 30 | 競走条件最若年 | str | × | KYOSO_JOKEN_CODE_SAIJAKUNEN | |
| 31 | 競走条件名称 | str | ○ | KYOSO_JOKEN_MEISHO | "オープン","２勝クラス","新馬"等 |
| 32 | 距離 | int | ○ | KYORI | メートル単位 |
| 33 | 変更前距離 | int | × | HENKOMAE_KYORI | |
| 34 | トラック | str | ○ | TRACK_CODE→トラック名 | コード変換後。"芝","ダ","障"と"左","右","直"を含む |
| 35 | 変更前トラック | str | × | HENKOMAE_TRACK_CODE→トラック名 | コード変換後 |
| 36 | コース区分 | str | ○ | COURSE_KUBUN→コース区分名 | "A","B","C","D"。コード変換後。内外情報も含む |
| 37 | 変更前コース区分 | str | × | HENKOMAE_COURSE_KUBUN→コース区分名 | コード変換後 |
| 38 | 本賞金1着 | int | ○ | HONSHOKIN1 | 百円単位（mykeibadb生値） |
| 39 | 本賞金2着 | int | ○ | HONSHOKIN2 | 百円単位 |
| 40 | 本賞金3着 | int | ○ | HONSHOKIN3 | 百円単位 |
| 41 | 本賞金4着 | int | ○ | HONSHOKIN4 | 百円単位 |
| 42 | 本賞金5着 | int | ○ | HONSHOKIN5 | 百円単位 |
| 43 | 本賞金6着 | int | × | HONSHOKIN6 | 百円単位 |
| 44 | 本賞金7着 | int | × | HONSHOKIN7 | 百円単位 |
| 45 | 変更前本賞金1着 | int | × | HENKOMAE_HONSHOKIN1 | 百円単位 |
| 46 | 変更前本賞金2着 | int | × | HENKOMAE_HONSHOKIN2 | 百円単位 |
| 47 | 変更前本賞金3着 | int | × | HENKOMAE_HONSHOKIN3 | 百円単位 |
| 48 | 変更前本賞金4着 | int | × | HENKOMAE_HONSHOKIN4 | 百円単位 |
| 49 | 変更前本賞金5着 | int | × | HENKOMAE_HONSHOKIN5 | 百円単位 |
| 50 | 付加賞金1着 | int | × | FUKASHOKIN1 | 百円単位 |
| 51 | 付加賞金2着 | int | × | FUKASHOKIN2 | 百円単位 |
| 52 | 付加賞金3着 | int | × | FUKASHOKIN3 | 百円単位 |
| 53 | 付加賞金4着 | int | × | FUKASHOKIN4 | 百円単位 |
| 54 | 付加賞金5着 | int | × | FUKASHOKIN5 | 百円単位 |
| 55 | 変更前付加賞金1着 | int | × | HENKOMAE_FUKASHOKIN1 | 百円単位 |
| 56 | 変更前付加賞金2着 | int | × | HENKOMAE_FUKASHOKIN2 | 百円単位 |
| 57 | 変更前付加賞金3着 | int | × | HENKOMAE_FUKASHOKIN3 | 百円単位 |
| 58 | 発走時刻 | str | ○ | HASSO_JIKOKU | "HH:MM"形式 |
| 59 | 変更前発走時刻 | str | × | HENKOMAE_HASSO_JIKOKU | "HH:MM"形式 |
| 60 | 登録頭数 | int | × | TOROKU_TOSU | |
| 61 | 出走頭数 | int | ○ | SHUSSO_TOSU | |
| 62 | 入線頭数 | int | × | NYUSEN_TOSU | |
| 63 | 天候 | str | ○ | TENKO_CODE→天候名 | "晴","曇","雨","小雨","小雪","雪"。コード変換後 |
| 64 | 芝馬場状態 | str | ○ | SHIBA_BABAJOTAI_CODE→馬場状態名 | "良","稍","重","不"。コード変換後 |
| 65 | ダート馬場状態 | str | ○ | DIRT_BABAJOTAI_CODE→馬場状態名 | "良","稍","重","不"。コード変換後 |

#### NaN条件

| カラム | NaN条件 |
|--------|---------|
| 天候 | scraping: 出走確定前 |
| 芝馬場状態 | scraping: 出走確定前 / ダートレースの場合 |
| ダート馬場状態 | scraping: 出走確定前 / 芝レースの場合 |
| グレードコード | 一般競走（値="_"）|
| 競走名副題〜競走名カッコ内欧字 | 該当なしの場合 |

---

### 2. レース結果情報

RACE_SHOSAIテーブルのうち、ResultPageScraperで取得できる範囲（ラップタイム・コーナー通過順・ハロンタイム）に対応する。1行のDataFrame。

対応元:
- mykeibadb: `RACE_SHOSAI`（LAP_TIME1〜RECORD_KOSHIN_KUBUN）
- scraping: `ResultPageScraper.get_lap_time()` + `ResultPageScraper.get_corner()`

| # | カラム名 | 型 | scraping | mykeibadb元カラム | 備考 |
|---|----------|------|----------|-------------------|------|
| 1 | レースコード | str | ○ | RACE_CODE | |
| 2 | ラップ100m | float | ○ | LAP_TIME1から展開 | 秒単位。100m刻みに展開 |
| 3 | ラップ200m | float | ○ | LAP_TIME1 | 秒単位。0.1秒単位から変換 |
| 4 | ラップ300m | float | ○ | LAP_TIME2から展開 | 秒単位 |
| 5 | ラップ400m | float | ○ | LAP_TIME2 | 秒単位 |
| 6 | ラップ500m | float | ○ | LAP_TIME3から展開 | 秒単位 |
| 7 | ラップ600m | float | ○ | LAP_TIME3 | 秒単位 |
| 8 | ラップ700m | float | ○ | LAP_TIME4から展開 | 秒単位 |
| 9 | ラップ800m | float | ○ | LAP_TIME4 | 秒単位 |
| 10 | ラップ900m | float | ○ | LAP_TIME5から展開 | 秒単位 |
| 11 | ラップ1000m | float | ○ | LAP_TIME5 | 秒単位 |
| 12 | ラップ1100m | float | ○ | LAP_TIME6から展開 | 秒単位 |
| 13 | ラップ1200m | float | ○ | LAP_TIME6 | 秒単位 |
| 14 | ラップ1300m | float | ○ | LAP_TIME7から展開 | 秒単位 |
| 15 | ラップ1400m | float | ○ | LAP_TIME7 | 秒単位 |
| 16 | ラップ1500m | float | ○ | LAP_TIME8から展開 | 秒単位 |
| 17 | ラップ1600m | float | ○ | LAP_TIME8 | 秒単位 |
| 18 | ラップ1700m | float | ○ | LAP_TIME9から展開 | 秒単位 |
| 19 | ラップ1800m | float | ○ | LAP_TIME9 | 秒単位 |
| 20 | ラップ1900m | float | ○ | LAP_TIME10から展開 | 秒単位 |
| 21 | ラップ2000m | float | ○ | LAP_TIME10 | 秒単位 |
| 22 | ラップ2100m | float | ○ | LAP_TIME11から展開 | 秒単位 |
| 23 | ラップ2200m | float | ○ | LAP_TIME11 | 秒単位 |
| 24 | ラップ2300m | float | ○ | LAP_TIME12から展開 | 秒単位 |
| 25 | ラップ2400m | float | ○ | LAP_TIME12 | 秒単位 |
| 26 | ラップ2500m | float | ○ | LAP_TIME13から展開 | 秒単位 |
| 27 | ラップ2600m | float | ○ | LAP_TIME13 | 秒単位 |
| 28 | ラップ2700m | float | ○ | LAP_TIME14から展開 | 秒単位 |
| 29 | ラップ2800m | float | ○ | LAP_TIME14 | 秒単位 |
| 30 | ラップ2900m | float | ○ | LAP_TIME15から展開 | 秒単位 |
| 31 | ラップ3000m | float | ○ | LAP_TIME15 | 秒単位 |
| 32 | ラップ3100m | float | ○ | LAP_TIME16から展開 | 秒単位 |
| 33 | ラップ3200m | float | ○ | LAP_TIME16 | 秒単位 |
| 34 | ラップ3300m | float | ○ | LAP_TIME17から展開 | 秒単位 |
| 35 | ラップ3400m | float | ○ | LAP_TIME17 | 秒単位 |
| 36 | ラップ3500m | float | ○ | LAP_TIME18から展開 | 秒単位 |
| 37 | ラップ3600m | float | ○ | LAP_TIME18 | 秒単位 |
| 38 | ラップ3700m | float | ○ | LAP_TIME19から展開 | 秒単位 |
| 39 | ラップ3800m | float | ○ | LAP_TIME19 | 秒単位 |
| 40 | ラップ3900m | float | ○ | LAP_TIME20から展開 | 秒単位 |
| 41 | ラップ4000m | float | ○ | LAP_TIME20 | 秒単位 |
| 42 | ラップ4100m | float | ○ | LAP_TIME21から展開 | 秒単位 |
| 43 | ラップ4200m | float | ○ | LAP_TIME21 | 秒単位 |
| 44 | ラップ4300m | float | ○ | LAP_TIME22から展開 | 秒単位 |
| 45 | ラップ4400m | float | ○ | LAP_TIME22 | 秒単位 |
| 46 | ラップ4500m | float | ○ | LAP_TIME23から展開 | 秒単位 |
| 47 | ラップ4600m | float | ○ | LAP_TIME23 | 秒単位 |
| 48 | ラップ4700m | float | ○ | LAP_TIME24から展開 | 秒単位 |
| 49 | ラップ4800m | float | ○ | LAP_TIME24 | 秒単位 |
| 50 | ラップ4900m | float | ○ | LAP_TIME25から展開 | 秒単位 |
| 51 | ラップ5000m | float | ○ | LAP_TIME25 | 秒単位 |
| 52 | 障害マイルタイム | str | × | SHOGAI_MILE_TIME | |
| 53 | 前3ハロン | float | ○ | ZENHAN_3F | 秒単位。0.1秒単位から変換 |
| 54 | 前4ハロン | float | × | ZENHAN_4F | 秒単位。0.1秒単位から変換 |
| 55 | 後3ハロン | float | ○ | KOHAN_3F | 秒単位。0.1秒単位から変換 |
| 56 | 後4ハロン | float | × | KOHAN_4F | 秒単位。0.1秒単位から変換 |
| 57 | 1コーナー | str | ○ | CORNER1 | コーナー位置 |
| 58 | 1コーナー周回数 | int | × | SHUKAISU1 | |
| 59 | 1コーナー通過順 | str | ○ | KAKU_TSUKA_JUNI1 | 馬番の通過順文字列 |
| 60 | 2コーナー | str | ○ | CORNER2 | |
| 61 | 2コーナー周回数 | int | × | SHUKAISU2 | |
| 62 | 2コーナー通過順 | str | ○ | KAKU_TSUKA_JUNI2 | |
| 63 | 3コーナー | str | ○ | CORNER3 | |
| 64 | 3コーナー周回数 | int | × | SHUKAISU3 | |
| 65 | 3コーナー通過順 | str | ○ | KAKU_TSUKA_JUNI3 | |
| 66 | 4コーナー | str | ○ | CORNER4 | |
| 67 | 4コーナー周回数 | int | × | SHUKAISU4 | |
| 68 | 4コーナー通過順 | str | ○ | KAKU_TSUKA_JUNI4 | |
| 69 | レコード更新区分 | str | × | RECORD_KOSHIN_KUBUN | |

#### ラップタイムの格納ルール

- 100m刻みでカラムを用意する（100m〜5000mの50カラム）
- 距離が200mで割り切れるレース: 200m刻みのデータが入り、奇数カラム（100m, 300m, ...）はNaN
- 距離が200mで割り切れないレース: 先頭区間のみ100m、以降200m刻み
- レース距離を超えるカラムはNaN
- mykeibadbは1ハロン(200m)刻みで最大25個。100m刻みへの展開はProvider側で実施

#### コーナー通過順の文字列フォーマット

```
"8-3-2-(1,17)(5,14)(7,4,15)(10,13)9,6(11,12)-16-18"
```

- `()`: 集団（同位置の馬群）
- `-`: 馬間の小差
- `=`: 馬間の大差
- `,`: 馬番の区切り（集団内）
- `*`: 先頭集団の先頭馬（mykeibadbのみ）

#### NaN条件

| カラム | NaN条件 |
|--------|---------|
| 各ラップタイム | レース距離を超える場合 / 距離200m倍数のレースで奇数カラム |
| 前3ハロン | レース未実施 |
| 後3ハロン | レース未実施 |
| 1〜4コーナー通過順 | 距離が短く該当コーナーがないレース |

---

### 3. 馬毎レース情報

UMAGOTO_RACE_JOHOテーブル全体に対応する。行数は出走頭数（出馬表取得時）または全頭（結果取得時）。

対応元:
- mykeibadb: `UMAGOTO_RACE_JOHO`
- scraping: `EntryPageScraper.get_entry()` / `ResultPageScraper.get_result()` / `PastPerformancesScraper.get_past_performances()`

| # | カラム名 | 型 | scraping | mykeibadb元カラム | 備考 |
|---|----------|------|----------|-------------------|------|
| 1 | レースコード | str | ○ | RACE_CODE | |
| 2 | 開催年 | str | ○ | KAISAI_NEN | |
| 3 | 開催月日 | str | ○ | KAISAI_GAPPI | |
| 4 | 競馬場 | str | ○ | KEIBAJO_CODE→競馬場名 | コード変換後 |
| 5 | 開催回 | int | ○ | KAISAI_KAIJI | 第N回 |
| 6 | 開催日目 | int | ○ | KAISAI_NICHIJI | N日目 |
| 7 | レース番号 | int | ○ | RACE_BANGO | |
| 8 | 枠番 | int | ○ | WAKUBAN | |
| 9 | 馬番 | int | ○ | UMABAN | |
| 10 | 血統登録番号 | str | ○ | KETTO_TOROKU_BANGO | 馬ID |
| 11 | 馬名 | str | △ | BAMEI | △=get_entry/get_resultのみ対応（get_past_performancesは取得不可）|
| 12 | 馬記号 | str | × | UMAKIGO_CODE→馬記号名 | コード変換後 |
| 13 | 性別コード | str | △ | SEIBETSU_CODE | "1"=牡,"2"=牝,"3"=セン。コードで保持。△=get_entry/get_resultのみ対応（get_past_performancesは取得不可）|
| 14 | 品種 | str | × | HINSHU_CODE→品種名 | "サラブレッド"等。コード変換後 |
| 15 | 毛色 | str | × | MOSHOKU_CODE→毛色名 | "鹿毛","栗毛"等。コード変換後 |
| 16 | 馬齢 | int | △ | BAREI | △=get_entry/get_resultのみ対応（get_past_performancesは取得不可）|
| 17 | 所属コード | str | △ | TOZAI_SHOZOKU_CODE | "1"=関東,"2"=関西,"3"=地方招待,"4"=外国招待。コードで保持。△=get_entry/get_resultのみ対応（get_past_performancesは取得不可）|
| 18 | 調教師コード | str | △ | CHOKYOSHI_CODE | JRA調教師コード。△=get_entry/get_resultのみ対応（get_past_performancesは取得不可）|
| 19 | 調教師名略称 | str | △ | CHOKYOSHIMEI_RYAKUSHO | △=get_entry/get_resultのみ対応（get_past_performancesは取得不可）|
| 20 | 馬主コード | str | × | BANUSHI_CODE | |
| 21 | 馬主名 | str | × | BANUSHIMEI_HOJINKAKU_NASHI | |
| 22 | 服色標示 | str | × | FUKUSHOKU_HYOJI | |
| 23 | 負担重量 | float | ○ | FUTAN_JURYO | 0.1kg単位→kg単位に変換 |
| 24 | 変更前負担重量 | float | × | HENKOMAE_FUTAN_JURYO | 0.1kg単位→kg単位に変換 |
| 25 | ブリンカー使用区分 | str | × | BLINKER_SHIYO_KUBUN | |
| 26 | 騎手コード | str | ○ | KISHU_CODE | JRA騎手コード |
| 27 | 変更前騎手コード | str | × | HENKOMAE_KISHU_CODE | |
| 28 | 騎手名略称 | str | ○ | KISHUMEI_RYAKUSHO | |
| 29 | 変更前騎手名略称 | str | × | HENKOMAE_KISHUMEI_RYAKUSHO | |
| 30 | 騎手見習コード | str | × | KISHU_MINARAI_CODE | |
| 31 | 変更前騎手見習コード | str | × | HENKOMAE_KISHU_MINARAI_CODE | |
| 32 | 馬体重 | int | ○ | BATAIJU | kg単位 |
| 33 | 増減符号 | str | ○ | ZOGEN_FUGO | "+","-"," " |
| 34 | 増減差 | int | ○ | ZOGEN_SA | |
| 35 | 異常区分 | str | ○ | IJO_KUBUN_CODE→異常区分名 | コード変換後。異常区分対応表参照 |
| 36 | 入線順位 | int | × | NYUSEN_JUNI | |
| 37 | 確定着順 | int | ○ | KAKUTEI_CHAKUJUN | 降着反映 |
| 38 | 同着区分 | str | × | DOCHAKU_KUBUN | |
| 39 | 同着頭数 | int | × | DOCHAKU_TOSU | |
| 40 | 走破タイム | str | ○ | SOHA_TIME | "M:SS.S"形式。mykeibadbは"MSSS"から変換 |
| 41 | 着差コード1 | str | ○ | CHAKUSA_CODE1 | "K__","_12","_34"等の着差コード。コードで保持 |
| 42 | 着差コード2 | str | × | CHAKUSA_CODE2 | 着差コードで保持 |
| 43 | 着差コード3 | str | × | CHAKUSA_CODE3 | 着差コードで保持 |
| 44 | 1コーナー順位 | int | ○ | CORNER1_JUNI | |
| 45 | 2コーナー順位 | int | ○ | CORNER2_JUNI | |
| 46 | 3コーナー順位 | int | ○ | CORNER3_JUNI | |
| 47 | 4コーナー順位 | int | ○ | CORNER4_JUNI | |
| 48 | 単勝オッズ | float | ○ | TANSHO_ODDS | 0.1倍単位→倍単位に変換 |
| 49 | 単勝人気順 | int | ○ | TANSHO_NINKIJUN | |
| 50 | 獲得本賞金 | int | ○ | KAKUTOKU_HONSHOKIN | 百円単位 |
| 51 | 獲得付加賞金 | int | × | KAKUTOKU_FUKASHOKIN | 百円単位 |
| 52 | 後4ハロン | float | × | KOHAN_4F | 秒単位。0.1秒単位から変換 |
| 53 | 後3ハロン | float | ○ | KOHAN_3F | 秒単位。0.1秒単位から変換 |
| 54 | 相手1血統登録番号 | str | × | AITE1_KETTO_TOROKU_BANGO | |
| 55 | 相手1馬名 | str | ○ | AITE1_BAMEI | PastPerformancesScraperのみ対応 |
| 56 | 相手2血統登録番号 | str | × | AITE2_KETTO_TOROKU_BANGO | |
| 57 | 相手2馬名 | str | × | AITE2_BAMEI | |
| 58 | 相手3血統登録番号 | str | × | AITE3_KETTO_TOROKU_BANGO | |
| 59 | 相手3馬名 | str | × | AITE3_BAMEI | |
| 60 | タイム差 | float | ○ | TIME_SA | 秒単位 |
| 61 | レコード更新区分 | str | × | RECORD_KOSHIN_KUBUN | |
| 62 | マイニング区分 | str | × | MINING_KUBUN | |
| 63 | マイニング予想走破タイム | str | × | MINING_YOSO_SOHA_TIME | |
| 64 | マイニング予想誤差プラス | str | × | MINING_YOSO_GOSA_PLUS | |
| 65 | マイニング予想誤差マイナス | str | × | MINING_YOSO_GOSA_MINUS | |
| 66 | マイニング予想順位 | int | × | MINING_YOSO_JUNI | |
| 67 | 脚質判定 | str | × | KYAKUSHITSU_HANTEI | "逃","先","差","追" |

#### 異常区分の対応表

| 統一値 | scraping元 | mykeibadb ijo_kubun_code |
|--------|-----------|---------------------------|
| ""（空文字） | 着順が数値かつ着差が降着でない | "0"（正常） |
| "出走取消" | 着順テキストが"取消" | "1"（出走取消） |
| "発走除外" | （区別不可→"競走除外"として扱う） | "2"（発走除外） |
| "競走除外" | 着順テキストが"除外" | "3"（競走除外） |
| "競走中止" | 着順テキストが"中止" | "4"（競走中止） |
| "失格" | 着順テキストが"失格" | "5"（失格） |
| "落馬再騎乗" | （scrapingでは区別不可→空文字として扱う） | "6"（落馬再騎乗） |
| "降着" | 着差テキストが"N位降着" | "7"（降着） |

**注意**:
- scrapingでは着順テキストから「取消・除外・中止・失格」を検出し、着差テキストから「N位降着」を検出する
- mykeibadbではijo_kubun_codeから判定する
- scrapingで取得できる「除外」は発走除外（code=2）と競走除外（code=3）を区別できないため、"競走除外"として扱う（発走除外はmykeibadb使用時のみ正確に判別可能）
- scrapingで取得できる「落馬再騎乗」（code=6）は着順が正常扱いのため区別できず、空文字として扱う（落馬再騎乗はmykeibadb使用時のみ正確に判別可能）

#### NaN条件

| カラム | NaN条件 |
|--------|---------|
| 枠番 | scraping: 出走確定前 |
| 馬番 | scraping: 出走確定前 |
| 確定着順 | 競走中止/出走取消/競走除外/失格 |
| 走破タイム | 競走中止/出走取消/競走除外 |
| 着差コード1 | 競走中止/出走取消/競走除外/失格 |
| 単勝オッズ | 出走取消/競走除外 |
| 単勝人気順 | 出走取消/競走除外 |
| 後3ハロン | 競走中止/出走取消/競走除外 |
| 1〜3コーナー順位 | 該当コーナーがない場合/競走中止/出走取消/競走除外 |
| 4コーナー順位 | 競走中止/出走取消/競走除外 |
| 馬体重 | 出走取消/競走除外/発表前 |
| 増減差 | 出走取消/競走除外/前計不/発表前 |
| 獲得本賞金 | 出走取消/競走除外/失格 |
| 騎手コード | scraping: 騎手未確定時 |

---

### 4. 払戻情報

HARAIMODOSHIテーブル全体に対応する。1行のDataFrame。全券種を1レコードで返す。

対応元:
- mykeibadb: `HARAIMODOSHI`
- scraping: `ResultPageScraper.get_win_payoff()` + `get_show_payoff()` + `get_bracket_payoff()` + `get_quinella_payoff()` + `get_quinella_place_payoff()` + `get_exacta_payoff()` + `get_trio_payoff()` + `get_trifecta_payoff()`

| # | カラム名 | 型 | scraping | mykeibadb元カラム | 備考 |
|---|----------|------|----------|-------------------|------|
| 1 | レースコード | str | ○ | RACE_CODE | |
| 2 | 開催年 | str | ○ | KAISAI_NEN | |
| 3 | 開催月日 | str | ○ | KAISAI_GAPPI | |
| 4 | 競馬場 | str | ○ | KEIBAJO_CODE→競馬場名 | コード変換後 |
| 5 | 開催回 | int | ○ | KAISAI_KAIJI | |
| 6 | 開催日目 | int | ○ | KAISAI_NICHIJI | |
| 7 | レース番号 | int | ○ | RACE_BANGO | |
| 8 | 登録頭数 | int | × | TOROKU_TOSU | |
| 9 | 出走頭数 | int | × | SHUSSO_TOSU | |
| 10 | 不成立フラグ単勝 | str | × | FUSEIRITSU_FLAG_TANSHO | |
| 11 | 不成立フラグ複勝 | str | × | FUSEIRITSU_FLAG_FUKUSHO | |
| 12 | 不成立フラグ枠連 | str | × | FUSEIRITSU_FLAG_WAKUREN | |
| 13 | 不成立フラグ馬連 | str | × | FUSEIRITSU_FLAG_UMAREN | |
| 14 | 不成立フラグワイド | str | × | FUSEIRITSU_FLAG_WIDE | |
| 15 | 不成立フラグ馬単 | str | × | FUSEIRITSU_FLAG_UMATAN | |
| 16 | 不成立フラグ3連複 | str | × | FUSEIRITSU_FLAG_SANRENPUKU | |
| 17 | 不成立フラグ3連単 | str | × | FUSEIRITSU_FLAG_SANRENTAN | |
| 18 | 特払フラグ単勝 | str | × | TOKUBARAI_FLAG_TANSHO | |
| 19 | 特払フラグ複勝 | str | × | TOKUBARAI_FLAG_FUKUSHO | |
| 20 | 特払フラグ枠連 | str | × | TOKUBARAI_FLAG_WAKUREN | |
| 21 | 特払フラグ馬連 | str | × | TOKUBARAI_FLAG_UMAREN | |
| 22 | 特払フラグワイド | str | × | TOKUBARAI_FLAG_WIDE | |
| 23 | 特払フラグ馬単 | str | × | TOKUBARAI_FLAG_UMATAN | |
| 24 | 特払フラグ3連複 | str | × | TOKUBARAI_FLAG_SANRENPUKU | |
| 25 | 特払フラグ3連単 | str | × | TOKUBARAI_FLAG_SANRENTAN | |
| 26 | 返還フラグ単勝 | str | × | HENKAN_FLAG_TANSHO | |
| 27 | 返還フラグ複勝 | str | × | HENKAN_FLAG_FUKUSHO | |
| 28 | 返還フラグ枠連 | str | × | HENKAN_FLAG_WAKUREN | |
| 29 | 返還フラグ馬連 | str | × | HENKAN_FLAG_UMAREN | |
| 30 | 返還フラグワイド | str | × | HENKAN_FLAG_WIDE | |
| 31 | 返還フラグ馬単 | str | × | HENKAN_FLAG_UMATAN | |
| 32 | 返還フラグ3連複 | str | × | HENKAN_FLAG_SANRENPUKU | |
| 33 | 返還フラグ3連単 | str | × | HENKAN_FLAG_SANRENTAN | |
| 34〜61 | 返還馬番情報1〜28 | str | × | HENKAN_UMABAN_JOHO1〜28 | |
| 62〜69 | 返還枠番情報1〜8 | str | × | HENKAN_WAKUBAN_JOHO1〜8 | |
| 70〜77 | 返還同枠情報1〜8 | str | × | HENKAN_DOWAKU_JOHO1〜8 | |
| 78 | 単勝1馬番 | int | ○ | TANSHO1_UMABAN | |
| 79 | 単勝1払戻金 | int | ○ | TANSHO1_HARAIMODOSHIKIN | |
| 80 | 単勝1人気順 | int | ○ | TANSHO1_NINKIJUN | |
| 81 | 単勝2馬番 | int | ○ | TANSHO2_UMABAN | 同着時 |
| 82 | 単勝2払戻金 | int | ○ | TANSHO2_HARAIMODOSHIKIN | |
| 83 | 単勝2人気順 | int | ○ | TANSHO2_NINKIJUN | |
| 84 | 単勝3馬番 | int | ○ | TANSHO3_UMABAN | 同着時 |
| 85 | 単勝3払戻金 | int | ○ | TANSHO3_HARAIMODOSHIKIN | |
| 86 | 単勝3人気順 | int | ○ | TANSHO3_NINKIJUN | |
| 87 | 複勝1馬番 | int | ○ | FUKUSHO1_UMABAN | |
| 88 | 複勝1払戻金 | int | ○ | FUKUSHO1_HARAIMODOSHIKIN | |
| 89 | 複勝1人気順 | int | ○ | FUKUSHO1_NINKIJUN | |
| 90 | 複勝2馬番 | int | ○ | FUKUSHO2_UMABAN | |
| 91 | 複勝2払戻金 | int | ○ | FUKUSHO2_HARAIMODOSHIKIN | |
| 92 | 複勝2人気順 | int | ○ | FUKUSHO2_NINKIJUN | |
| 93 | 複勝3馬番 | int | ○ | FUKUSHO3_UMABAN | |
| 94 | 複勝3払戻金 | int | ○ | FUKUSHO3_HARAIMODOSHIKIN | |
| 95 | 複勝3人気順 | int | ○ | FUKUSHO3_NINKIJUN | |
| 96 | 複勝4馬番 | int | ○ | FUKUSHO4_UMABAN | 同着時 |
| 97 | 複勝4払戻金 | int | ○ | FUKUSHO4_HARAIMODOSHIKIN | |
| 98 | 複勝4人気順 | int | ○ | FUKUSHO4_NINKIJUN | |
| 99 | 複勝5馬番 | int | ○ | FUKUSHO5_UMABAN | 同着時 |
| 100 | 複勝5払戻金 | int | ○ | FUKUSHO5_HARAIMODOSHIKIN | |
| 101 | 複勝5人気順 | int | ○ | FUKUSHO5_NINKIJUN | |
| 102 | 枠連1組番1 | int | ○ | WAKUREN1_KUMIBAN1 | |
| 103 | 枠連1組番2 | int | ○ | WAKUREN1_KUMIBAN2 | |
| 104 | 枠連1払戻金 | int | ○ | WAKUREN1_HARAIMODOSHIKIN | |
| 105 | 枠連1人気順 | int | ○ | WAKUREN1_NINKIJUN | |
| 106 | 枠連2組番1 | int | ○ | WAKUREN2_KUMIBAN1 | 同着時 |
| 107 | 枠連2組番2 | int | ○ | WAKUREN2_KUMIBAN2 | |
| 108 | 枠連2払戻金 | int | ○ | WAKUREN2_HARAIMODOSHIKIN | |
| 109 | 枠連2人気順 | int | ○ | WAKUREN2_NINKIJUN | |
| 110 | 枠連3組番1 | int | ○ | WAKUREN3_KUMIBAN1 | 同着時 |
| 111 | 枠連3組番2 | int | ○ | WAKUREN3_KUMIBAN2 | |
| 112 | 枠連3払戻金 | int | ○ | WAKUREN3_HARAIMODOSHIKIN | |
| 113 | 枠連3人気順 | int | ○ | WAKUREN3_NINKIJUN | |
| 114 | 馬連1組番1 | int | ○ | UMAREN1_KUMIBAN1 | |
| 115 | 馬連1組番2 | int | ○ | UMAREN1_KUMIBAN2 | |
| 116 | 馬連1払戻金 | int | ○ | UMAREN1_HARAIMODOSHIKIN | |
| 117 | 馬連1人気順 | int | ○ | UMAREN1_NINKIJUN | |
| 118 | 馬連2組番1 | int | ○ | UMAREN2_KUMIBAN1 | 同着時 |
| 119 | 馬連2組番2 | int | ○ | UMAREN2_KUMIBAN2 | |
| 120 | 馬連2払戻金 | int | ○ | UMAREN2_HARAIMODOSHIKIN | |
| 121 | 馬連2人気順 | int | ○ | UMAREN2_NINKIJUN | |
| 122 | 馬連3組番1 | int | ○ | UMAREN3_KUMIBAN1 | 同着時 |
| 123 | 馬連3組番2 | int | ○ | UMAREN3_KUMIBAN2 | |
| 124 | 馬連3払戻金 | int | ○ | UMAREN3_HARAIMODOSHIKIN | |
| 125 | 馬連3人気順 | int | ○ | UMAREN3_NINKIJUN | |
| 126 | ワイド1組番1 | int | ○ | WIDE1_KUMIBAN1 | |
| 127 | ワイド1組番2 | int | ○ | WIDE1_KUMIBAN2 | |
| 128 | ワイド1払戻金 | int | ○ | WIDE1_HARAIMODOSHIKIN | |
| 129 | ワイド1人気順 | int | ○ | WIDE1_NINKIJUN | |
| 130 | ワイド2組番1 | int | ○ | WIDE2_KUMIBAN1 | |
| 131 | ワイド2組番2 | int | ○ | WIDE2_KUMIBAN2 | |
| 132 | ワイド2払戻金 | int | ○ | WIDE2_HARAIMODOSHIKIN | |
| 133 | ワイド2人気順 | int | ○ | WIDE2_NINKIJUN | |
| 134 | ワイド3組番1 | int | ○ | WIDE3_KUMIBAN1 | |
| 135 | ワイド3組番2 | int | ○ | WIDE3_KUMIBAN2 | |
| 136 | ワイド3払戻金 | int | ○ | WIDE3_HARAIMODOSHIKIN | |
| 137 | ワイド3人気順 | int | ○ | WIDE3_NINKIJUN | |
| 138 | ワイド4組番1 | int | ○ | WIDE4_KUMIBAN1 | 同着時 |
| 139 | ワイド4組番2 | int | ○ | WIDE4_KUMIBAN2 | |
| 140 | ワイド4払戻金 | int | ○ | WIDE4_HARAIMODOSHIKIN | |
| 141 | ワイド4人気順 | int | ○ | WIDE4_NINKIJUN | |
| 142 | ワイド5組番1 | int | ○ | WIDE5_KUMIBAN1 | 同着時 |
| 143 | ワイド5組番2 | int | ○ | WIDE5_KUMIBAN2 | |
| 144 | ワイド5払戻金 | int | ○ | WIDE5_HARAIMODOSHIKIN | |
| 145 | ワイド5人気順 | int | ○ | WIDE5_NINKIJUN | |
| 146 | ワイド6組番1 | int | ○ | WIDE6_KUMIBAN1 | 同着時 |
| 147 | ワイド6組番2 | int | ○ | WIDE6_KUMIBAN2 | |
| 148 | ワイド6払戻金 | int | ○ | WIDE6_HARAIMODOSHIKIN | |
| 149 | ワイド6人気順 | int | ○ | WIDE6_NINKIJUN | |
| 150 | ワイド7組番1 | int | ○ | WIDE7_KUMIBAN1 | 同着時 |
| 151 | ワイド7組番2 | int | ○ | WIDE7_KUMIBAN2 | |
| 152 | ワイド7払戻金 | int | ○ | WIDE7_HARAIMODOSHIKIN | |
| 153 | ワイド7人気順 | int | ○ | WIDE7_NINKIJUN | |
| 154 | 馬単1組番1 | int | ○ | UMATAN1_KUMIBAN1 | 1着馬番 |
| 155 | 馬単1組番2 | int | ○ | UMATAN1_KUMIBAN2 | 2着馬番 |
| 156 | 馬単1払戻金 | int | ○ | UMATAN1_HARAIMODOSHIKIN | |
| 157 | 馬単1人気順 | int | ○ | UMATAN1_NINKIJUN | |
| 158 | 馬単2組番1 | int | ○ | UMATAN2_KUMIBAN1 | 同着時 |
| 159 | 馬単2組番2 | int | ○ | UMATAN2_KUMIBAN2 | |
| 160 | 馬単2払戻金 | int | ○ | UMATAN2_HARAIMODOSHIKIN | |
| 161 | 馬単2人気順 | int | ○ | UMATAN2_NINKIJUN | |
| 162 | 馬単3組番1 | int | ○ | UMATAN3_KUMIBAN1 | 同着時 |
| 163 | 馬単3組番2 | int | ○ | UMATAN3_KUMIBAN2 | |
| 164 | 馬単3払戻金 | int | ○ | UMATAN3_HARAIMODOSHIKIN | |
| 165 | 馬単3人気順 | int | ○ | UMATAN3_NINKIJUN | |
| 166 | 馬単4組番1 | int | ○ | UMATAN4_KUMIBAN1 | 同着時 |
| 167 | 馬単4組番2 | int | ○ | UMATAN4_KUMIBAN2 | |
| 168 | 馬単4払戻金 | int | ○ | UMATAN4_HARAIMODOSHIKIN | |
| 169 | 馬単4人気順 | int | ○ | UMATAN4_NINKIJUN | |
| 170 | 馬単5組番1 | int | ○ | UMATAN5_KUMIBAN1 | 同着時 |
| 171 | 馬単5組番2 | int | ○ | UMATAN5_KUMIBAN2 | |
| 172 | 馬単5払戻金 | int | ○ | UMATAN5_HARAIMODOSHIKIN | |
| 173 | 馬単5人気順 | int | ○ | UMATAN5_NINKIJUN | |
| 174 | 馬単6組番1 | int | ○ | UMATAN6_KUMIBAN1 | 同着時 |
| 175 | 馬単6組番2 | int | ○ | UMATAN6_KUMIBAN2 | |
| 176 | 馬単6払戻金 | int | ○ | UMATAN6_HARAIMODOSHIKIN | |
| 177 | 馬単6人気順 | int | ○ | UMATAN6_NINKIJUN | |
| 178 | 3連複1組番1 | int | ○ | SANRENPUKU1_KUMIBAN1 | |
| 179 | 3連複1組番2 | int | ○ | SANRENPUKU1_KUMIBAN2 | |
| 180 | 3連複1組番3 | int | ○ | SANRENPUKU1_KUMIBAN3 | |
| 181 | 3連複1払戻金 | int | ○ | SANRENPUKU1_HARAIMODOSHIKIN | |
| 182 | 3連複1人気順 | int | ○ | SANRENPUKU1_NINKIJUN | |
| 183 | 3連複2組番1 | int | ○ | SANRENPUKU2_KUMIBAN1 | 同着時 |
| 184 | 3連複2組番2 | int | ○ | SANRENPUKU2_KUMIBAN2 | |
| 185 | 3連複2組番3 | int | ○ | SANRENPUKU2_KUMIBAN3 | |
| 186 | 3連複2払戻金 | int | ○ | SANRENPUKU2_HARAIMODOSHIKIN | |
| 187 | 3連複2人気順 | int | ○ | SANRENPUKU2_NINKIJUN | |
| 188 | 3連複3組番1 | int | ○ | SANRENPUKU3_KUMIBAN1 | 同着時 |
| 189 | 3連複3組番2 | int | ○ | SANRENPUKU3_KUMIBAN2 | |
| 190 | 3連複3組番3 | int | ○ | SANRENPUKU3_KUMIBAN3 | |
| 191 | 3連複3払戻金 | int | ○ | SANRENPUKU3_HARAIMODOSHIKIN | |
| 192 | 3連複3人気順 | int | ○ | SANRENPUKU3_NINKIJUN | |
| 193 | 3連単1組番1 | int | ○ | SANRENTAN1_KUMIBAN1 | 1着馬番 |
| 194 | 3連単1組番2 | int | ○ | SANRENTAN1_KUMIBAN2 | 2着馬番 |
| 195 | 3連単1組番3 | int | ○ | SANRENTAN1_KUMIBAN3 | 3着馬番 |
| 196 | 3連単1払戻金 | int | ○ | SANRENTAN1_HARAIMODOSHIKIN | |
| 197 | 3連単1人気順 | int | ○ | SANRENTAN1_NINKIJUN | |
| 198 | 3連単2組番1 | int | ○ | SANRENTAN2_KUMIBAN1 | 同着時 |
| 199 | 3連単2組番2 | int | ○ | SANRENTAN2_KUMIBAN2 | |
| 200 | 3連単2組番3 | int | ○ | SANRENTAN2_KUMIBAN3 | |
| 201 | 3連単2払戻金 | int | ○ | SANRENTAN2_HARAIMODOSHIKIN | |
| 202 | 3連単2人気順 | int | ○ | SANRENTAN2_NINKIJUN | |
| 203 | 3連単3組番1 | int | ○ | SANRENTAN3_KUMIBAN1 | 同着時 |
| 204 | 3連単3組番2 | int | ○ | SANRENTAN3_KUMIBAN2 | |
| 205 | 3連単3組番3 | int | ○ | SANRENTAN3_KUMIBAN3 | |
| 206 | 3連単3払戻金 | int | ○ | SANRENTAN3_HARAIMODOSHIKIN | |
| 207 | 3連単3人気順 | int | ○ | SANRENTAN3_NINKIJUN | |
| 208 | 3連単4組番1 | int | ○ | SANRENTAN4_KUMIBAN1 | 同着時 |
| 209 | 3連単4組番2 | int | ○ | SANRENTAN4_KUMIBAN2 | |
| 210 | 3連単4組番3 | int | ○ | SANRENTAN4_KUMIBAN3 | |
| 211 | 3連単4払戻金 | int | ○ | SANRENTAN4_HARAIMODOSHIKIN | |
| 212 | 3連単4人気順 | int | ○ | SANRENTAN4_NINKIJUN | |
| 213 | 3連単5組番1 | int | ○ | SANRENTAN5_KUMIBAN1 | 同着時 |
| 214 | 3連単5組番2 | int | ○ | SANRENTAN5_KUMIBAN2 | |
| 215 | 3連単5組番3 | int | ○ | SANRENTAN5_KUMIBAN3 | |
| 216 | 3連単5払戻金 | int | ○ | SANRENTAN5_HARAIMODOSHIKIN | |
| 217 | 3連単5人気順 | int | ○ | SANRENTAN5_NINKIJUN | |
| 218 | 3連単6組番1 | int | ○ | SANRENTAN6_KUMIBAN1 | 同着時 |
| 219 | 3連単6組番2 | int | ○ | SANRENTAN6_KUMIBAN2 | |
| 220 | 3連単6組番3 | int | ○ | SANRENTAN6_KUMIBAN3 | |
| 221 | 3連単6払戻金 | int | ○ | SANRENTAN6_HARAIMODOSHIKIN | |
| 222 | 3連単6人気順 | int | ○ | SANRENTAN6_NINKIJUN | |

#### NaN条件

全券種共通で、同着がない場合は2組目以降がNaN。各券種の不成立時は該当券種の全カラムがNaN。

---

### 5. 単複オッズ情報

ODDS1_TANSHO（単勝オッズ）とODDS1_FUKUSHO（複勝オッズ）を合体したテーブル。重複するヘッダカラム（レースコード〜レース番号）は1セットにまとめる。行数は最大28行（馬番数分）。

対応元:
- mykeibadb: `ODDS1_TANSHO` + `ODDS1_FUKUSHO`
- scraping: `scrape_odds_from_jra()` / `scrape_odds_from_netkeiba()`

| # | カラム名 | 型 | scraping | mykeibadb元カラム | 備考 |
|---|----------|------|----------|-------------------|------|
| 1 | レースコード | str | ○ | RACE_CODE | |
| 2 | 開催年 | str | ○ | KAISAI_NEN | |
| 3 | 開催月日 | str | ○ | KAISAI_GAPPI | |
| 4 | 競馬場 | str | ○ | KEIBAJO_CODE→競馬場名 | コード変換後 |
| 5 | 開催回 | int | ○ | KAISAI_KAIJI | |
| 6 | 開催日目 | int | ○ | KAISAI_NICHIJI | |
| 7 | レース番号 | int | ○ | RACE_BANGO | |
| 8 | 馬番 | int | ○ | UMABAN | |
| 9 | 単勝オッズ | float | ○ | ODDS | 0.1倍単位→倍単位に変換 |
| 10 | 単勝人気 | int | ○ | NINKI（単勝） | |
| 11 | 複勝最低オッズ | float | ○ | ODDS_SAITEI | 0.1倍単位→倍単位に変換 |
| 12 | 複勝最高オッズ | float | ○ | ODDS_SAIKOU | 0.1倍単位→倍単位に変換 |
| 13 | 複勝人気 | int | ○ | NINKI（複勝） | |

#### NaN条件

| カラム | NaN条件 |
|--------|---------|
| 全カラム（馬番以外） | 出走取消の馬 |

---

### 6. 開催スケジュール情報

KAISAI_SCHEDULEテーブル全体に対応する。行数は開催場数。

対応元:
- mykeibadb: `KAISAI_SCHEDULE`
- scraping: `RaceScheduleScraper.get_race_schedule()`

| # | カラム名 | 型 | scraping | mykeibadb元カラム | 備考 |
|---|----------|------|----------|-------------------|------|
| 1 | 開催コード | str | ○ | KAISAI_CODE | |
| 2 | 開催年 | str | ○ | KAISAI_NEN | |
| 3 | 開催月日 | str | ○ | KAISAI_GAPPI | |
| 4 | 競馬場 | str | ○ | KEIBAJO_CODE→競馬場名 | コード変換後 |
| 5 | 開催回 | int | ○ | KAISAI_KAIJI | |
| 6 | 開催日目 | int | ○ | KAISAI_NICHIJI | |
| 7 | 曜日 | str | × | YOBI_CODE→曜日名 | コード変換後 |
| 8 | 重賞1特別競走番号 | int | × | JUSHO1_TOKUBETSU_KYOSO_BANGO | |
| 9 | 重賞1競走名本題 | str | × | JUSHO1_KYOSOMEI_HONDAI | |
| 10 | 重賞1競走名略称10文字 | str | × | JUSHO1_KYOSOMEI_RYAKUSHO_10 | |
| 11 | 重賞1競走名略称6文字 | str | × | JUSHO1_KYOSOMEI_RYAKUSHO_6 | |
| 12 | 重賞1競走名略称3文字 | str | × | JUSHO1_KYOSOMEI_RYAKUSHO_3 | |
| 13 | 重賞1重賞回次 | int | × | JUSHO1_JUSHO_KAIJI | |
| 14 | 重賞1グレード | str | × | JUSHO1_GRADE_CODE→グレード名 | コード変換後 |
| 15 | 重賞1競走種別 | str | × | JUSHO1_KYOSO_SHUBETSU_CODE→競走種別名 | コード変換後 |
| 16 | 重賞1競走記号 | str | × | JUSHO1_KYOSO_KIGO_CODE→競走記号名 | コード変換後 |
| 17 | 重賞1重量種別 | str | × | JUSHO1_JURYO_SHUBETSU_CODE→重量種別名 | コード変換後 |
| 18 | 重賞1距離 | int | × | JUSHO1_KYORI | |
| 19 | 重賞1トラック | str | × | JUSHO1_TRACK_CODE→トラック名 | コード変換後 |
| 20 | 重賞2特別競走番号 | int | × | JUSHO2_TOKUBETSU_KYOSO_BANGO | |
| 21 | 重賞2競走名本題 | str | × | JUSHO2_KYOSOMEI_HONDAI | |
| 22 | 重賞2競走名略称10文字 | str | × | JUSHO2_KYOSOMEI_RYAKUSHO_10 | |
| 23 | 重賞2競走名略称6文字 | str | × | JUSHO2_KYOSOMEI_RYAKUSHO_6 | |
| 24 | 重賞2競走名略称3文字 | str | × | JUSHO2_KYOSOMEI_RYAKUSHO_3 | |
| 25 | 重賞2重賞回次 | int | × | JUSHO2_JUSHO_KAIJI | |
| 26 | 重賞2グレード | str | × | JUSHO2_GRADE_CODE→グレード名 | コード変換後 |
| 27 | 重賞2競走種別 | str | × | JUSHO2_KYOSO_SHUBETSU_CODE→競走種別名 | コード変換後 |
| 28 | 重賞2競走記号 | str | × | JUSHO2_KYOSO_KIGO_CODE→競走記号名 | コード変換後 |
| 29 | 重賞2重量種別 | str | × | JUSHO2_JURYO_SHUBETSU_CODE→重量種別名 | コード変換後 |
| 30 | 重賞2距離 | int | × | JUSHO2_KYORI | |
| 31 | 重賞2トラック | str | × | JUSHO2_TRACK_CODE→トラック名 | コード変換後 |
| 32 | 重賞3特別競走番号 | int | × | JUSHO3_TOKUBETSU_KYOSO_BANGO | |
| 33 | 重賞3競走名本題 | str | × | JUSHO3_KYOSOMEI_HONDAI | |
| 34 | 重賞3競走名略称10文字 | str | × | JUSHO3_KYOSOMEI_RYAKUSHO_10 | |
| 35 | 重賞3競走名略称6文字 | str | × | JUSHO3_KYOSOMEI_RYAKUSHO_6 | |
| 36 | 重賞3競走名略称3文字 | str | × | JUSHO3_KYOSOMEI_RYAKUSHO_3 | |
| 37 | 重賞3重賞回次 | int | × | JUSHO3_JUSHO_KAIJI | |
| 38 | 重賞3グレード | str | × | JUSHO3_GRADE_CODE→グレード名 | コード変換後 |
| 39 | 重賞3競走種別 | str | × | JUSHO3_KYOSO_SHUBETSU_CODE→競走種別名 | コード変換後 |
| 40 | 重賞3競走記号 | str | × | JUSHO3_KYOSO_KIGO_CODE→競走記号名 | コード変換後 |
| 41 | 重賞3重量種別 | str | × | JUSHO3_JURYO_SHUBETSU_CODE→重量種別名 | コード変換後 |
| 42 | 重賞3距離 | int | × | JUSHO3_KYORI | |
| 43 | 重賞3トラック | str | × | JUSHO3_TRACK_CODE→トラック名 | コード変換後 |

#### 備考

- scrapingの`get_race_schedule()`は指定した日付のすべてのレース情報（各レースごと）を取得するが、KAISAI_SCHEDULEはその日に行われる競馬場と開催情報のみを格納する
- scrapingからKAISAI_SCHEDULEに変換する場合は、レース情報を開催場単位に集約する必要がある

---

## 値の変換ルール

### mykeibadb → 統一スキーマへの主要変換

| 項目 | mykeibadb生値 | 変換後 | 変換方法 |
|------|-------------|--------|---------|
| 発走時刻 | `"1540"` | `"15:40"` | `hhmm` → `HH:MM` |
| 走破タイム | `"2315"` | `"2:31.5"` | `MSSS` → `M:SS.S` |
| 負担重量 | `"560"` | `56.0` | 0.1kg単位 → kg単位 |
| 単勝オッズ | `"0038"` | `3.8` | 0.1倍単位 → 倍単位 |
| 後3F/後4F | `"346"` | `34.6` | 0.1秒単位 → 秒単位 |
| ラップタイム | `"122"` | `12.2` | 0.1秒単位 → 秒単位 |
| 馬体重増減 | 符号`"+"`+差`"002"` | `2` | 符号＋差 → 符号付き整数 |
| 天候 | コード→名称変換済 | そのまま | `convert_codes=True` 使用 |
| 馬場状態 | コード→名称変換済 | そのまま | `convert_codes=True` 使用 |
| 性別コード | SEIBETSU_CODEをそのまま保持 | 性別文字列→コード変換 | 内部ではコードで保持し表示時に名称変換 |
| 所属コード | TOZAI_SHOZOKU_CODEをそのまま保持 | 所属文字列→コード変換 | 内部ではコードで保持し表示時に名称変換 |
| 異常区分 | コード→名称変換済 | そのまま | `convert_codes=True` 使用 |

### scraping → 統一スキーマへの変換

scrapingの出力はmykeibadbとカラム構成が異なるため、以下の変換が必要：

- scrapingで取得できないカラムはNaN埋め
- カラム名の対応（scraping日本語名 → 統一スキーマ日本語名）
  - 例：「馬ID」→「血統登録番号」、「厩舎」→「調教師名略称」、「騎手ID」→「騎手コード」
- **レースコード：引数として受け取った16桁レースコードをそのまま使用する。scrapingへの呼び出し時は16桁→12桁に変換して渡し、取得結果には引数の16桁を格納する**
- 異常区分：scrapingの「除外」は発走除外と競走除外を区別できないため、一律「競走除外」（=mykeibadbの"3"相当）として扱う
- 増減：scrapingの増減（符号付き整数）を増減符号と増減差に分離
