"""取得済みデータのキャッシュ.

同じキーのデータを繰り返し取得しないようメモリへ保持する。取得そのものより、
1件あたりの変換処理（型変換・コード変換）が積み上がるコストが大きいため、
取得結果の再利用が効く。
"""

import datetime
import logging
from collections import OrderedDict
from typing import Any

# 保持する最大エントリ数の既定値。
# データ種別ごとに独立して数える。学習データ生成では5年分（約15,000レース）を
# 連続処理するため、上限がないとメモリを圧迫する
DEFAULT_MAX_ENTRIES = 20000


class DataCache:
    """取得済みデータをデータ種別・キーごとに保持するキャッシュ.

    保持する最大エントリ数を超えた分は、最も古く使われたものから捨てる（LRU）。
    上限はデータ種別ごとに独立して数える。

    複数の`DataInterface`インスタンスで共有できるよう、`DataInterface`の外へ
    置ける設計にしている。学習データ生成では対象レース群をまたいでキャッシュを
    効かせたいため。

    未来レース（結果が確定していないレース）は保持しない。単勝オッズは発走直前まで
    変動し、予測実行では直前に取得し直す必要があるため、キャッシュした値を返すと
    古いオッズで予測することになる。

    Attributes:
        max_entries (int): データ種別ごとに保持する最大エントリ数
    """

    def __init__(
        self,
        max_entries: int = DEFAULT_MAX_ENTRIES,
        logger: logging.Logger | None = None,
    ) -> None:
        """キャッシュを初期化する.

        Args:
            max_entries (int): データ種別ごとに保持する最大エントリ数
            logger (logging.Logger | None): ロガーインスタンス
        """
        self._logger = logger or logging.getLogger(__name__)
        self.max_entries = max_entries
        self._entries: dict[str, OrderedDict[str, Any]] = {}

    def get(self, kind: str, key: str) -> Any | None:  # noqa: ANN401
        """キャッシュから値を取り出す.

        Args:
            kind (str): データ種別（取得メソッド名など）
            key (str): キー（レースコード・馬IDなど）

        Returns:
            Any | None: 保持している値。無い場合はNone
        """
        entries = self._entries.get(kind)
        if entries is None or key not in entries:
            self._logger.debug("キャッシュにありません: 種別=%s, キー=%s", kind, key)
            return None

        entries.move_to_end(key)
        self._logger.debug("キャッシュから取得しました: 種別=%s, キー=%s", kind, key)
        return entries[key]

    def set(self, kind: str, key: str, value: Any) -> None:  # noqa: ANN401
        """キャッシュへ値を格納する.

        未来レースのレースコードは格納しない。

        Args:
            kind (str): データ種別（取得メソッド名など）
            key (str): キー（レースコード・馬IDなど）
            value (Any): 保持する値
        """
        if is_future_race_code(key):
            self._logger.debug("未来レースのためキャッシュしません: キー=%s", key)
            return

        entries = self._entries.setdefault(kind, OrderedDict())
        entries[key] = value
        entries.move_to_end(key)
        while len(entries) > self.max_entries:
            oldest_key, _ = entries.popitem(last=False)
            self._logger.debug(
                "上限を超えたため最も古いものを捨てました: 種別=%s, キー=%s", kind, oldest_key
            )

    def clear(self) -> None:
        """キャッシュを空にする."""
        self._entries.clear()
        self._logger.debug("キャッシュを空にしました")


def is_future_race_code(key: str) -> bool:
    """キーが未来レース（当日を含む）のレースコードかどうかを返す.

    16桁レースコードの先頭8桁を開催日として現在日と比較する。当日を未来として
    扱うのは、発走前のレースを過去として扱わないため（`race-data`の`RaceData`と
    同じ判定）。

    レースコード以外のキー（馬IDなど）は未来レースではないためFalseを返す。

    Args:
        key (str): キー

    Returns:
        bool: 当日を含む未来のレースコードならTrue
    """
    if len(key) != 16 or not key.isdigit():
        return False
    return key[:8] >= datetime.date.today().strftime("%Y%m%d")
