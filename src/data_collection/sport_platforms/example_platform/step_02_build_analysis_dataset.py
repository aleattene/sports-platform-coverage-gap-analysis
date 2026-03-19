import csv
import logging
import time
from pathlib import Path
from typing import Any

from src.config import (
    LOG_LEVEL,
    PLATFORM_COUNTS_CSV,
    PLATFORM_PROCESSED_DIR,
    PLATFORM_RAW_DIR,
    REGION_CODE_TO_NAME,
)
from src.utils.input_output import load_json, save_json
from src.utils.logging import configure_logging

configure_logging(LOG_LEVEL)
logger = logging.getLogger(__name__)

RAW_INPUT = PLATFORM_RAW_DIR / "platform_entities.json"
ANALYSIS_CSV_BY_PROVINCE = PLATFORM_COUNTS_CSV
ANALYSIS_JSON_BY_PROVINCE = PLATFORM_PROCESSED_DIR / "platform_entity_counts_by_province.json"


def aggregate_by_province(items: list[dict[str, Any]]) -> list[dict[str, str | int]]:
    """
    Aggregate entities by province, counting occurrences.
    """
    province_counts: dict[str, int] = {}
    province_region: dict[str, str] = {}

    for item in items:
        zone: str = item.get("province_abbr", "")
        region_code: str = item.get("region_code", "")

        if not zone:
            continue

        province_counts[zone] = province_counts.get(zone, 0) + 1

        if zone not in province_region and region_code:
            province_region[zone] = region_code

    rows: list[dict[str, str | int]] = []
    for zone in sorted(province_counts):
        region_code = province_region.get(zone, "")
        rows.append({
            "region_code": region_code,
            "region_name": REGION_CODE_TO_NAME.get(region_code, region_code),
            "province_abbr": zone,
            "platform_entities": province_counts[zone],
        })

    return rows


def build_csv(
    rows: list[dict[str, Any]],
    fieldnames: list[str],
    output_path: Path,
) -> None:
    """
    Export rows to CSV.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer: csv.DictWriter[str] = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    """
    Step 02: build analysis-ready datasets from platform entities.

    Produces:
    - CSV aggregated by province
    - JSON aggregated by province
    """
    logger.info("Starting step_02_build_analysis_dataset")

    data: Any = load_json(RAW_INPUT)

    if not isinstance(data, dict):
        raise ValueError("Invalid platform entities file format: expected dictionary payload.")

    items: list[dict[str, Any]] = data.get("items", [])

    if not isinstance(items, list):
        raise ValueError("Invalid platform entities file format: expected 'items' to be a list.")

    logger.info("Platform entities loaded: %d", len(items))

    # Aggregate by province
    province_rows: list[dict[str, str | int]] = aggregate_by_province(items)

    province_fieldnames: list[str] = ["region_code", "region_name", "province_abbr", "platform_entities"]
    build_csv(province_rows, province_fieldnames, ANALYSIS_CSV_BY_PROVINCE)

    province_json_payload: dict[str, Any] = {
        "generated_at_epoch": int(time.time()),
        "dimension": "platform_entity_counts_by_province",
        "count": len(province_rows),
        "items": province_rows,
    }
    save_json(province_json_payload, ANALYSIS_JSON_BY_PROVINCE)

    logger.info("Province rows: %d", len(province_rows))
    logger.info("Province CSV: %s", ANALYSIS_CSV_BY_PROVINCE)
    logger.info("Province JSON: %s", ANALYSIS_JSON_BY_PROVINCE)


if __name__ == "__main__":
    main()
