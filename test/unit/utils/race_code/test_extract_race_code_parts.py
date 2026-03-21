"""extract_race_code_parts関数のテスト."""

import pytest

from keiba_data_interface.utils.race_code import RaceCodeError, extract_race_code_parts


# 正常系
def test_extract_race_code_parts_normal() -> None:
    """16桁レースコードから各要素を正しく抽出できる."""
    result = extract_race_code_parts("2025050206021211")
    assert result == {
        "年": "2025",
        "月日": "0502",
        "競馬場": "06",
        "回": "02",
        "日目": "12",
        "R": "11",
    }


def test_extract_race_code_parts_first_race() -> None:
    """1Rのレースコードから各要素を正しく抽出できる."""
    result = extract_race_code_parts("2024010105010101")
    assert result == {
        "年": "2024",
        "月日": "0101",
        "競馬場": "05",
        "回": "01",
        "日目": "01",
        "R": "01",
    }


def test_extract_race_code_parts_last_race() -> None:
    """12Rのレースコードから各要素を正しく抽出できる."""
    result = extract_race_code_parts("2023123110050812")
    assert result == {
        "年": "2023",
        "月日": "1231",
        "競馬場": "10",
        "回": "05",
        "日目": "08",
        "R": "12",
    }


# 準正常系
def test_extract_race_code_parts_invalid_length() -> None:
    """桁数が不正な場合にRaceCodeErrorが発生する."""
    with pytest.raises(RaceCodeError, match="16桁"):
        extract_race_code_parts("202505020602")


def test_extract_race_code_parts_non_digit() -> None:
    """数値以外の文字を含む場合にRaceCodeErrorが発生する."""
    with pytest.raises(RaceCodeError, match="数字のみ"):
        extract_race_code_parts("2025050206ab1211")
