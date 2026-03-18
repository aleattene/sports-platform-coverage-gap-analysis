"""Tests for platform step_02 — aggregation and CSV export functions."""

import csv
from pathlib import Path
from typing import Any

import pytest
from src.data_collection.sport_platforms.example_platform.step_02_build_analysis_dataset import (
    aggregate_by_province,
    aggregate_by_sport_and_province,
    build_csv,
)


class TestAggregateByProvince:

    def test_counts_entities_per_province(self, sample_platform_items: list[dict[str, Any]]) -> None:
        rows = aggregate_by_province(sample_platform_items)
        province_map = {r["province_abbr"]: r["platform_entities"] for r in rows}
        assert province_map["RM"] == 2  # calcio + nuoto
        assert province_map["MI"] == 1

    def test_resolves_region_name(self, sample_platform_items: list[dict[str, Any]]) -> None:
        rows = aggregate_by_province(sample_platform_items)
        rm_row = next(r for r in rows if r["province_abbr"] == "RM")
        assert rm_row["region_code"] == "LAZ"
        assert rm_row["region_name"] == "Lazio"

    def test_sorted_by_province(self, sample_platform_items: list[dict[str, Any]]) -> None:
        rows = aggregate_by_province(sample_platform_items)
        provinces = [r["province_abbr"] for r in rows]
        assert provinces == sorted(provinces)

    def test_empty_input(self) -> None:
        assert aggregate_by_province([]) == []

    def test_skips_items_without_province(self) -> None:
        items = [{"sport": ["calcio"], "province_abbr": "", "region_code": "LAZ"}]
        assert aggregate_by_province(items) == []

    def test_unknown_region_code_used_as_name(self) -> None:
        items = [{"sport": ["calcio"], "province_abbr": "XX", "region_code": "ZZZ"}]
        rows = aggregate_by_province(items)
        assert rows[0]["region_name"] == "ZZZ"  # fallback to code itself


class TestAggregateBySportAndProvince:

    def test_counts_per_sport_province_pair(self, sample_platform_items: list[dict[str, Any]]) -> None:
        rows = aggregate_by_sport_and_province(sample_platform_items)
        lookup = {(r["sport_key"], r["province_abbr"]): r["platform_entities"] for r in rows}
        assert lookup[("calcio", "RM")] == 1
        assert lookup[("nuoto", "RM")] == 1
        assert lookup[("calcio", "MI")] == 1
        assert lookup[("basket", "MI")] == 1

    def test_multi_sport_entity_counted_per_sport(self) -> None:
        items = [{"sport": ["calcio", "nuoto"], "province_abbr": "TO", "region_code": "PIE"}]
        rows = aggregate_by_sport_and_province(items)
        assert len(rows) == 2
        sports = {r["sport_key"] for r in rows}
        assert sports == {"calcio", "nuoto"}

    def test_sorted_by_sport_then_province(self, sample_platform_items: list[dict[str, Any]]) -> None:
        rows = aggregate_by_sport_and_province(sample_platform_items)
        keys = [(r["sport_key"], r["province_abbr"]) for r in rows]
        assert keys == sorted(keys)

    def test_empty_input(self) -> None:
        assert aggregate_by_sport_and_province([]) == []

    def test_skips_items_without_sport(self) -> None:
        items = [{"sport": [], "province_abbr": "RM", "region_code": "LAZ"}]
        assert aggregate_by_sport_and_province(items) == []


class TestBuildCsv:

    def test_writes_valid_csv(self, tmp_path: Path) -> None:
        rows = [
            {"region_code": "LAZ", "province_abbr": "RM", "count": 10},
            {"region_code": "LOM", "province_abbr": "MI", "count": 20},
        ]
        output = tmp_path / "test.csv"
        build_csv(rows, ["region_code", "province_abbr", "count"], output)

        with output.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            csv_rows = list(reader)

        assert len(csv_rows) == 2
        assert csv_rows[0]["province_abbr"] == "RM"
        assert csv_rows[1]["count"] == "20"  # CSV values are strings

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        output = tmp_path / "nested" / "deep" / "test.csv"
        build_csv([{"a": 1}], ["a"], output)
        assert output.exists()

    def test_empty_rows_produces_header_only(self, tmp_path: Path) -> None:
        output = tmp_path / "empty.csv"
        build_csv([], ["col_a", "col_b"], output)
        content = output.read_text(encoding="utf-8")
        assert "col_a,col_b" in content
        lines = content.strip().split("\n")
        assert len(lines) == 1  # header only
