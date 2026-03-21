"""keiba-data-interface: 競馬データ統一インターフェース.

競馬データを取得する複数のデータソース（netkeiba、JRA-VAN）を
統一的なインターフェースで扱うためのライブラリ。
"""

try:
    from importlib.metadata import PackageNotFoundError, version

    __version__ = version("keiba-data-interface")
except (PackageNotFoundError, ImportError):
    __version__ = "unknown"
