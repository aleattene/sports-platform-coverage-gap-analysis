"""Integration tests for registry step_02 — retrieve provinces.

Playwright is fully mocked: these tests verify region iteration, province file
generation, quality checks, and error handling without any browser or network.
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, PropertyMock

import pytest

import src.data_collection.sport_registries.example_registry.step_02_retrieve_provinces as step_02_mod


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

FAKE_REGIONS_PAYLOAD: dict[str, Any] = {
    "dimension": "regions",
    "count": 2,
    "items": [
        {"value": "12", "label": "Lazio"},
        {"value": "03", "label": "Lombardia"},
    ],
}

FAKE_PROVINCES: dict[str, list[dict[str, Any]]] = {
    "12": [
        {"codR": 12, "nomeR": "Lazio", "codP": 58, "nomeP": "Roma", "siglaP": "RM"},
        {"codR": 12, "nomeR": "Lazio", "codP": 60, "nomeP": "Frosinone", "siglaP": "FR"},
    ],
    "03": [
        {"codR": 3, "nomeR": "Lombardia", "codP": 15, "nomeP": "Milano", "siglaP": "MI"},
    ],
}


def _seed_regions(regions_dir: Path) -> None:
    regions_dir.mkdir(parents=True, exist_ok=True)
    (regions_dir / "regions.json").write_text(
        json.dumps(FAKE_REGIONS_PAYLOAD), encoding="utf-8",
    )


def _build_playwright_mock(provinces_by_region: dict[str, list[dict[str, Any]]]) -> MagicMock:
    """Build a Playwright mock where expect_response returns province payloads."""
    region_call_index = {"idx": 0}
    region_values = list(provinces_by_region.keys())

    page = MagicMock()

    def _fake_expect_response(*args: Any, **kwargs: Any) -> MagicMock:
        ctx = MagicMock()
        idx = region_call_index["idx"]
        region_key = region_values[idx] if idx < len(region_values) else region_values[-1]
        region_call_index["idx"] += 1

        response_mock = MagicMock()
        response_mock.json.return_value = provinces_by_region[region_key]
        type(ctx).value = PropertyMock(return_value=response_mock)

        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        return ctx

    page.expect_response = _fake_expect_response

    # find_region_select needs a visible locator
    region_locator = MagicMock()
    region_locator.is_visible.return_value = True
    page.locator.return_value = MagicMock(first=region_locator)

    context = MagicMock()
    context.new_page.return_value = page
    browser = MagicMock()
    browser.new_context.return_value = context
    playwright = MagicMock()
    playwright.chromium.launch.return_value = browser

    pw_cm = MagicMock()
    pw_cm.__enter__ = MagicMock(return_value=playwright)
    pw_cm.__exit__ = MagicMock(return_value=False)
    return pw_cm


@pytest.fixture
def tmp_dirs(tmp_path: Path) -> dict[str, Path]:
    regions_dir = tmp_path / "regions"
    provinces_dir = tmp_path / "provinces"
    quality_dir = tmp_path / "quality"
    for d in (regions_dir, provinces_dir, quality_dir):
        d.mkdir()
    return {"regions": regions_dir, "provinces": provinces_dir, "quality": quality_dir}


@pytest.fixture
def _patch_dirs(monkeypatch: pytest.MonkeyPatch, tmp_dirs: dict[str, Path]) -> dict[str, Path]:
    monkeypatch.setattr(step_02_mod, "REGIONS_DIR", tmp_dirs["regions"])
    monkeypatch.setattr(step_02_mod, "PROVINCES_DIR", tmp_dirs["provinces"])
    monkeypatch.setattr(step_02_mod, "QUALITY_DIR", tmp_dirs["quality"])
    return tmp_dirs


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestStep02Main:

    def test_produces_province_files(
        self,
        monkeypatch: pytest.MonkeyPatch,
        _patch_dirs: dict[str, Path],
    ) -> None:
        _seed_regions(_patch_dirs["regions"])

        monkeypatch.setattr(step_02_mod, "sync_playwright", lambda: _build_playwright_mock(FAKE_PROVINCES))
        monkeypatch.setattr(step_02_mod, "handle_cookie_banner", lambda page, wait_ms: None)

        step_02_mod.main()

        province_files = sorted(_patch_dirs["provinces"].glob("*.json"))
        assert len(province_files) == 2  # one per region

    def test_province_file_structure(
        self,
        monkeypatch: pytest.MonkeyPatch,
        _patch_dirs: dict[str, Path],
    ) -> None:
        _seed_regions(_patch_dirs["regions"])

        monkeypatch.setattr(step_02_mod, "sync_playwright", lambda: _build_playwright_mock(FAKE_PROVINCES))
        monkeypatch.setattr(step_02_mod, "handle_cookie_banner", lambda page, wait_ms: None)

        step_02_mod.main()

        province_files = sorted(_patch_dirs["provinces"].glob("*.json"))
        for pf in province_files:
            data = json.loads(pf.read_text(encoding="utf-8"))
            assert data["dimension"] == "provinces"
            assert "region_id" in data
            assert "region_name" in data
            assert isinstance(data["items"], list)
            for item in data["items"]:
                assert "province_id" in item
                assert "province_name" in item
                assert "province_abbr" in item

    def test_produces_quality_checks(
        self,
        monkeypatch: pytest.MonkeyPatch,
        _patch_dirs: dict[str, Path],
    ) -> None:
        _seed_regions(_patch_dirs["regions"])

        monkeypatch.setattr(step_02_mod, "sync_playwright", lambda: _build_playwright_mock(FAKE_PROVINCES))
        monkeypatch.setattr(step_02_mod, "handle_cookie_banner", lambda page, wait_ms: None)

        step_02_mod.main()

        quality_file = _patch_dirs["quality"] / "provinces_checks.json"
        assert quality_file.exists()
        data = json.loads(quality_file.read_text(encoding="utf-8"))
        assert data["count"] == 2
        assert all(r["status"] == "ok" for r in data["items"])

    def test_records_failed_region_in_quality(
        self,
        monkeypatch: pytest.MonkeyPatch,
        _patch_dirs: dict[str, Path],
    ) -> None:
        """When expect_response raises for a region, quality marks it as failed."""
        _seed_regions(_patch_dirs["regions"])

        call_count = {"n": 0}

        def _failing_on_second(*args: Any, **kwargs: Any) -> MagicMock:
            call_count["n"] += 1
            ctx = MagicMock()
            if call_count["n"] == 2:
                ctx.__enter__ = MagicMock(side_effect=RuntimeError("timeout"))
            else:
                response_mock = MagicMock()
                response_mock.json.return_value = FAKE_PROVINCES["12"]
                type(ctx).value = PropertyMock(return_value=response_mock)
                ctx.__enter__ = MagicMock(return_value=ctx)
            ctx.__exit__ = MagicMock(return_value=False)
            return ctx

        page = MagicMock()
        page.expect_response = _failing_on_second

        region_locator = MagicMock()
        region_locator.is_visible.return_value = True
        page.locator.return_value = MagicMock(first=region_locator)

        context = MagicMock()
        context.new_page.return_value = page
        browser = MagicMock()
        browser.new_context.return_value = context
        playwright = MagicMock()
        playwright.chromium.launch.return_value = browser

        pw_cm = MagicMock()
        pw_cm.__enter__ = MagicMock(return_value=playwright)
        pw_cm.__exit__ = MagicMock(return_value=False)

        monkeypatch.setattr(step_02_mod, "sync_playwright", lambda: pw_cm)
        monkeypatch.setattr(step_02_mod, "handle_cookie_banner", lambda page, wait_ms: None)

        step_02_mod.main()

        quality_file = _patch_dirs["quality"] / "provinces_checks.json"
        data = json.loads(quality_file.read_text(encoding="utf-8"))
        statuses = [r["status"] for r in data["items"]]
        assert "ok" in statuses
        assert "failed" in statuses


class TestLoadRegions:

    def test_loads_items_format(self, tmp_path: Path) -> None:
        regions_file = tmp_path / "regions.json"
        regions_file.write_text(
            json.dumps({"items": [{"value": "1", "label": "TestRegion"}]}),
            encoding="utf-8",
        )
        result = step_02_mod.load_regions(regions_file)
        assert len(result) == 1
        assert result[0]["label"] == "TestRegion"

    def test_loads_list_format(self, tmp_path: Path) -> None:
        regions_file = tmp_path / "regions.json"
        regions_file.write_text(
            json.dumps([{"value": "1", "label": "TestRegion"}]),
            encoding="utf-8",
        )
        result = step_02_mod.load_regions(regions_file)
        assert len(result) == 1

    def test_raises_on_empty(self, tmp_path: Path) -> None:
        regions_file = tmp_path / "regions.json"
        regions_file.write_text(json.dumps({"items": []}), encoding="utf-8")
        with pytest.raises(ValueError, match="empty"):
            step_02_mod.load_regions(regions_file)

    def test_raises_on_missing_keys(self, tmp_path: Path) -> None:
        regions_file = tmp_path / "regions.json"
        regions_file.write_text(
            json.dumps({"items": [{"value": "1"}]}),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="label"):
            step_02_mod.load_regions(regions_file)


class TestNormalizeProvincePayload:

    def test_normalizes_keys(self) -> None:
        region = {"value": "12", "label": "Lazio"}
        raw = [{"codR": 12, "nomeR": "Lazio", "codP": 58, "nomeP": "Roma", "siglaP": "RM"}]

        result = step_02_mod.normalize_province_payload(region, raw)
        assert result["dimension"] == "provinces"
        assert result["region_id"] == 12
        assert result["count"] == 1
        item = result["items"][0]
        assert item["province_name"] == "Roma"
        assert item["province_abbr"] == "RM"

    def test_raises_on_missing_region_keys(self) -> None:
        with pytest.raises(ValueError, match="value"):
            step_02_mod.normalize_province_payload({"label": "Test"}, [])
