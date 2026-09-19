"""scraping プロバイダーの単複オッズの取得元."""

from enum import StrEnum


class OddsSource(StrEnum):
    """scraping プロバイダーの単複オッズの取得元.

    Attributes:
        JRA: JRA 公式サイト（Playwright で操作する）。最新のオッズ
        NETKEIBA: netkeiba のオッズ API。発売前は 0 行
    """

    JRA = "jra"
    NETKEIBA = "netkeiba"
