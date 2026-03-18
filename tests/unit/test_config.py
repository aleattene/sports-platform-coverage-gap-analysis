"""Tests for src.config — environment variable parsing helpers."""

import pytest
from src.config import get_env, get_env_bool, get_env_int


class TestGetEnv:

    def test_returns_value_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TEST_VAR", "hello")
        assert get_env("TEST_VAR") == "hello"

    def test_returns_default_when_missing(self) -> None:
        assert get_env("NONEXISTENT_VAR_XYZ", "fallback") == "fallback"

    def test_returns_empty_string_when_no_default(self) -> None:
        assert get_env("NONEXISTENT_VAR_XYZ") == ""

    def test_raises_when_required_and_missing(self) -> None:
        with pytest.raises(ValueError, match="Missing required"):
            get_env("NONEXISTENT_VAR_XYZ", required=True)

    def test_required_with_value_does_not_raise(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TEST_VAR", "present")
        assert get_env("TEST_VAR", required=True) == "present"


class TestGetEnvBool:

    @pytest.mark.parametrize("value", ["1", "true", "True", "TRUE", "yes", "y", "on", " true "])
    def test_truthy_values(self, monkeypatch: pytest.MonkeyPatch, value: str) -> None:
        monkeypatch.setenv("TEST_BOOL", value)
        assert get_env_bool("TEST_BOOL") is True

    @pytest.mark.parametrize("value", ["0", "false", "False", "no", "off", "anything", ""])
    def test_falsy_values(self, monkeypatch: pytest.MonkeyPatch, value: str) -> None:
        monkeypatch.setenv("TEST_BOOL", value)
        assert get_env_bool("TEST_BOOL") is False

    def test_returns_default_when_missing(self) -> None:
        assert get_env_bool("NONEXISTENT_VAR_XYZ") is False
        assert get_env_bool("NONEXISTENT_VAR_XYZ", True) is True


class TestGetEnvInt:

    def test_returns_parsed_int(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TEST_INT", "42")
        assert get_env_int("TEST_INT", 0) == 42

    def test_returns_default_when_missing(self) -> None:
        assert get_env_int("NONEXISTENT_VAR_XYZ", 99) == 99

    def test_raises_on_non_integer(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TEST_INT", "not_a_number")
        with pytest.raises(ValueError, match="must be an integer"):
            get_env_int("TEST_INT", 0)
