from __future__ import annotations

import csv
import logging
import time
from typing import Any

from src.config import (
    LOG_LEVEL,
    PLATFORM_COUNTS_CSV,
    PLATFORM_PROCESSED_DIR,
    PLATFORM_QUALITY_DIR,
    PLATFORM_RAW_DIR,
    PROJECT_ROOT,
    REGION_CODE_TO_NAME,
)
from src.utils.input_output import load_json, save_json
from src.utils.logging import configure_logging

configure_logging(LOG_LEVEL)
logger = logging.getLogger(__name__)

RAW_INPUT = PLATFORM_RAW_DIR / "platform_entities.json"
ANALYSIS_CSV_BY_PROVINCE = PLATFORM_COUNTS_CSV
ANALYSIS_JSON_BY_PROVINCE = PLATFORM_PROCESSED_DIR / "platform_entity_counts_by_province.json"
ANALYSIS_CSV_BY_SPORT_PROVINCE = PLATFORM_PROCESSED_DIR / "platform_entity_counts_by_sport_province.csv"
QUALITY_OUTPUT = PLATFORM_QUALITY_DIR / "analysis_dataset_checks.json"


def aggregate_by_province(items: list[dict[str, Any]]) -> list[dict[str, str | int]]:
    """
    Aggregate entities by province, counting occurrences.
    """
    province_counts: dict[str, int] = {}
    province_region: dict[str, str] = {}

    for item in items:
        zone = item.get("province_abbr", "")
        region_code = item.get("region_code", "")

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


def aggregate_by_sport_and_province(items: list[dict[str, Any]]) -> list[dict[str, str | int]]:
    """
    Aggregate entities by (sport, province) pair for sport-level analysis.
    """
    sport_province_counts: dict[tuple[str, str], int] = {}
    province_region: dict[str, str] = {}

    for item in items:
        zone = item.get("province_abbr", "")
        region_code = item.get("region_code", "")
        sport = item.get("sport", [])
        sports = [sport] if isinstance(sport, str) else sport

        if not zone or not sports:
            continue

        if zone not in province_region and region_code:
            province_region[zone] = region_code

        for sport_key in sports:
            key = (sport_key, zone)
            sport_province_counts[key] = sport_province_counts.get(key, 0) + 1

    rows: list[dict[str, str | int]] = []
    for (sport_key, zone) in sorted(sport_province_counts):
        region_code = province_region.get(zone, "")
        rows.append({
            "region_code": region_code,
            "region_name": REGION_CODE_TO_NAME.get(region_code, region_code),
            "province_abbr": zone,
            "sport_key": sport_key,
            "platform_entities": sport_province_counts[(sport_key, zone)],
        })

    return rows


def build_csv(
    rows: list[dict[str, Any]],
    fieldnames: list[str],
    output_path: Any,
) -> None:
    """
    Export rows to CSV.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    """
    Step 02: build analysis-ready datasets from platform entities.

    Produces:
    - CSV/JSON aggregated by province
    - CSV aggregated by sport and province
    - Quality checks report
    """
    logger.info("Starting step_02_build_analysis_dataset")

    data = load_json(RAW_INPUT)

    if not isinstance(data, dict):
        raise ValueError("Invalid platform entities file format: expected dictionary payload.")

    items = data.get("items", [])

    if not isinstance(items, list):
        raise ValueError("Invalid platform entities file format: expected 'items' to be a list.")

    logger.info("Platform entities loaded: %d", len(items))

    # Aggregate by province
    province_rows = aggregate_by_province(items)

    province_fieldnames = ["region_code", "region_name", "province_abbr", "platform_entities"]
    build_csv(province_rows, province_fieldnames, ANALYSIS_CSV_BY_PROVINCE)

    province_json_payload = {
        "generated_at_epoch": int(time.time()),
        "dimension": "platform_entity_counts_by_province",
        "count": len(province_rows),
        "items": province_rows,
    }
    save_json(province_json_payload, ANALYSIS_JSON_BY_PROVINCE)

    # Aggregate by sport and province
    sport_province_rows = aggregate_by_sport_and_province(items)

    sport_province_fieldnames = [
        "region_code", "region_name", "province_abbr", "sport_key", "platform_entities",
    ]
    build_csv(sport_province_rows, sport_province_fieldnames, ANALYSIS_CSV_BY_SPORT_PROVINCE)

    # Quality checks
    unique_provinces = {item.get("province_abbr") for item in items if item.get("province_abbr")}
    unique_sports = set()
    for item in items:
        sport = item.get("sport", [])
        for s in ([sport] if isinstance(sport, str) else sport):
            unique_sports.add(s)

    quality_payload = {
        "generated_at_epoch": int(time.time()),
        "input_file": str(RAW_INPUT.relative_to(PROJECT_ROOT)),
        "dimension": "platform_analysis_dataset_checks",
        "total_entities": len(items),
        "unique_provinces": len(unique_provinces),
        "unique_sports": len(unique_sports),
        "province_rows_count": len(province_rows),
        "sport_province_rows_count": len(sport_province_rows),
    }
    save_json(quality_payload, QUALITY_OUTPUT)

    logger.info("Province rows: %d", len(province_rows))
    logger.info("Sport-province rows: %d", len(sport_province_rows))
    logger.info("Province CSV: %s", ANALYSIS_CSV_BY_PROVINCE)
    logger.info("Province JSON: %s", ANALYSIS_JSON_BY_PROVINCE)
    logger.info("Sport-province CSV: %s", ANALYSIS_CSV_BY_SPORT_PROVINCE)
    logger.info("Quality checks: %s", QUALITY_OUTPUT)


if __name__ == "__main__":
    main()
