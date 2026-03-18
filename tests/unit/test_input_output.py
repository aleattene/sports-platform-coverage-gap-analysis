"""Tests for src.utils.input_output — JSON save/load utilities."""

import json
from pathlib import Path

import pytest
from src.utils.input_output import load_json, save_json


class TestSaveJson:

    def test_saves_dict(self, tmp_path: Path) -> None:
        output = tmp_path / "test.json"
        payload = {"key": "value"}
        save_json(payload, output)
        assert output.exists()
        assert json.loads(output.read_text(encoding="utf-8")) == payload

    def test_saves_list(self, tmp_path: Path) -> None:
        output = tmp_path / "test.json"
        payload = [1, 2, 3]
        save_json(payload, output)
        assert json.loads(output.read_text(encoding="utf-8")) == payload

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        output = tmp_path / "nested" / "deep" / "test.json"
        save_json({"a": 1}, output)
        assert output.exists()

    def test_rejects_non_json_extension(self, tmp_path: Path) -> None:
        output = tmp_path / "test.txt"
        with pytest.raises(ValueError, match=".json"):
            save_json({}, output)

    def test_rejects_non_serializable_payload(self, tmp_path: Path) -> None:
        output = tmp_path / "test.json"
        with pytest.raises(TypeError, match="not JSON-serializable"):
            save_json({1, 2, 3}, output)  # sets are not JSON-serializable

    def test_preserves_unicode(self, tmp_path: Path) -> None:
        output = tmp_path / "test.json"
        payload = {"name": "Émilia-Romagna"}
        save_json(payload, output)
        content = output.read_text(encoding="utf-8")
        assert "Émilia-Romagna" in content  # ensure_ascii=False

    def test_overwrites_existing_file(self, tmp_path: Path) -> None:
        output = tmp_path / "test.json"
        save_json({"v": 1}, output)
        save_json({"v": 2}, output)
        assert json.loads(output.read_text(encoding="utf-8")) == {"v": 2}


class TestLoadJson:

    def test_loads_dict(self, tmp_path: Path) -> None:
        input_file = tmp_path / "test.json"
        input_file.write_text('{"key": "value"}', encoding="utf-8")
        assert load_json(input_file) == {"key": "value"}

    def test_loads_list(self, tmp_path: Path) -> None:
        input_file = tmp_path / "test.json"
        input_file.write_text("[1, 2, 3]", encoding="utf-8")
        assert load_json(input_file) == [1, 2, 3]

    def test_rejects_non_json_extension(self, tmp_path: Path) -> None:
        input_file = tmp_path / "test.csv"
        input_file.write_text("{}", encoding="utf-8")
        with pytest.raises(ValueError, match=".json"):
            load_json(input_file)

    def test_file_not_found(self, tmp_path: Path) -> None:
        input_file = tmp_path / "missing.json"
        with pytest.raises(FileNotFoundError):
            load_json(input_file)

    def test_empty_file(self, tmp_path: Path) -> None:
        input_file = tmp_path / "test.json"
        input_file.write_text("", encoding="utf-8")
        with pytest.raises(ValueError, match="empty"):
            load_json(input_file)

    def test_invalid_json(self, tmp_path: Path) -> None:
        input_file = tmp_path / "test.json"
        input_file.write_text("{broken", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            load_json(input_file)

    def test_directory_path_rejected(self, tmp_path: Path) -> None:
        dir_path = tmp_path / "subdir.json"
        dir_path.mkdir()
        with pytest.raises(ValueError, match="not a file"):
            load_json(dir_path)
