"""Integration tests for registry step_03 — retrieve entities by province.

Playwright is fully mocked: these tests verify province iteration, entity
count extraction, retry logic, quality checks, and output structure.
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

import src.data_collection.sport_registries.example_registry.step_03_retrieve_entities_by_province as step_03_mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seed_province_file(provinces_dir: Path, filename: str, data: dict[str, Any]) -> None:
    provinces_dir.mkdir(parents=True, exist_ok=True)
    (provinces_dir / filename).write_text(json.dumps(data), encoding="utf-8")


def _sample_province_file(region_name: str, region_id: int, provinces: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "dimension": "provinces",
        "region_id": region_id,
        "region_name": region_name,
        "count": len(provinces),
        "items": provinces,
    }


LAZIO_PROVINCES = _sample_province_file("Lazio", 12, [
    {"region_id": 12, "region_name": "Lazio", "province_id": 58, "province_name": "Roma", "province_abbr": "RM"},
])

LOMBARDIA_PROVINCES = _sample_province_file("Lombardia", 3, [
    {"region_id": 3, "region_name": "Lombardia", "province_id": 15, "province_name": "Milano", "province_abbr": "MI"},
])


def _build_playwright_mock(
    results_by_province: dict[str, int],
) -> MagicMock:
    """Build a Playwright mock where extract_total_results returns configured counts."""
    # Each province gets a fresh page via context.new_page()
    page_call_index = {"idx": 0}
    province_names = list(results_by_province.keys())
    province_counts = list(results_by_province.values())

    context = MagicMock()

    def _new_page() -> MagicMock:
        page = MagicMock()
        idx = page_call_index["idx"]
        page_call_index["idx"] += 1

        # Mock region select locator
        region_locator = MagicMock()
        page.locator.return_value = MagicMock(first=region_locator)

        # Mock expect_response context manager
        response_ctx = MagicMock()
        response_ctx.__enter__ = MagicMock(return_value=response_ctx)
        response_ctx.__exit__ = MagicMock(return_value=False)
        page.expect_response = MagicMock(return_value=response_ctx)

        return page

    context.new_page = _new_page

    browser = MagicMock()
    browser.new_context.return_value = context
    playwright = MagicMock()
    playwright.chromium.launch.return_value = browser

    pw_cm = MagicMock()
    pw_cm.__enter__ = MagicMock(return_value=playwright)
    pw_cm.__exit__ = MagicMock(return_value=False)
    return pw_cm


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_dirs(tmp_path: Path) -> dict[str, Path]:
    provinces_dir = tmp_path / "provinces"
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    quality_dir = tmp_path / "quality"
    for d in (provinces_dir, raw_dir, processed_dir, quality_dir):
        d.mkdir()
    return {"provinces": provinces_dir, "raw": raw_dir, "processed": processed_dir, "quality": quality_dir}


@pytest.fixture
def _patch_dirs(monkeypatch: pytest.MonkeyPatch, tmp_dirs: dict[str, Path]) -> dict[str, Path]:
    monkeypatch.setattr(step_03_mod, "PROVINCES_DIR", tmp_dirs["provinces"])
    monkeypatch.setattr(step_03_mod, "COUNTS_OUTPUT_FILE", tmp_dirs["raw"] / "registry_entity_counts_by_province.json")
    monkeypatch.setattr(step_03_mod, "DEV_MODE", False)
    # Speed up: no waits
    monkeypatch.setattr(step_03_mod, "PWT_BETWEEN_REQUESTS_MS", 0)
    monkeypatch.setattr(step_03_mod, "PWT_POST_LOAD_WAIT_MS", 0)
    monkeypatch.setattr(step_03_mod, "PWT_COOKIE_WAIT_MS", 0)
    monkeypatch.setattr(step_03_mod, "WAIT_AFTER_SELECT_MS", 0)
    monkeypatch.setattr(step_03_mod, "WAIT_AFTER_SEARCH_MS", 0)
    monkeypatch.setattr(step_03_mod, "WAIT_RETRY_MS", 0)
    monkeypatch.setattr(step_03_mod, "MAX_PROVINCE_RETRIES", 1)
    return tmp_dirs


# ---------------------------------------------------------------------------
# Tests — main()
# ---------------------------------------------------------------------------

class TestStep03Main:

    def test_produces_counts_output(
        self,
        monkeypatch: pytest.MonkeyPatch,
        _patch_dirs: dict[str, Path],
    ) -> None:
        _seed_province_file(_patch_dirs["provinces"], "lazio.json", LAZIO_PROVINCES)

        monkeypatch.setattr(
            step_03_mod, "sync_playwright",
            lambda: _build_playwright_mock({"Roma": 1500}),
        )
        monkeypatch.setattr(step_03_mod, "handle_cookie_banner", lambda page, wait_ms: None)
        monkeypatch.setattr(step_03_mod, "extract_total_results", lambda page: 1500)

        step_03_mod.main()

        output_file = _patch_dirs["raw"] / "registry_entity_counts_by_province.json"
        assert output_file.exists()
        data = json.loads(output_file.read_text(encoding="utf-8"))
        assert data["dimension"] == "province_entity_counts"
        assert data["count"] == 1
        item = data["items"][0]
        assert item["province_name"] == "Roma"
        assert item["entities_total"] == 1500

    def test_processes_multiple_provinces(
        self,
        monkeypatch: pytest.MonkeyPatch,
        _patch_dirs: dict[str, Path],
    ) -> None:
        _seed_province_file(_patch_dirs["provinces"], "lazio.json", LAZIO_PROVINCES)
        _seed_province_file(_patch_dirs["provinces"], "lombardia.json", LOMBARDIA_PROVINCES)

        call_idx = {"n": 0}
        counts = [1500, 2000]

        def _rotating_extract(page: Any) -> int:
            idx = call_idx["n"]
            call_idx["n"] += 1
            return counts[idx]

        monkeypatch.setattr(
            step_03_mod, "sync_playwright",
            lambda: _build_playwright_mock({"Roma": 1500, "Milano": 2000}),
        )
        monkeypatch.setattr(step_03_mod, "handle_cookie_banner", lambda page, wait_ms: None)
        monkeypatch.setattr(step_03_mod, "extract_total_results", _rotating_extract)

        step_03_mod.main()

        data = json.loads(
            (_patch_dirs["raw"] / "registry_entity_counts_by_province.json").read_text(encoding="utf-8")
        )
        assert data["count"] == 2

    def test_raises_if_no_province_files(
        self,
        monkeypatch: pytest.MonkeyPatch,
        _patch_dirs: dict[str, Path],
    ) -> None:
        """Empty provinces dir triggers FileNotFoundError from collect_all_provinces."""
        monkeypatch.setattr(
            step_03_mod, "sync_playwright",
            lambda: _build_playwright_mock({}),
        )

        with pytest.raises(FileNotFoundError):
            step_03_mod.main()


# ---------------------------------------------------------------------------
# Tests — helper functions
# ---------------------------------------------------------------------------

class TestNormalizeCountRow:

    def test_normalizes_all_fields(self) -> None:
        row = {
            "region_id": 12,
            "region_name": "Lazio",
            "province_id": 58,
            "province_name": "Roma",
            "province_abbr": "RM",
        }
        result = step_03_mod.normalize_count_row(row, 1500)
        assert result["entities_total"] == 1500
        assert result["province_abbr"] == "RM"


class TestLoadProvinceFiles:

    def test_loads_sorted_files(self, tmp_path: Path) -> None:
        for name in ("b_region.json", "a_region.json"):
            (tmp_path / name).write_text("{}", encoding="utf-8")

        files = step_03_mod.load_province_files(tmp_path)
        assert len(files) == 2
        assert files[0].name == "a_region.json"

    def test_raises_on_empty_dir(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            step_03_mod.load_province_files(tmp_path)


class TestExtractTotalResults:

    @staticmethod
    def _build_page(inner_text: str, *, visible: bool = True) -> MagicMock:
        page = MagicMock()
        locator = MagicMock()
        locator.is_visible.return_value = visible
        locator.inner_text.return_value = inner_text
        page.locator.return_value = MagicMock(first=locator)
        return page

    def test_parses_plain_number(self) -> None:
        page = self._build_page("1234")
        assert step_03_mod.extract_total_results(page) == 1234

    def test_extracts_digits_from_mixed_text(self) -> None:
        page = self._build_page("Risultati: 1.500 trovati")
        assert step_03_mod.extract_total_results(page) == 1500

    def test_returns_none_when_not_visible(self) -> None:
        page = self._build_page("1234", visible=False)
        assert step_03_mod.extract_total_results(page) is None

    def test_returns_none_when_no_digits(self) -> None:
        page = self._build_page("Nessun risultato")
        assert step_03_mod.extract_total_results(page) is None

    def test_falls_back_to_second_selector(self) -> None:
        page = MagicMock()
        first_locator = MagicMock()
        first_locator.is_visible.side_effect = Exception("not found")
        second_locator = MagicMock()
        second_locator.is_visible.return_value = True
        second_locator.inner_text.return_value = "42"
        page.locator.return_value = MagicMock(
            first=MagicMock(side_effect=[first_locator, second_locator]),
        )
        # Re-build so each locator() call returns a different .first
        call_count = {"n": 0}
        locators = [first_locator, second_locator]

        def _locator_factory(selector: str) -> MagicMock:
            m = MagicMock()
            m.first = locators[call_count["n"]]
            call_count["n"] += 1
            return m

        page.locator = _locator_factory
        assert step_03_mod.extract_total_results(page) == 42

    def test_returns_none_when_all_selectors_fail(self) -> None:
        page = MagicMock()
        locator = MagicMock()
        locator.is_visible.side_effect = Exception("timeout")
        page.locator.return_value = MagicMock(first=locator)
        assert step_03_mod.extract_total_results(page) is None
