"""Integration tests for registry step_04 — build analysis dataset.

Step_04 is pure data processing (no Playwright): it loads entity_counts.json
from step_03 output, validates rows, removes duplicates, and exports
analysis-ready JSON, CSV, and quality checks.
"""

import csv
import json
from pathlib import Path
from typing import Any

import pytest

import src.data_collection.sport_registries.example_registry.step_04_build_analysis_dataset as step_04_mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seed_entity_counts(processed_dir: Path, items: list[dict[str, Any]]) -> None:
    """Write a valid entity_counts.json fixture into processed_dir."""
    processed_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "dimension": "province_entity_counts",
        "count": len(items),
        "items": items,
    }
    (processed_dir / "entity_counts.json").write_text(
        json.dumps(payload), encoding="utf-8",
    )


def _sample_items() -> list[dict[str, Any]]:
    return [
        {
            "region_id": "12",
            "region_name": "Lazio",
            "province_id": "058",
            "province_name": "Roma",
            "province_abbr": "RM",
            "entities_total": 1500,
        },
        {
            "region_id": "03",
            "region_name": "Lombardia",
            "province_id": "015",
            "province_name": "Milano",
            "province_abbr": "MI",
            "entities_total": 2000,
        },
    ]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_dirs(tmp_path: Path) -> dict[str, Path]:
    processed_dir = tmp_path / "processed"
    quality_dir = tmp_path / "quality"
    processed_dir.mkdir()
    quality_dir.mkdir()
    return {"processed": processed_dir, "quality": quality_dir}


@pytest.fixture
def _patch_dirs(monkeypatch: pytest.MonkeyPatch, tmp_dirs: dict[str, Path]) -> dict[str, Path]:
    monkeypatch.setattr(step_04_mod, "COUNTS_INPUT_FILE", tmp_dirs["processed"] / "entity_counts.json")
    monkeypatch.setattr(step_04_mod, "ANALYSIS_JSON_FILE", tmp_dirs["processed"] / "registry_entity_counts_by_province.json")
    monkeypatch.setattr(step_04_mod, "ANALYSIS_CSV_FILE", tmp_dirs["processed"] / "registry_entity_counts_by_province.csv")
    monkeypatch.setattr(step_04_mod, "ANALYSIS_QUALITY_FILE", tmp_dirs["quality"] / "registry_entity_counts_by_province_checks.json")
    monkeypatch.setattr(step_04_mod, "PROJECT_ROOT", tmp_dirs["processed"].parent)
    return tmp_dirs


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestStep04Main:

    def test_produces_analysis_json(
        self,
        _patch_dirs: dict[str, Path],
    ) -> None:
        items = _sample_items()
        _seed_entity_counts(_patch_dirs["processed"], items)

        step_04_mod.main()

        json_file = _patch_dirs["processed"] / "registry_entity_counts_by_province.json"
        assert json_file.exists()
        data = json.loads(json_file.read_text(encoding="utf-8"))
        assert data["dimension"] == "province_entity_counts"
        assert data["count"] == 2
        assert len(data["items"]) == 2

    def test_produces_analysis_csv(
        self,
        _patch_dirs: dict[str, Path],
    ) -> None:
        items = _sample_items()
        _seed_entity_counts(_patch_dirs["processed"], items)

        step_04_mod.main()

        csv_file = _patch_dirs["processed"] / "registry_entity_counts_by_province.csv"
        assert csv_file.exists()
        with csv_file.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["province_name"] == "Roma"
        assert rows[0]["entities_total"] == "1500"

    def test_produces_quality_report(
        self,
        _patch_dirs: dict[str, Path],
    ) -> None:
        items = _sample_items()
        _seed_entity_counts(_patch_dirs["processed"], items)

        step_04_mod.main()

        quality_file = _patch_dirs["quality"] / "registry_entity_counts_by_province_checks.json"
        assert quality_file.exists()
        data = json.loads(quality_file.read_text(encoding="utf-8"))
        assert data["count"] == 2
        assert all(r["status"] == "ok" for r in data["items"])

    def test_deduplicates_rows(
        self,
        _patch_dirs: dict[str, Path],
    ) -> None:
        items = _sample_items()
        items.append(items[0].copy())  # duplicate Roma row
        _seed_entity_counts(_patch_dirs["processed"], items)

        step_04_mod.main()

        json_file = _patch_dirs["processed"] / "registry_entity_counts_by_province.json"
        data = json.loads(json_file.read_text(encoding="utf-8"))
        assert data["count"] == 2  # duplicate removed

        quality_file = _patch_dirs["quality"] / "registry_entity_counts_by_province_checks.json"
        quality = json.loads(quality_file.read_text(encoding="utf-8"))
        statuses = [r["status"] for r in quality["items"]]
        assert statuses.count("duplicate_skipped") == 1

    def test_skips_invalid_rows(
        self,
        _patch_dirs: dict[str, Path],
    ) -> None:
        items: list[Any] = _sample_items()
        items.append("not_a_dict")  # invalid row
        _seed_entity_counts(_patch_dirs["processed"], items)

        step_04_mod.main()

        json_file = _patch_dirs["processed"] / "registry_entity_counts_by_province.json"
        data = json.loads(json_file.read_text(encoding="utf-8"))
        assert data["count"] == 2  # invalid row excluded

        quality_file = _patch_dirs["quality"] / "registry_entity_counts_by_province_checks.json"
        quality = json.loads(quality_file.read_text(encoding="utf-8"))
        statuses = [r["status"] for r in quality["items"]]
        assert "invalid_row" in statuses

    def test_raises_on_invalid_file_format(
        self,
        _patch_dirs: dict[str, Path],
    ) -> None:
        """entity_counts.json as a list instead of dict."""
        input_file = _patch_dirs["processed"] / "entity_counts.json"
        input_file.write_text(json.dumps([1, 2, 3]), encoding="utf-8")

        with pytest.raises(ValueError, match="expected dictionary"):
            step_04_mod.main()

    def test_raises_on_invalid_items_type(
        self,
        _patch_dirs: dict[str, Path],
    ) -> None:
        """items is a string instead of list."""
        input_file = _patch_dirs["processed"] / "entity_counts.json"
        input_file.write_text(
            json.dumps({"dimension": "test", "items": "not_a_list"}),
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match="expected 'items' to be a list"):
            step_04_mod.main()

    def test_empty_items_produces_empty_output(
        self,
        _patch_dirs: dict[str, Path],
    ) -> None:
        _seed_entity_counts(_patch_dirs["processed"], [])

        step_04_mod.main()

        json_file = _patch_dirs["processed"] / "registry_entity_counts_by_province.json"
        data = json.loads(json_file.read_text(encoding="utf-8"))
        assert data["count"] == 0
        assert data["items"] == []
