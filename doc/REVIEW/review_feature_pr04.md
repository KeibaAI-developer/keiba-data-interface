# レビュー: feature/pr04

## 概要

- **対象**: develop → feature/pr04
- **レビュー日**: 2026-03-22
- **レビュー対象ファイル数**: 6ファイル

## 指摘事項

### 1. 16桁レースコードと開催日の不整合をそのまま返してしまう

| 項目 | 内容 |
|------|------|
| 重要度 | Critical |
| 場所 | `keiba_data_interface/providers/scraping_provider.py` L53-L54 |

**指摘内容**

`get_race_info()` は引数の16桁レースコードを主キーとして返す一方で、`開催年` と `開催月日` はスクレイピング結果の `日付` から再計算しています。
ScrapingProvider が内部で使う12桁IDは月日を含まないため、呼び出し側が月日だけ誤った16桁コードを渡しても同じページを取得できてしまいます。その結果、返却DataFrame内で `レースコード` と `開催年` / `開催月日` が矛盾した状態になります。

実際に `_convert_race_info()` に `race_code="2025010106021211"` と `日付=2025-05-02` の生データを渡すと、`レースコード=2025010106021211` かつ `開催月日=0502` の不整合な行が再現しました。統一スキーマのキー整合性が壊れるため、後続の join や期間フィルタで誤動作します。

**修正案**

`開催年` と `開催月日` は `race_code` から導出するか、少なくともスクレイピング結果の `日付` と `race_code` の月日が一致することを検証し、不一致なら例外にしてください。

```python
# 修正前
date_val = row["日付"]
converted["開催年"] = str(date_val.year)
converted["開催月日"] = f"{date_val.month:02d}{date_val.day:02d}"

# 修正後の方向性
parts = extract_race_code_parts(race_code)
converted["開催年"] = parts["年"]
converted["開催月日"] = parts["月日"]
```

### 2. 外部依存をモックしても provider を import した時点で `scraping` が必須になる

| 項目 | 内容 |
|------|------|
| 重要度 | Warning |
| 場所 | `keiba_data_interface/providers/scraping_provider.py` L4 |

**指摘内容**

`EntryPageScraper` をモジュールトップレベルで import しているため、単体テストが `patch()` で外部依存を差し替える前に `scraping` パッケージの import が走ります。今回追加された provider テストも `ScrapingProvider` の import 時点で `scraping` に依存するため、外部依存をモック化するという計画に反してテスト実行環境に keiba-scraping の実体が必要です。

実際にローカル環境で `pytest test/unit/providers/scraping_provider/test_get_race_info.py -q` を実行すると、`test/unit/providers/scraping_provider/conftest.py` の import で `ModuleNotFoundError: No module named 'scraping'` が発生しました。

**修正案**

`scraping` の import は `get_race_info()` 内に遅延させるか、コンストラクタでスクレイパークラスを注入できるようにして、単体テストが外部ライブラリ未導入でも成立するようにしてください。

```python
# 修正前
from scraping import EntryPageScraper

def get_race_info(self, race_code: str) -> pd.DataFrame:
    scraper = EntryPageScraper(race_id)

# 修正後の方向性
def get_race_info(self, race_code: str) -> pd.DataFrame:
    from scraping import EntryPageScraper
    scraper = EntryPageScraper(race_id)
```

## まとめ

| 重要度 | 件数 |
|--------|------|
| Critical | 1 |
| Warning | 1 |
| Suggestion | 0 |

---

## 再レビュー（2026-03-22）

前回の指摘に対する修正状況:

- [x] 指摘1: `開催年` と `開催月日` を `race_code` から導出するようになり、返却DataFrame内でキー項目が食い違う問題は解消された
- [x] 指摘2: `scraping` の import が `__init__()` 内に遅延され、テストでは `scraper_class` 注入で外部依存なしに `ScrapingProvider` を構築できるようになった
- [x] 追加確認: privateメソッドの `_convert_race_info()` が publicメソッド群の下に移動され、`python-coding-rule` の public/private 配置順序にも適合した

### 追加指摘

追加の問題は見つかりませんでした。

残るテスト上のリスクとしては、月日が食い違う `race_code` を渡したときに `race_code` 側の値が優先されることを明示する回帰テストはまだありません。ただし、前回の Critical / Warning はいずれも解消済みです。