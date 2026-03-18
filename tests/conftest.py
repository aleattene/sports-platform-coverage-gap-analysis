"""
Shared fixtures for the test suite.

Fixtures defined here are automatically available to all tests
without explicit imports — pytest discovers conftest.py files
by walking up the directory tree from each test file.
"""

import os
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Safe defaults for environment variables required by src.config at import time.
# Without these, importing any src.* module in a clean environment (CI, fresh
# clone) would raise ValueError because SOURCE_URL is required and the
# SOURCE_*_SELECT_NAME / SOURCE_*_TASK_KEY variables are validated non-empty.
# ---------------------------------------------------------------------------
_CONFIG_DEFAULTS: dict[str, str] = {
    "SOURCE_URL": "https://test.example.com",
    "SOURCE_REGION_SELECT_NAME": "test_region",
    "SOURCE_PROVINCE_SELECT_NAME": "test_province",
    "SOURCE_PROVINCES_TASK_KEY": "test_task_key",
}

for key, value in _CONFIG_DEFAULTS.items():
    os.environ.setdefault(key, value)


# ---------------------------------------------------------------------------
# Platform entity fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def valid_raw_api_item() -> dict[str, Any]:
    """A raw API item as received from the platform endpoint (before sanitization)."""
    return {
        "name": "Test Entity Alpha",
        "sport": ["calcio"],
        "registrationYear": 2023,
        "address": {
            "street": "Via Roma 1",
            "zone": "RM",
            "region": "LAZ",
            "lat": 41.9,
            "lng": 12.5,
        },
        "logo": "https://example.com/logo.png",
    }


@pytest.fixture
def sanitized_entity() -> dict[str, Any]:
    """A platform entity after sanitization (only analysis-relevant fields)."""
    return {
        "sport": ["calcio"],
        "registration_year": 2023,
        "province_abbr": "RM",
        "region_code": "LAZ",
    }


@pytest.fixture
def sample_platform_items(sanitized_entity: dict[str, Any]) -> list[dict[str, Any]]:
    """A small list of sanitized platform entities for aggregation tests."""
    return [
        sanitized_entity,
        {
            "sport": ["nuoto"],
            "registration_year": 2022,
            "province_abbr": "RM",
            "region_code": "LAZ",
        },
        {
            "sport": ["calcio", "basket"],
            "registration_year": 2021,
            "province_abbr": "MI",
            "region_code": "LOM",
        },
    ]


@pytest.fixture
def sample_raw_payload(
    sample_platform_items: list[dict[str, Any]],
) -> dict[str, Any]:
    """A complete raw payload as produced by platform step_01."""
    return {
        "dimension": "platform_entities",
        "retrieved_at": "20240315_143022",
        "count": len(sample_platform_items),
        "items": sample_platform_items,
    }


# ---------------------------------------------------------------------------
# Registry entity fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_registry_items() -> list[dict[str, Any]]:
    """Registry province count rows as produced by step_03."""
    return [
        {
            "region_id": "12",
            "region_name": "Lazio",
            "province_id": "058",
            "province_name": "Roma",
            "province_abbr": "RM",
            "entities_total": 1500,
        },
        {
            "region_id": "03",
            "region_name": "Lombardia",
            "province_id": "015",
            "province_name": "Milano",
            "province_abbr": "MI",
            "entities_total": 2000,
        },
    ]


@pytest.fixture
def sample_registry_payload(
    sample_registry_items: list[dict[str, Any]],
) -> dict[str, Any]:
    """A complete registry_entity_counts_by_province.json payload as produced by step_03."""
    return {
        "generated_at_epoch": 1710511822,
        "dimension": "province_entity_counts",
        "count": len(sample_registry_items),
        "items": sample_registry_items,
    }
