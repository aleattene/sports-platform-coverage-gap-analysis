from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from src.config import (
    LOG_LEVEL,
    PLATFORM_BASE_URL,
    PLATFORM_MAX_RETRIES,
    PLATFORM_ORGS_ENDPOINT,
    PLATFORM_RAW_DIR,
    PLATFORM_REQUEST_DELAY_S,
    PLATFORM_REQUEST_TIMEOUT_S,
    PROJECT_ROOT,
    PLATFORM_QUALITY_DIR,
)
from src.utils.http_client import create_client, fetch_json_with_retry
from src.utils.input_output import save_json
from src.utils.logging import configure_logging

configure_logging(LOG_LEVEL)
logger = logging.getLogger(__name__)

RAW_OUTPUT = PLATFORM_RAW_DIR / "platform_entities.json"
QUALITY_OUTPUT = PLATFORM_QUALITY_DIR / "entities_retrieval_checks.json"


def sanitize_entity(raw_item: Any) -> dict[str, Any] | None:
    """
    Extract only analysis-relevant fields from a raw entity object.

    Validates presence of mandatory fields (sport, address.zone, address.region).
    Returns None if validation fails.
    """
    if not isinstance(raw_item, dict):
        return None

    address = raw_item.get("address")
    if not isinstance(address, dict):
        return None

    raw_sport: Any = raw_item.get("sport")
    zone: str | None = address.get("zone")
    region: str | None = address.get("region")

    if not raw_sport or not zone or not region:
        return None

    sport: list[str] = [raw_sport] if isinstance(raw_sport, str) else raw_sport

    return {
        "sport": sport,
        "registration_year": raw_item.get("registrationYear"),
        "province_abbr": zone,
        "region_code": region,
    }


def main() -> None:
    """
    Step 01: retrieve entities from the platform API and sanitize for privacy.

    Only analysis-relevant fields are extracted and saved.
    No sensitive data (names, logos, coordinates, addresses) is written to disk.
    """
    logger.info("Starting step_01_retrieve_entities")

    if not PLATFORM_BASE_URL:
        raise ValueError("PLATFORM_BASE_URL must be set to run the platform pipeline.")
    if not PLATFORM_ORGS_ENDPOINT:
        raise ValueError("PLATFORM_ORGS_ENDPOINT must be set to run the platform pipeline.")

    url = f"{PLATFORM_BASE_URL.rstrip('/')}/{PLATFORM_ORGS_ENDPOINT.lstrip('/')}"

    client = create_client(timeout_s=PLATFORM_REQUEST_TIMEOUT_S)
    try:
        raw_items = fetch_json_with_retry(
            client=client,
            url=url,
            max_retries=PLATFORM_MAX_RETRIES,
            base_delay_s=PLATFORM_REQUEST_DELAY_S,
        )
    finally:
        client.close()

    if not isinstance(raw_items, list):
        raise ValueError("Expected a JSON array from the entities endpoint.")

    logger.info("Raw entities received: %d", len(raw_items))

    selected: list[dict[str, Any]] = []
    skipped = 0

    for item in raw_items:
        result = sanitize_entity(item)
        if result is not None:
            selected.append(result)
        else:
            skipped += 1

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    raw_payload = {
        "dimension": "platform_entities",
        "retrieved_at": timestamp,
        "count": len(selected),
        "items": selected,
    }

    save_json(raw_payload, RAW_OUTPUT)

    quality_payload = {
        "retrieved_at": timestamp,
        "dimension": "entities_retrieval_checks",
        "raw_count": len(raw_items),
        "selected_count": len(selected),
        "skipped_count": skipped,
        "output_file": str(RAW_OUTPUT.relative_to(PROJECT_ROOT)),
    }

    save_json(quality_payload, QUALITY_OUTPUT)

    logger.info("Curated entities: %d (skipped: %d)", len(selected), skipped)
    logger.info("Output saved: %s", RAW_OUTPUT)
    logger.info("Quality checks: %s", QUALITY_OUTPUT)


if __name__ == "__main__":
    main()
