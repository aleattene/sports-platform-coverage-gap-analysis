"""Tests for src.utils.runtime — timer and formatting utilities."""

from src.utils.runtime import elapsed_seconds, format_duration, start_timer, utc_now_iso


class TestUtcNowIso:

    def test_returns_string(self) -> None:
        result = utc_now_iso()
        assert isinstance(result, str)

    def test_contains_timezone_info(self) -> None:
        result = utc_now_iso()
        assert "+" in result or "Z" in result


class TestStartTimerAndElapsed:

    def test_elapsed_returns_numeric(self) -> None:
        timer = start_timer()
        result = elapsed_seconds(timer)
        assert isinstance(result, (int, float))

    def test_elapsed_is_non_negative(self) -> None:
        timer = start_timer()
        result = elapsed_seconds(timer)
        assert result >= 0


class TestFormatDuration:

    def test_zero_seconds(self) -> None:
        assert format_duration(0) == "00.000"

    def test_fractional_seconds(self) -> None:
        assert format_duration(1.5) == "01.500"

    def test_seconds_only(self) -> None:
        assert format_duration(45) == "45.000"

    def test_minutes_and_seconds(self) -> None:
        assert format_duration(125) == "02:05.000"

    def test_hours_minutes_seconds(self) -> None:
        assert format_duration(3661) == "01:01:01.000"

    def test_exact_one_hour(self) -> None:
        assert format_duration(3600) == "01:00.000"

    def test_large_duration(self) -> None:
        result = format_duration(7200 + 1800 + 30.123)
        assert result == "02:30:30.123"
