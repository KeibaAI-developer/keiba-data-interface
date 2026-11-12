"""race_code_to_race_id関数のテスト."""

import pytest
from keiba_domain import KeibaDomainError

from keiba_data_interface.utils.race_code import race_code_to_race_id


# 正常系
@pytest.mark.parametrize(
    "race_code, expected",
    [
        ("2025050206021211", "202506021211"),
        ("2024123105010101", "202405010101"),
        ("2023010110030812", "202310030812"),
    ],
)
def test_race_code_to_race_id_normal(race_code: str, expected: str) -> None:
    """16桁レースコードから12桁レースIDに正しく変換できる."""
    assert race_code_to_race_id(race_code) == expected


# 準正常系
@pytest.mark.parametrize(
    "race_code",
    [
        "202505020602121",
        "20250502060212111",
        "202505020602121a",
        "202505020602121１",
        "",
    ],
)
def test_race_code_to_race_id_with_invalid_race_code_raises_error(race_code: str) -> None:
    """半角数字16桁でないレースコードでKeibaDomainErrorが発生する."""
    with pytest.raises(KeibaDomainError):
        race_code_to_race_id(race_code)
