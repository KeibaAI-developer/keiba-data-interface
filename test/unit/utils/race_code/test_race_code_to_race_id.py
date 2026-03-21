"""race_code_to_race_id関数のテスト."""

import pytest

from keiba_data_interface.utils.race_code import RaceCodeError, race_code_to_race_id


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
def test_race_code_to_race_id_invalid_length_short() -> None:
    """15桁のレースコードでRaceCodeErrorが発生する."""
    with pytest.raises(RaceCodeError, match="16桁"):
        race_code_to_race_id("202505020602121")


def test_race_code_to_race_id_invalid_length_long() -> None:
    """17桁のレースコードでRaceCodeErrorが発生する."""
    with pytest.raises(RaceCodeError, match="16桁"):
        race_code_to_race_id("20250502060212111")


def test_race_code_to_race_id_non_digit() -> None:
    """数値以外の文字を含むレースコードでRaceCodeErrorが発生する."""
    with pytest.raises(RaceCodeError, match="数字のみ"):
        race_code_to_race_id("202505020602121a")


def test_race_code_to_race_id_empty() -> None:
    """空文字列でRaceCodeErrorが発生する."""
    with pytest.raises(RaceCodeError, match="16桁"):
        race_code_to_race_id("")
