"""Integration tests for platform_pipeline.main() — orchestration logic.

All remote calls (HTTP API) are mocked: these tests verify the pipeline
orchestration, step sequencing, summary generation, and error handling
without any network access.
"""

import json
import types
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

import src.data_collection.sport_platforms.example_platform.platform_pipeline as pipeline_mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seed_raw_data(raw_input: Path) -> None:
    """Create a minimal raw JSON file so the pipeline detects existing data."""
    raw_input.parent.mkdir(parents=True, exist_ok=True)
    raw_input.write_text(
        json.dumps({
            "dimension": "platform_entities",
            "retrieved_at": "20240315_143022",
            "count": 1,
            "items": [{"sport": ["calcio"], "registration_year": 2023, "province_abbr": "RM", "region_code": "LAZ"}],
        }),
        encoding="utf-8",
    )


def _read_summary(quality_dir: Path) -> dict[str, Any]:
    summary_file = quality_dir / "pipeline_run_summary.json"
    return json.loads(summary_file.read_text(encoding="utf-8"))


def _make_patched_import(
    fake_modules: dict[str, types.ModuleType],
) -> Any:
    """Build a __import__ replacement that intercepts specific module names."""
    original_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

    def _patched(name: str, *args: Any, **kwargs: Any) -> Any:
        if name in fake_modules:
            return fake_modules[name]
        return original_import(name, *args, **kwargs)

    return _patched


def _fake_module(fn: Any) -> types.ModuleType:
    """Wrap a callable as a fake module with a .main attribute."""
    mod = types.ModuleType("fake_step")
    mod.main = fn  # type: ignore[attr-defined]
    return mod


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_dirs(tmp_path: Path) -> dict[str, Path]:
    """Create temporary dirs and a RAW_INPUT path for a test run."""
    raw_dir = tmp_path / "raw"
    quality_dir = tmp_path / "quality"
    raw_dir.mkdir()
    quality_dir.mkdir()
    return {
        "raw_dir": raw_dir,
        "raw_input": raw_dir / "platform_entities.json",
        "quality": quality_dir,
    }


@pytest.fixture
def _patch_dirs(monkeypatch: pytest.MonkeyPatch, tmp_dirs: dict[str, Path]) -> dict[str, Path]:
    """Patch pipeline module paths to use tmp dirs."""
    monkeypatch.setattr(pipeline_mod, "RAW_INPUT", tmp_dirs["raw_input"])
    monkeypatch.setattr(pipeline_mod, "PLATFORM_QUALITY_DIR", tmp_dirs["quality"])
    return tmp_dirs


# ---------------------------------------------------------------------------
# Tests — fetch disabled (default mode)
# ---------------------------------------------------------------------------

class TestPlatformPipelineFetchDisabled:
    """FETCH_PLATFORM_DATA=false: step_01 is skipped."""

    def test_no_raw_data_skips_all_steps(
        self,
        monkeypatch: pytest.MonkeyPatch,
        _patch_dirs: dict[str, Path],
    ) -> None:
        """Without raw data, both steps are marked 'skipped'."""
        monkeypatch.setattr(pipeline_mod, "FETCH_PLATFORM_DATA", False)

        pipeline_mod.main()

        summary = _read_summary(_patch_dirs["quality"])
        assert summary["status"] == "ok"
        assert summary["fetch_enabled"] is False
        assert len(summary["steps"]) == 2
        assert all(s["status"] == "skipped" for s in summary["steps"])

    def test_raw_data_exists_runs_step_02(
        self,
        monkeypatch: pytest.MonkeyPatch,
        _patch_dirs: dict[str, Path],
    ) -> None:
        """With raw data present, step_02 is executed (step_01 still skipped)."""
        monkeypatch.setattr(pipeline_mod, "FETCH_PLATFORM_DATA", False)

        _seed_raw_data(_patch_dirs["raw_input"])

        mock_step_02_fn = MagicMock()
        fake_modules = {
            "src.data_collection.sport_platforms.example_platform.step_02_build_analysis_dataset": _fake_module(mock_step_02_fn),
        }
        monkeypatch.setattr("builtins.__import__", _make_patched_import(fake_modules))

        pipeline_mod.main()

        summary = _read_summary(_patch_dirs["quality"])
        assert summary["status"] == "ok"
        assert summary["steps"][0]["status"] == "skipped"
        assert summary["steps"][1]["step_name"] == "step_02_build_analysis_dataset"
        assert summary["steps"][1]["status"] == "ok"
        mock_step_02_fn.assert_called_once()


# ---------------------------------------------------------------------------
# Tests — fetch enabled
# ---------------------------------------------------------------------------

class TestPlatformPipelineFetchEnabled:
    """FETCH_PLATFORM_DATA=true: step_01 runs, then step_02."""

    def test_all_steps_succeed(
        self,
        monkeypatch: pytest.MonkeyPatch,
        _patch_dirs: dict[str, Path],
    ) -> None:
        """When both steps succeed, pipeline status is 'ok'."""
        monkeypatch.setattr(pipeline_mod, "FETCH_PLATFORM_DATA", True)

        # step_01 succeeds and seeds raw data so step_02 branch is entered
        def _step_01_with_seed() -> None:
            _seed_raw_data(_patch_dirs["raw_input"])

        mock_step_02_fn = MagicMock()
        fake_modules = {
            "src.data_collection.sport_platforms.example_platform.step_01_retrieve_entities": _fake_module(_step_01_with_seed),
            "src.data_collection.sport_platforms.example_platform.step_02_build_analysis_dataset": _fake_module(mock_step_02_fn),
        }
        monkeypatch.setattr("builtins.__import__", _make_patched_import(fake_modules))

        pipeline_mod.main()

        summary = _read_summary(_patch_dirs["quality"])
        assert summary["status"] == "ok"
        assert summary["fetch_enabled"] is True
        assert len(summary["steps"]) == 2
        assert all(s["status"] == "ok" for s in summary["steps"])
        mock_step_02_fn.assert_called_once()

    def test_step_01_failure_stops_pipeline(
        self,
        monkeypatch: pytest.MonkeyPatch,
        _patch_dirs: dict[str, Path],
    ) -> None:
        """When step_01 fails, pipeline stops and raises RuntimeError."""
        monkeypatch.setattr(pipeline_mod, "FETCH_PLATFORM_DATA", True)

        def _failing_step_01() -> None:
            raise RuntimeError("simulated API failure")

        fake_modules = {
            "src.data_collection.sport_platforms.example_platform.step_01_retrieve_entities": _fake_module(_failing_step_01),
        }
        monkeypatch.setattr("builtins.__import__", _make_patched_import(fake_modules))

        with pytest.raises(RuntimeError, match="Platform pipeline failed"):
            pipeline_mod.main()

        summary = _read_summary(_patch_dirs["quality"])
        assert summary["status"] == "failed"
        assert len(summary["steps"]) == 1
        assert summary["steps"][0]["status"] == "failed"

    def test_step_02_failure_raises(
        self,
        monkeypatch: pytest.MonkeyPatch,
        _patch_dirs: dict[str, Path],
    ) -> None:
        """When step_02 fails, pipeline status is 'failed' and RuntimeError is raised."""
        monkeypatch.setattr(pipeline_mod, "FETCH_PLATFORM_DATA", True)

        def _step_01_with_seed() -> None:
            _seed_raw_data(_patch_dirs["raw_input"])

        def _failing_step_02() -> None:
            raise RuntimeError("step_02 exploded")

        fake_modules = {
            "src.data_collection.sport_platforms.example_platform.step_01_retrieve_entities": _fake_module(_step_01_with_seed),
            "src.data_collection.sport_platforms.example_platform.step_02_build_analysis_dataset": _fake_module(_failing_step_02),
        }
        monkeypatch.setattr("builtins.__import__", _make_patched_import(fake_modules))

        with pytest.raises(RuntimeError, match="Platform pipeline failed"):
            pipeline_mod.main()

        summary = _read_summary(_patch_dirs["quality"])
        assert summary["status"] == "failed"
        assert summary["steps"][0]["status"] == "ok"
        assert summary["steps"][1]["status"] == "failed"


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
