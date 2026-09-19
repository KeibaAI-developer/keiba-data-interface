"""scraping で取得できないカラムの定数を検証するテスト."""

from pathlib import Path

import pytest

from keiba_data_interface.schema.columns import (
    RACE_BASIC_INFO_COLUMNS,
    RACE_BASIC_INFO_COLUMNS_UNAVAILABLE_IN_SCRAPING,
    RACE_INFO_BY_HORSE_COLUMNS,
    RACE_INFO_BY_HORSE_COLUMNS_UNAVAILABLE_IN_SCRAPING,
)

_DOC_DIR = Path(__file__).resolve().parents[4] / "doc" / "SCHEMA"


def _unavailable_columns_in_doc(doc_name: str) -> set[str]:
    """SCHEMA ドキュメントのカラム表で scraping が × のカラム名を集める."""
    columns: set[str] = set()
    in_table = False
    for line in (_DOC_DIR / doc_name).read_text(encoding="utf-8").splitlines():
        if line.startswith("| カラム名 | 型 | scraping"):
            in_table = True
            continue
        if not in_table:
            continue
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4 or cells[0].startswith("---"):
            continue
        if cells[2] == "×":
            columns.add(cells[0])
    return columns


# 正常系
@pytest.mark.parametrize(
    ("constant", "doc_name"),
    [
        (RACE_BASIC_INFO_COLUMNS_UNAVAILABLE_IN_SCRAPING, "RACE_BASIC_INFO.md"),
        (RACE_INFO_BY_HORSE_COLUMNS_UNAVAILABLE_IN_SCRAPING, "RACE_INFO_BY_HORSE.md"),
    ],
)
def test_matches_schema_doc(constant: frozenset[str], doc_name: str) -> None:
    """定数がドキュメントの表で scraping が × のカラム集合と一致する."""
    assert set(constant) == _unavailable_columns_in_doc(doc_name)


@pytest.mark.parametrize(
    ("constant", "columns"),
    [
        (RACE_BASIC_INFO_COLUMNS_UNAVAILABLE_IN_SCRAPING, RACE_BASIC_INFO_COLUMNS),
        (RACE_INFO_BY_HORSE_COLUMNS_UNAVAILABLE_IN_SCRAPING, RACE_INFO_BY_HORSE_COLUMNS),
    ],
)
def test_subset_of_schema_columns(constant: frozenset[str], columns: list[str]) -> None:
    """定数のカラムはすべてスキーマのカラムに含まれる."""
    assert constant <= set(columns)
