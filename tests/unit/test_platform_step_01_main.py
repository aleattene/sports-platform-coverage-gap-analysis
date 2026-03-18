"""Tests for platform step_01 main() — entity retrieval orchestration."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


class TestStep01Main:

    def _run_main_with_mock_api(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        raw_api_response: list[dict[str, Any]],
    ) -> Path:
        """Run step_01 main() with a mocked API response and temp output dirs."""
        raw_dir = tmp_path / "raw"
        quality_dir = tmp_path / "quality"
        raw_dir.mkdir()
        quality_dir.mkdir()

        import src.data_collection.sport_platforms.example_platform.step_01_retrieve_entities as mod

        monkeypatch.setattr(mod, "PLATFORM_BASE_URL", "https://example.com")
        monkeypatch.setattr(mod, "PLATFORM_ORGS_ENDPOINT", "/api/entities")
        monkeypatch.setattr(mod, "PLATFORM_REQUEST_TIMEOUT_S", 10)
        monkeypatch.setattr(mod, "PLATFORM_MAX_RETRIES", 1)
        monkeypatch.setattr(mod, "PLATFORM_REQUEST_DELAY_S", 0)
        monkeypatch.setattr(mod, "RAW_OUTPUT", raw_dir / "platform_entities.json")
        monkeypatch.setattr(mod, "QUALITY_OUTPUT", quality_dir / "entities_retrieval_checks.json")
        monkeypatch.setattr(mod, "PROJECT_ROOT", tmp_path)

        mock_client = MagicMock()
        monkeypatch.setattr(mod, "create_client", lambda timeout_s: mock_client)
        monkeypatch.setattr(
            mod, "fetch_json_with_retry",
            lambda client, url, max_retries, base_delay_s: raw_api_response,
        )

        mod.main()
        return raw_dir

    def test_main_saves_sanitized_entities(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        valid_raw_api_item: dict[str, Any],
    ) -> None:
        raw_dir = self._run_main_with_mock_api(monkeypatch, tmp_path, [valid_raw_api_item])

        import json
        output = raw_dir / "platform_entities.json"
        assert output.exists()
        data = json.loads(output.read_text(encoding="utf-8"))
        assert data["count"] == 1
        # Verify no sensitive fields leaked
        item = data["items"][0]
        assert "name" not in item
        assert "address" not in item
        assert "logo" not in item

    def test_main_writes_quality_report(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        valid_raw_api_item: dict[str, Any],
    ) -> None:
        self._run_main_with_mock_api(monkeypatch, tmp_path, [valid_raw_api_item])

        import json
        quality_file = tmp_path / "quality" / "entities_retrieval_checks.json"
        assert quality_file.exists()
        data = json.loads(quality_file.read_text(encoding="utf-8"))
        assert data["raw_count"] == 1
        assert data["selected_count"] == 1
        assert data["skipped_count"] == 0

    def test_main_counts_skipped_invalid_items(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        valid_raw_api_item: dict[str, Any],
    ) -> None:
        invalid_item = {"no_sport": True}
        self._run_main_with_mock_api(monkeypatch, tmp_path, [valid_raw_api_item, invalid_item])

        import json
        quality_file = tmp_path / "quality" / "entities_retrieval_checks.json"
        data = json.loads(quality_file.read_text(encoding="utf-8"))
        assert data["raw_count"] == 2
        assert data["selected_count"] == 1
        assert data["skipped_count"] == 1

    def test_main_raises_if_no_base_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import src.data_collection.sport_platforms.example_platform.step_01_retrieve_entities as mod
        monkeypatch.setattr(mod, "PLATFORM_BASE_URL", "")
        with pytest.raises(ValueError, match="PLATFORM_BASE_URL"):
            mod.main()

    def test_main_raises_if_no_endpoint(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import src.data_collection.sport_platforms.example_platform.step_01_retrieve_entities as mod
        monkeypatch.setattr(mod, "PLATFORM_BASE_URL", "https://example.com")
        monkeypatch.setattr(mod, "PLATFORM_ORGS_ENDPOINT", "")
        with pytest.raises(ValueError, match="PLATFORM_ORGS_ENDPOINT"):
            mod.main()

    def test_main_raises_if_response_not_list(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        import src.data_collection.sport_platforms.example_platform.step_01_retrieve_entities as mod
        monkeypatch.setattr(mod, "PLATFORM_BASE_URL", "https://example.com")
        monkeypatch.setattr(mod, "PLATFORM_ORGS_ENDPOINT", "/api/entities")
        monkeypatch.setattr(mod, "PLATFORM_REQUEST_TIMEOUT_S", 10)
        monkeypatch.setattr(mod, "PLATFORM_MAX_RETRIES", 1)
        monkeypatch.setattr(mod, "PLATFORM_REQUEST_DELAY_S", 0)

        mock_client = MagicMock()
        monkeypatch.setattr(mod, "create_client", lambda timeout_s: mock_client)
        monkeypatch.setattr(
            mod, "fetch_json_with_retry",
            lambda client, url, max_retries, base_delay_s: {"not": "a list"},
        )

        with pytest.raises(ValueError, match="JSON array"):
            mod.main()
