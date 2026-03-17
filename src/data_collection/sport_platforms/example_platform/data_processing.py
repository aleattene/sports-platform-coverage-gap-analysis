import csv
import logging
from typing import Any

from src.config import LOG_LEVEL, PLATFORM_COUNTS_CSV, PLATFORM_RAW_DIR, REGION_CODE_TO_NAME
from src.utils.input_output import load_json
from src.utils.logging import configure_logging

configure_logging(LOG_LEVEL)
logger = logging.getLogger(__name__)

RAW_INPUT = PLATFORM_RAW_DIR / "platform_coverage.json"
PROCESSED_OUTPUT = PLATFORM_COUNTS_CSV


def aggregate_by_province(entities: list[dict[str, Any]]) -> list[dict[str, str | int]]:
    """
    Aggregate platform entities by province (zone), counting unique entity IDs.
    """
    province_entity_ids: dict[str, set[str]] = {}
    province_region: dict[str, str] = {}

    for entity in entities:
        if not isinstance(entity, dict):
            continue

        address = entity.get("address") or {}
        if not isinstance(address, dict):
            continue

        zone = address.get("zone")
        region_code = address.get("region")
        entity_id = entity.get("organizationId")

        if not zone or not entity_id:
            continue

        province_entity_ids.setdefault(zone, set()).add(entity_id)

        if zone not in province_region and region_code:
            province_region[zone] = region_code

    rows: list[dict[str, str | int]] = []
    for zone in sorted(province_entity_ids):
        region_code = province_region.get(zone, "")
        rows.append({
            "region_code": region_code,
            "region_name": REGION_CODE_TO_NAME.get(region_code, region_code),
            "province_abbr": zone,
            "platform_entities": len(province_entity_ids[zone]),
        })

    return rows


def main() -> None:
    logger.info("Starting platform data processing")

    entities = load_json(RAW_INPUT)

    if not isinstance(entities, list):
        raise ValueError(f"Expected a JSON array in {RAW_INPUT}")

    logger.info("Raw entities loaded: %s", len(entities))

    rows = aggregate_by_province(entities)

    fieldnames = ["region_code", "region_name", "province_abbr", "platform_entities"]

    PROCESSED_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with PROCESSED_OUTPUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logger.info("Processed rows: %s", len(rows))
    logger.info("Output saved: %s", PROCESSED_OUTPUT)


if __name__ == "__main__":
    main()
