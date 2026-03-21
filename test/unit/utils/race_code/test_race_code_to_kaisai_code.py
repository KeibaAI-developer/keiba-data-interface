"""race_code_to_kaisai_code関数のテスト."""

import pytest

from keiba_data_interface.utils.race_code import RaceCodeError, race_code_to_kaisai_code


# 正常系
@pytest.mark.parametrize(
    "race_code, expected",
    [
        ("2025050206021211", "20250502060212"),
        ("2024123105010101", "20241231050101"),
        ("2023010110030812", "20230101100308"),
    ],
)
def test_race_code_to_kaisai_code_normal(race_code: str, expected: str) -> None:
    """16桁レースコードから14桁開催コードに正しく変換できる."""
    assert race_code_to_kaisai_code(race_code) == expected


# 準正常系
def test_race_code_to_kaisai_code_invalid_length() -> None:
    """桁数が不正な場合にRaceCodeErrorが発生する."""
    with pytest.raises(RaceCodeError, match="16桁"):
        race_code_to_kaisai_code("20250502060212")


def test_race_code_to_kaisai_code_non_digit() -> None:
    """数値以外の文字を含む場合にRaceCodeErrorが発生する."""
    with pytest.raises(RaceCodeError, match="数字のみ"):
        race_code_to_kaisai_code("abcdefghijklmnop")
