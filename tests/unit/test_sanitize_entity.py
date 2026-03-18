"""Tests for sanitize_entity — privacy-critical field extraction."""

from typing import Any
from src.data_collection.sport_platforms.example_platform.step_01_retrieve_entities import (
    sanitize_entity,
)


class TestSanitizeEntity:

    def test_valid_entity(self, valid_raw_api_item: dict[str, Any]) -> None:
        result = sanitize_entity(valid_raw_api_item)
        assert result is not None
        assert result["sport"] == ["calcio"]
        assert result["registration_year"] == 2023
        assert result["province_abbr"] == "RM"
        assert result["region_code"] == "LAZ"

    def test_only_allowed_fields_extracted(self, valid_raw_api_item: dict[str, Any]) -> None:
        """Ensure no sensitive data leaks through sanitization."""
        result = sanitize_entity(valid_raw_api_item)
        assert result is not None
        allowed_keys = {"sport", "registration_year", "province_abbr", "region_code"}
        assert set(result.keys()) == allowed_keys

    def test_no_name_in_output(self, valid_raw_api_item: dict[str, Any]) -> None:
        result = sanitize_entity(valid_raw_api_item)
        assert "name" not in result

    def test_no_address_details_in_output(self, valid_raw_api_item: dict[str, Any]) -> None:
        result = sanitize_entity(valid_raw_api_item)
        assert "address" not in result
        assert "street" not in result
        assert "lat" not in result
        assert "lng" not in result

    def test_no_logo_in_output(self, valid_raw_api_item: dict[str, Any]) -> None:
        result = sanitize_entity(valid_raw_api_item)
        assert "logo" not in result

    def test_sport_as_string_converted_to_list(self) -> None:
        item = {"sport": "nuoto", "address": {"zone": "MI", "region": "LOM"}}
        result = sanitize_entity(item)
        assert result is not None
        assert result["sport"] == ["nuoto"]

    def test_sport_as_list(self) -> None:
        item = {"sport": ["calcio", "basket"], "address": {"zone": "TO", "region": "PIE"}}
        result = sanitize_entity(item)
        assert result is not None
        assert result["sport"] == ["calcio", "basket"]

    def test_missing_sport_returns_none(self) -> None:
        item = {"address": {"zone": "RM", "region": "LAZ"}}
        assert sanitize_entity(item) is None

    def test_missing_zone_returns_none(self) -> None:
        item = {"sport": "calcio", "address": {"region": "LAZ"}}
        assert sanitize_entity(item) is None

    def test_missing_region_returns_none(self) -> None:
        item = {"sport": "calcio", "address": {"zone": "RM"}}
        assert sanitize_entity(item) is None

    def test_missing_address_returns_none(self) -> None:
        item = {"sport": "calcio"}
        assert sanitize_entity(item) is None

    def test_address_not_dict_returns_none(self) -> None:
        item = {"sport": "calcio", "address": "Via Roma 1"}
        assert sanitize_entity(item) is None

    def test_non_dict_input_returns_none(self) -> None:
        assert sanitize_entity("not a dict") is None
        assert sanitize_entity(42) is None
        assert sanitize_entity(None) is None

    def test_sport_invalid_type_returns_none(self) -> None:
        item = {"sport": 123, "address": {"zone": "RM", "region": "LAZ"}}
        assert sanitize_entity(item) is None

    def test_sport_list_with_non_string_returns_none(self) -> None:
        item = {"sport": ["calcio", 123], "address": {"zone": "RM", "region": "LAZ"}}
        assert sanitize_entity(item) is None

    def test_registration_year_preserved_when_present(self) -> None:
        item = {"sport": "calcio", "registrationYear": 2020, "address": {"zone": "RM", "region": "LAZ"}}
        result = sanitize_entity(item)
        assert result["registration_year"] == 2020

    def test_registration_year_none_when_absent(self) -> None:
        item = {"sport": "calcio", "address": {"zone": "RM", "region": "LAZ"}}
        result = sanitize_entity(item)
        assert result["registration_year"] is None
