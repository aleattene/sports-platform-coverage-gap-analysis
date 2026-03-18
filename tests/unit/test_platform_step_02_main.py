"""Tests for platform step_02 main() — analysis dataset build orchestration."""

import csv
import json
from pathlib import Path
from typing import Any

import pytest


class TestStep02Main:

    def _setup_and_run(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        raw_payload: dict[str, Any],
    ) -> Path:
        """Write a raw input file, patch module paths, and run main()."""
        raw_dir = tmp_path / "raw"
        processed_dir = tmp_path / "processed"
        quality_dir = tmp_path / "quality"
        raw_dir.mkdir()
        processed_dir.mkdir()
        quality_dir.mkdir()

        raw_file = raw_dir / "platform_entities.json"
        raw_file.write_text(json.dumps(raw_payload), encoding="utf-8")

        import src.data_collection.sport_platforms.example_platform.step_02_build_analysis_dataset as mod

        monkeypatch.setattr(mod, "RAW_INPUT", raw_file)
        monkeypatch.setattr(mod, "ANALYSIS_CSV_BY_PROVINCE", processed_dir / "by_province.csv")
        monkeypatch.setattr(mod, "ANALYSIS_JSON_BY_PROVINCE", processed_dir / "by_province.json")
        monkeypatch.setattr(mod, "ANALYSIS_CSV_BY_SPORT_PROVINCE", processed_dir / "by_sport_province.csv")
        monkeypatch.setattr(mod, "QUALITY_OUTPUT", quality_dir / "checks.json")
        monkeypatch.setattr(mod, "PROJECT_ROOT", tmp_path)

        mod.main()
        return processed_dir

    def test_main_produces_province_csv(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        sample_raw_payload: dict[str, Any],
    ) -> None:
        processed_dir = self._setup_and_run(monkeypatch, tmp_path, sample_raw_payload)
        csv_file = processed_dir / "by_province.csv"
        assert csv_file.exists()

        with csv_file.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 2  # RM + MI
        provinces = {r["province_abbr"] for r in rows}
        assert provinces == {"RM", "MI"}

    def test_main_produces_province_json(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        sample_raw_payload: dict[str, Any],
    ) -> None:
        processed_dir = self._setup_and_run(monkeypatch, tmp_path, sample_raw_payload)
        json_file = processed_dir / "by_province.json"
        assert json_file.exists()

        data = json.loads(json_file.read_text(encoding="utf-8"))
        assert data["dimension"] == "platform_entity_counts_by_province"
        assert data["count"] == 2

    def test_main_produces_sport_province_csv(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        sample_raw_payload: dict[str, Any],
    ) -> None:
        processed_dir = self._setup_and_run(monkeypatch, tmp_path, sample_raw_payload)
        csv_file = processed_dir / "by_sport_province.csv"
        assert csv_file.exists()

        with csv_file.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        # calcio-MI, calcio-RM, basket-MI, nuoto-RM = 4
        assert len(rows) == 4

    def test_main_produces_quality_report(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        sample_raw_payload: dict[str, Any],
    ) -> None:
        self._setup_and_run(monkeypatch, tmp_path, sample_raw_payload)
        quality_file = tmp_path / "quality" / "checks.json"
        assert quality_file.exists()

        data = json.loads(quality_file.read_text(encoding="utf-8"))
        assert data["total_entities"] == 3
        assert data["unique_provinces"] == 2

    def test_main_raises_on_invalid_format(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        with pytest.raises(ValueError, match="expected dictionary"):
            self._setup_and_run(monkeypatch, tmp_path, [1, 2, 3])  # list instead of dict

    def test_main_raises_on_invalid_items_type(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        with pytest.raises(ValueError, match="expected 'items' to be a list"):
            self._setup_and_run(monkeypatch, tmp_path, {"items": "not a list"})
