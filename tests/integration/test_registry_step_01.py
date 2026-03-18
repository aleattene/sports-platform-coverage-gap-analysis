"""Integration tests for registry step_01 — retrieve regions.

Playwright is fully mocked: these tests verify the orchestration logic,
output structure, and DEV_MODE sampling without any browser or network access.
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

import src.data_collection.sport_registries.example_registry.step_01_retrieve_regions as step_01_mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FAKE_REGIONS: list[dict[str, str]] = [
    {"value": str(i), "label": f"Regione_{i}"} for i in range(1, 21)
]


def _build_playwright_mock() -> MagicMock:
    """Build a nested Playwright mock: playwright → browser → context → page."""
    page = MagicMock()
    context = MagicMock()
    context.new_page.return_value = page
    browser = MagicMock()
    browser.new_context.return_value = context
    playwright = MagicMock()
    playwright.chromium.launch.return_value = browser

    pw_context_manager = MagicMock()
    pw_context_manager.__enter__ = MagicMock(return_value=playwright)
    pw_context_manager.__exit__ = MagicMock(return_value=False)
    return pw_context_manager


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestStep01Main:

    def test_saves_regions_json(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        regions_dir = tmp_path / "regions"
        regions_dir.mkdir()

        monkeypatch.setattr(step_01_mod, "REGIONS_DIR", regions_dir)
        monkeypatch.setattr(step_01_mod, "DEV_MODE", False)
        monkeypatch.setattr(step_01_mod, "sync_playwright", lambda: _build_playwright_mock())
        monkeypatch.setattr(step_01_mod, "handle_cookie_banner", lambda page, wait_ms: None)
        monkeypatch.setattr(step_01_mod, "extract_select_options", lambda **kwargs: FAKE_REGIONS)

        step_01_mod.main()

        output = regions_dir / "regions.json"
        assert output.exists()
        data = json.loads(output.read_text(encoding="utf-8"))
        assert data["dimension"] == "regions"
        assert data["count"] == 20
        assert len(data["items"]) == 20

    def test_output_structure_has_required_keys(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        regions_dir = tmp_path / "regions"
        regions_dir.mkdir()

        monkeypatch.setattr(step_01_mod, "REGIONS_DIR", regions_dir)
        monkeypatch.setattr(step_01_mod, "DEV_MODE", False)
        monkeypatch.setattr(step_01_mod, "sync_playwright", lambda: _build_playwright_mock())
        monkeypatch.setattr(step_01_mod, "handle_cookie_banner", lambda page, wait_ms: None)
        monkeypatch.setattr(step_01_mod, "extract_select_options", lambda **kwargs: FAKE_REGIONS)

        step_01_mod.main()

        data = json.loads((regions_dir / "regions.json").read_text(encoding="utf-8"))
        for item in data["items"]:
            assert "value" in item
            assert "label" in item

    def test_dev_mode_samples_regions(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        regions_dir = tmp_path / "regions"
        regions_dir.mkdir()
        sample_size = 3

        monkeypatch.setattr(step_01_mod, "REGIONS_DIR", regions_dir)
        monkeypatch.setattr(step_01_mod, "DEV_MODE", True)
        monkeypatch.setattr(step_01_mod, "DEV_SAMPLE_REGIONS", sample_size)
        monkeypatch.setattr(step_01_mod, "sync_playwright", lambda: _build_playwright_mock())
        monkeypatch.setattr(step_01_mod, "handle_cookie_banner", lambda page, wait_ms: None)
        monkeypatch.setattr(step_01_mod, "extract_select_options", lambda **kwargs: FAKE_REGIONS)

        step_01_mod.main()

        data = json.loads((regions_dir / "regions.json").read_text(encoding="utf-8"))
        assert data["count"] == sample_size
        assert len(data["items"]) == sample_size

    def test_warns_on_unexpected_region_count(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        regions_dir = tmp_path / "regions"
        regions_dir.mkdir()

        fewer_regions = FAKE_REGIONS[:10]

        monkeypatch.setattr(step_01_mod, "REGIONS_DIR", regions_dir)
        monkeypatch.setattr(step_01_mod, "DEV_MODE", False)
        monkeypatch.setattr(step_01_mod, "sync_playwright", lambda: _build_playwright_mock())
        monkeypatch.setattr(step_01_mod, "handle_cookie_banner", lambda page, wait_ms: None)
        monkeypatch.setattr(step_01_mod, "extract_select_options", lambda **kwargs: fewer_regions)

        with caplog.at_level("WARNING"):
            step_01_mod.main()

        assert any("Unexpected number of regions" in msg for msg in caplog.messages)

    def test_raises_on_playwright_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        regions_dir = tmp_path / "regions"
        regions_dir.mkdir()

        monkeypatch.setattr(step_01_mod, "REGIONS_DIR", regions_dir)
        monkeypatch.setattr(step_01_mod, "DEV_MODE", False)
        monkeypatch.setattr(step_01_mod, "sync_playwright", lambda: _build_playwright_mock())
        monkeypatch.setattr(step_01_mod, "handle_cookie_banner", lambda page, wait_ms: None)
        monkeypatch.setattr(
            step_01_mod, "extract_select_options",
            lambda **kwargs: (_ for _ in ()).throw(RuntimeError("DOM error")),
        )

        with pytest.raises(RuntimeError, match="DOM error"):
            step_01_mod.main()
