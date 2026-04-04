# Provider出力差異レポート

scraping○カラムのみを比較対象とし、既知差異と未知差異を分離。

テスト対象: レース27件, 馬10件

検出差異総数: **879件**

- 未知差異（要対応）: **5件**
- 既知差異（KNOWN_DIFF_*で許容済み）: 874件

---

## 1. 未知差異（要対応）

統合テストで検証すべき差異。KNOWN_DIFF_*に追加するか、converter修正が必要。

- 値不一致: 0件
- NaN不一致: 0件
- 行数不一致: 5件
- 変換エラー: 0件

### 1c. 行数不一致

| テストケース | メソッド | scraping行数 | mykeibadb行数 |
|-------------|----------|-------------|---------------|
| ビコーズウイキャン(2021103695) | get_past_performances | 30 | 5 |
| カランダガン(2021190001) | get_past_performances | 14 | 1 |
| タイトルホルダー(2018103559) | get_past_performances | 19 | 18 |
| フォーエバーヤング(2021105727) | get_past_performances | 14 | 1 |
| クリノガイディー(2016103690) | get_past_performances | 33 | 31 |

---

## 2. 既知差異サマリー（KNOWN_DIFF_*で許容済み）

これらはデータソースの仕様差異であり、テストでは許容される。

| カラム | メソッド | 差異種別 | 影響ケース数 | 発生行数 | scraping例 | mykeibadb例 |
|--------|----------|----------|-------------|----------|------------|-------------|
| 1コーナー | get_race_result_info | NaN不一致 | 27 | 27 | NaN | '1' |
| 1コーナー通過順 | get_race_result_info | NaN不一致 | 13 | 13 | NaN | '(*3,13)1,11(9,5)(2,14)-1 |
| 2コーナー | get_race_result_info | NaN不一致 | 27 | 27 | NaN | '2' |
| 2コーナー通過順 | get_race_result_info | NaN不一致 | 11 | 11 | NaN | '(*3,13)1,11,9,5,14(8,2,6 |
| 2コーナー通過順 | get_race_result_info | 値不一致 | 2 | 2 | '5,1(2,4)3' | '(*5,1)-4,2,3             |
| 3コーナー | get_race_result_info | NaN不一致 | 27 | 27 | NaN | '3' |
| 3コーナー通過順 | get_race_result_info | NaN不一致 | 1 | 1 | NaN | '                         |
| 3コーナー通過順 | get_race_result_info | 値不一致 | 12 | 12 | '(*3,13)1,11(9,5)(2,14)-1 | '                         |
| 3連複1人気順 | get_payoff | 値不一致 | 1 | 1 | 33 | 32 |
| 4コーナー | get_race_result_info | NaN不一致 | 27 | 27 | NaN | '4' |
| 4コーナー通過順 | get_race_result_info | NaN不一致 | 1 | 1 | NaN | '                         |
| 4コーナー通過順 | get_race_result_info | 値不一致 | 12 | 12 | '(*3,13)1,11,9,5,14(8,2,6 | '                         |
| グレード | get_race_info | 値不一致 | 21 | 21 | 'G1' | 'GI' |
| コース区分 | get_race_info | 値不一致 | 6 | 6 | 'C外' | 'C ' |
| タイム差 | get_past_performances | NaN不一致 | 5 | 15 | NaN | 0.4000 |
| ダート馬場状態 | get_race_info | NaN不一致 | 24 | 24 | NaN | '' |
| トラック | get_race_info | 値不一致 | 27 | 27 | '芝右' | '芝・右' |
| ワイド1人気順 | get_payoff | 値不一致 | 4 | 4 | 5 | 6 |
| ワイド2人気順 | get_payoff | 値不一致 | 8 | 8 | 4 | 3 |
| ワイド3人気順 | get_payoff | 値不一致 | 5 | 5 | 30 | 28 |
| 出走頭数 | get_payoff | NaN不一致 | 27 | 27 | NaN | 16 |
| 出走頭数 | get_race_info | 値不一致 | 2 | 2 | 18 | 16 |
| 単勝1人気順 | get_payoff | 値不一致 | 1 | 1 | 2 | 1 |
| 単勝人気順 | get_past_performances | NaN不一致 | 2 | 6 | NaN | 1 |
| 性別コード | get_past_performances | NaN不一致 | 5 | 15 | NaN | '1' |
| 所属コード | get_past_performances | NaN不一致 | 5 | 15 | NaN | '2' |
| 曜日 | get_race_info | 値不一致 | 2 | 2 | '日' | '祝' |
| 本賞金1着 | get_race_info | 値不一致 | 1 | 1 | 970000 | 680000 |
| 本賞金2着 | get_race_info | 値不一致 | 1 | 1 | 390000 | 680000 |
| 本賞金3着 | get_race_info | 値不一致 | 2 | 2 | 1250000 | 1300000 |
| 本賞金4着 | get_race_info | 値不一致 | 1 | 1 | 11000 | 12540 |
| 本賞金5着 | get_race_info | 値不一致 | 1 | 1 | 7600 | 12540 |
| 枠連1組番1 | get_payoff | NaN不一致 | 1 | 1 | NaN | 0 |
| 枠連1組番2 | get_payoff | NaN不一致 | 1 | 1 | NaN | 0 |
| 獲得本賞金 | get_past_performances | NaN不一致 | 4 | 7 | NaN | 0 |
| 獲得本賞金 | get_past_performances | 値不一致 | 4 | 8 | 109000 | 107000 |
| 獲得本賞金 | get_result | 値不一致 | 3 | 6 | 1250000 | 1300000 |
| 着差コード1 | get_past_performances | NaN不一致 | 4 | 8 | -0.2000 | NaN |
| 着差コード1 | get_past_performances | 値不一致 | 5 | 7 | 0.4000 | '134' |
| 着差コード1 | get_result | NaN不一致 | 1 | 1 | NaN | 'H__' |
| 着差コード1 | get_result | 値不一致 | 2 | 3 | 'K__' | 'D__' |
| 確定着順 | get_past_performances | NaN不一致 | 3 | 9 | NaN | 2 |
| 競走名本題 | get_race_info | 値不一致 | 20 | 20 | 'ジャパンC' | 'ジャパンカップ' |
| 競走条件名称 | get_race_info | 値不一致 | 27 | 27 | 'オープン' | '\u3000\u3000\u3000\u3000 |
| 競走種別 | get_race_info | 値不一致 | 1 | 1 | '障害３歳以上' | 'サラ障害３歳以上' |
| 競走記号 | get_race_info | 値不一致 | 20 | 20 | '(国際)(指)' | '(国際)(指定)' |
| 芝馬場状態 | get_race_info | NaN不一致 | 3 | 3 | NaN | '' |
| 芝馬場状態 | get_race_info | 値不一致 | 5 | 5 | '稍' | '稍重' |
| 複勝1人気順 | get_payoff | 値不一致 | 5 | 5 | 2 | 1 |
| 複勝2人気順 | get_payoff | 値不一致 | 3 | 3 | 1 | 2 |
| 複勝3人気順 | get_payoff | 値不一致 | 1 | 1 | 3 | 2 |
| 複勝3馬番 | get_payoff | NaN不一致 | 1 | 1 | NaN | 0 |
| 調教師コード | get_past_performances | NaN不一致 | 5 | 15 | NaN | '01159' |
| 調教師名略称 | get_entry | 値不一致 | 27 | 83 | '和田郎' | '和田正一' |
| 調教師名略称 | get_past_performances | NaN不一致 | 5 | 15 | NaN | '高柳大輔' |
| 調教師名略称 | get_result | 値不一致 | 27 | 83 | '和田郎' | '和田正一' |
| 馬単1人気順 | get_payoff | 値不一致 | 1 | 1 | 10 | 9 |
| 馬名 | get_past_performances | NaN不一致 | 5 | 15 | NaN | 'ミュージアムマイル' |
| 馬齢 | get_past_performances | NaN不一致 | 5 | 15 | NaN | 2 |
| 騎手名略称 | get_entry | 値不一致 | 27 | 82 | '福永' | '福永祐一' |
| 騎手名略称 | get_result | 値不一致 | 27 | 83 | '福永' | '福永祐一' |