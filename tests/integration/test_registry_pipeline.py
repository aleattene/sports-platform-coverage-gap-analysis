"""Integration tests for registry_pipeline.main() — orchestration logic.

All remote calls (Playwright) are mocked: these tests verify the pipeline
orchestration, step sequencing, summary generation, and error handling
without any network access.
"""

import json
import types
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

import src.data_collection.sport_registries.example_registry.registry_pipeline as pipeline_mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_step_module(succeed: bool = True) -> types.ModuleType:
    """Return a fake module with a main() that either succeeds or raises."""
    mod = types.ModuleType("fake_step")

    def _main() -> None:
        if not succeed:
            raise RuntimeError("simulated step failure")

    mod.main = _main  # type: ignore[attr-defined]
    return mod


def _seed_raw_data(raw_dir: Path) -> None:
    """Create a minimal JSON file inside raw_dir so the pipeline detects raw data."""
    regions_dir = raw_dir / "regions"
    regions_dir.mkdir(parents=True, exist_ok=True)
    (regions_dir / "regions.json").write_text(
        json.dumps({"dimension": "regions", "count": 1, "items": [{"value": "1", "label": "TestRegione"}]}),
        encoding="utf-8",
    )


def _read_summary(quality_dir: Path) -> dict[str, Any]:
    summary_file = quality_dir / "pipeline_run_summary.json"
    return json.loads(summary_file.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_dirs(tmp_path: Path) -> dict[str, Path]:
    """Create temporary RAW_DIR and QUALITY_DIR for a test run."""
    raw_dir = tmp_path / "raw"
    quality_dir = tmp_path / "quality"
    raw_dir.mkdir()
    quality_dir.mkdir()
    return {"raw": raw_dir, "quality": quality_dir}


@pytest.fixture
def _patch_dirs(monkeypatch: pytest.MonkeyPatch, tmp_dirs: dict[str, Path]) -> dict[str, Path]:
    """Patch pipeline module directory constants to use tmp dirs."""
    monkeypatch.setattr(pipeline_mod, "RAW_DIR", tmp_dirs["raw"])
    monkeypatch.setattr(pipeline_mod, "QUALITY_DIR", tmp_dirs["quality"])
    return tmp_dirs


# ---------------------------------------------------------------------------
# Tests — fetch disabled (default mode)
# ---------------------------------------------------------------------------

class TestRegistryPipelineFetchDisabled:
    """FETCH_REGISTRY_DATA=false: steps 01-03 are skipped."""

    def test_no_raw_data_skips_all_steps(
        self,
        monkeypatch: pytest.MonkeyPatch,
        _patch_dirs: dict[str, Path],
    ) -> None:
        """Without raw data, all four steps are marked 'skipped'."""
        monkeypatch.setattr(pipeline_mod, "FETCH_REGISTRY_DATA", False)
        monkeypatch.setattr(pipeline_mod, "DEV_MODE", False)

        pipeline_mod.main()

        summary = _read_summary(_patch_dirs["quality"])
        assert summary["status"] == "ok"
        assert summary["fetch_enabled"] is False
        assert len(summary["steps"]) == 4
        assert all(s["status"] == "skipped" for s in summary["steps"])

    def test_raw_data_exists_runs_step_04(
        self,
        monkeypatch: pytest.MonkeyPatch,
        _patch_dirs: dict[str, Path],
    ) -> None:
        """With raw data present, step_04 is executed (steps 01-03 still skipped)."""
        monkeypatch.setattr(pipeline_mod, "FETCH_REGISTRY_DATA", False)
        monkeypatch.setattr(pipeline_mod, "DEV_MODE", False)

        _seed_raw_data(_patch_dirs["raw"])

        mock_step_04_fn = MagicMock()
        fake_step_04_mod = types.ModuleType("fake_step_04")
        fake_step_04_mod.main = mock_step_04_fn  # type: ignore[attr-defined]

        original_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

        def _patched_import(name: str, *args: Any, **kwargs: Any) -> Any:
            if name == "src.data_collection.sport_registries.example_registry.step_04_build_analysis_dataset":
                return fake_step_04_mod
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", _patched_import)

        pipeline_mod.main()

        summary = _read_summary(_patch_dirs["quality"])
        assert summary["status"] == "ok"

        skipped = [s for s in summary["steps"] if s["status"] == "skipped"]
        assert len(skipped) == 3

        step_04 = summary["steps"][-1]
        assert step_04["step_name"] == "step_04_build_analysis_dataset"
        assert step_04["status"] == "ok"
        mock_step_04_fn.assert_called_once()


# ---------------------------------------------------------------------------
# Tests — fetch enabled
# ---------------------------------------------------------------------------

class TestRegistryPipelineFetchEnabled:
    """FETCH_REGISTRY_DATA=true: steps 01-03 run, then step_04."""

    def test_all_steps_succeed(
        self,
        monkeypatch: pytest.MonkeyPatch,
        _patch_dirs: dict[str, Path],
    ) -> None:
        """When all steps succeed, pipeline status is 'ok'."""
        monkeypatch.setattr(pipeline_mod, "FETCH_REGISTRY_DATA", True)
        monkeypatch.setattr(pipeline_mod, "DEV_MODE", False)

        # Steps 01-03: mock importlib.import_module
        fake_modules = {
            "src.data_collection.sport_registries.example_registry.step_01_retrieve_regions": _fake_step_module(True),
            "src.data_collection.sport_registries.example_registry.step_02_retrieve_provinces": _fake_step_module(True),
            "src.data_collection.sport_registries.example_registry.step_03_retrieve_entities_by_province": _fake_step_module(True),
        }
        monkeypatch.setattr(
            pipeline_mod.importlib, "import_module",
            lambda path: fake_modules[path],
        )

        # After steps 01-03, the pipeline checks for raw JSON to decide on step_04.
        # Seed raw data so step_04 branch is entered.
        _seed_raw_data(_patch_dirs["raw"])

        # Step 04: intercept the direct import
        mock_step_04_fn = MagicMock()
        fake_step_04_mod = types.ModuleType("fake_step_04")
        fake_step_04_mod.main = mock_step_04_fn  # type: ignore[attr-defined]

        original_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

        def _patched_import(name: str, *args: Any, **kwargs: Any) -> Any:
            if name == "src.data_collection.sport_registries.example_registry.step_04_build_analysis_dataset":
                return fake_step_04_mod
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", _patched_import)

        pipeline_mod.main()

        summary = _read_summary(_patch_dirs["quality"])
        assert summary["status"] == "ok"
        assert summary["fetch_enabled"] is True
        assert len(summary["steps"]) == 4
        assert all(s["status"] == "ok" for s in summary["steps"])
        mock_step_04_fn.assert_called_once()

    def test_step_failure_stops_pipeline(
        self,
        monkeypatch: pytest.MonkeyPatch,
        _patch_dirs: dict[str, Path],
    ) -> None:
        """When a fetch step fails, pipeline stops and raises RuntimeError."""
        monkeypatch.setattr(pipeline_mod, "FETCH_REGISTRY_DATA", True)
        monkeypatch.setattr(pipeline_mod, "DEV_MODE", False)

        # Step 01 succeeds, step 02 fails
        fake_modules = {
            "src.data_collection.sport_registries.example_registry.step_01_retrieve_regions": _fake_step_module(True),
            "src.data_collection.sport_registries.example_registry.step_02_retrieve_provinces": _fake_step_module(False),
        }
        monkeypatch.setattr(
            pipeline_mod.importlib, "import_module",
            lambda path: fake_modules[path],
        )

        with pytest.raises(RuntimeError, match="Registry pipeline failed"):
            pipeline_mod.main()

        summary = _read_summary(_patch_dirs["quality"])
        assert summary["status"] == "failed"

        # step_01 ok, step_02 failed — step_03 never reached
        assert summary["steps"][0]["status"] == "ok"
        assert summary["steps"][1]["status"] == "failed"
        assert len(summary["steps"]) == 2  # step_03, step_04 never appended

    def test_step_04_failure_raises(
        self,
        monkeypatch: pytest.MonkeyPatch,
        _patch_dirs: dict[str, Path],
    ) -> None:
        """When step_04 fails, pipeline status is 'failed' and RuntimeError is raised."""
        monkeypatch.setattr(pipeline_mod, "FETCH_REGISTRY_DATA", True)
        monkeypatch.setattr(pipeline_mod, "DEV_MODE", False)

        fake_modules = {
            "src.data_collection.sport_registries.example_registry.step_01_retrieve_regions": _fake_step_module(True),
            "src.data_collection.sport_registries.example_registry.step_02_retrieve_provinces": _fake_step_module(True),
            "src.data_collection.sport_registries.example_registry.step_03_retrieve_entities_by_province": _fake_step_module(True),
        }
        monkeypatch.setattr(
            pipeline_mod.importlib, "import_module",
            lambda path: fake_modules[path],
        )

        _seed_raw_data(_patch_dirs["raw"])

        # step_04 raises
        def _failing_step_04() -> None:
            raise RuntimeError("step_04 exploded")

        fake_step_04_mod = types.ModuleType("fake_step_04")
        fake_step_04_mod.main = _failing_step_04  # type: ignore[attr-defined]

        original_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

        def _patched_import(name: str, *args: Any, **kwargs: Any) -> Any:
            if name == "src.data_collection.sport_registries.example_registry.step_04_build_analysis_dataset":
                return fake_step_04_mod
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", _patched_import)

        with pytest.raises(RuntimeError, match="Registry pipeline failed"):
            pipeline_mod.main()

        summary = _read_summary(_patch_dirs["quality"])
        assert summary["status"] == "failed"
        assert summary["steps"][-1]["status"] == "failed"


# ---------------------------------------------------------------------------
# Tests — run_step unit behavior
# ---------------------------------------------------------------------------

class TestRunStep:
    """Tests for the run_step() helper function."""

    def test_successful_step_returns_ok(self) -> None:
        result = pipeline_mod.run_step("test_step", lambda: None)
        assert result["step_name"] == "test_step"
        assert result["status"] == "ok"
        assert "started_at_utc" in result
        assert "finished_at_utc" in result
        assert isinstance(result["duration_seconds"], (int, float))

    def test_failing_step_returns_failed(self) -> None:
        def _boom() -> None:
            raise ValueError("boom")

        result = pipeline_mod.run_step("bad_step", _boom)
        assert result["step_name"] == "bad_step"
        assert result["status"] == "failed"


# ---------------------------------------------------------------------------
# Tests — DEV_MODE flag
# ---------------------------------------------------------------------------

class TestDevModeFlag:
    """Verify DEV_MODE is propagated in the pipeline summary."""

    def test_dev_mode_in_summary(
        self,
        monkeypatch: pytest.MonkeyPatch,
        _patch_dirs: dict[str, Path],
    ) -> None:
        monkeypatch.setattr(pipeline_mod, "FETCH_REGISTRY_DATA", False)
        monkeypatch.setattr(pipeline_mod, "DEV_MODE", True)

        pipeline_mod.main()

        summary = _read_summary(_patch_dirs["quality"])
        assert summary["dev_mode"] is True
