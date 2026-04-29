"""例外クラス定義.

このモジュールは、keiba-data-interfaceライブラリで使用される例外クラスを定義する。
"""


class KeibaDataInterfaceError(Exception):
    """keiba-data-interface基底例外.

    keiba-data-interfaceライブラリの全ての例外の基底クラス。
    """

    pass


class RaceCodeError(KeibaDataInterfaceError):
    """レースコード関連の例外."""

    pass
