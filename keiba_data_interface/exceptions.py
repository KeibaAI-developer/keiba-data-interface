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


class DataNotFoundError(KeibaDataInterfaceError):
    """要求されたデータがプロバイダーから取得できない場合の例外."""

    pass


class UnsupportedOperationError(KeibaDataInterfaceError):
    """使用中のプロバイダーがその操作（一括取得・票数など）に対応していない場合の例外.

    データが存在しない（DataNotFoundError）のとは区別し、呼び出し側が「対応していない
    操作は省く」判断だけをできるようにする。
    """

    pass
