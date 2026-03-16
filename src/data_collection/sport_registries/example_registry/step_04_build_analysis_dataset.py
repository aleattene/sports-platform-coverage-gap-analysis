import csv
import logging
import time
from typing import Any

from src.config import LOG_LEVEL, PROCESSED_DIR, QUALITY_DIR, REGISTRY_COUNTS_CSV
from src.utils.input_output import load_json, save_json
from src.utils.logging import configure_logging


configure_logging(LOG_LEVEL)
logger = logging.getLogger(__name__)


COUNTS_INPUT_FILE = PROCESSED_DIR / "entity_counts.json"
ANALYSIS_JSON_FILE = PROCESSED_DIR / "registry_entity_counts_by_province.json"
ANALYSIS_CSV_FILE = REGISTRY_COUNTS_CSV
ANALYSIS_QUALITY_FILE = QUALITY_DIR / "registry_entity_counts_by_province_checks.json"


def build_csv(rows: list[dict[str, Any]]) -> None:
    """
    Export normalized province count rows to CSV.
    """
    fieldnames = [
        "region_id",
        "region_name",
        "province_id",
        "province_name",
        "province_abbr",
        "entities_total",
    ]

    ANALYSIS_CSV_FILE.parent.mkdir(parents=True, exist_ok=True)

    with ANALYSIS_CSV_FILE.open("w", encoding="utf-8", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    """
    Step 04 of the data collection pipeline.

    Objective:
    - load the province counts output from step 03
    - validate rows and remove duplicates if present
    - export analysis-ready JSON and CSV outputs
    - generate quality checks
    """
    logger.info("Starting step_04_build_analysis_dataset")

    data = load_json(COUNTS_INPUT_FILE)

    if not isinstance(data, dict):
        raise ValueError("Invalid province counts file format: expected dictionary payload.")

    items = data.get("items", [])

    if not isinstance(items, list):
        raise ValueError("Invalid province counts file format: expected 'items' to be a list.")

    normalized_rows: list[dict[str, Any]] = []
    unique_keys: set[tuple[Any, ...]] = set()
    quality_rows: list[dict[str, Any]] = []

    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            quality_rows.append(
                {
                    "row_index": index,
                    "status": "invalid_row",
                    "error": "Expected row to be a dictionary.",
                }
            )
            continue

        key = (
            item.get("region_id"),
            item.get("province_id"),
            item.get("province_name"),
        )

        if key in unique_keys:
            quality_rows.append(
                {
                    "row_index": index,
                    "region_name": item.get("region_name"),
                    "province_name": item.get("province_name"),
                    "status": "duplicate_skipped",
                }
            )
            continue

        unique_keys.add(key)
        normalized_rows.append(item)

        quality_rows.append(
            {
                "row_index": index,
                "region_name": item.get("region_name"),
                "province_name": item.get("province_name"),
                "entities_total": item.get("entities_total"),
                "status": "ok",
            }
        )

    analysis_json_payload = {
        "generated_at_epoch": int(time.time()),
        "dimension": "province_entity_counts",
        "count": len(normalized_rows),
        "items": normalized_rows,
    }

    save_json(analysis_json_payload, ANALYSIS_JSON_FILE)
    build_csv(normalized_rows)

    quality_payload = {
        "generated_at_epoch": int(time.time()),
        "input_file": str(COUNTS_INPUT_FILE),
        "dimension": "registry_entity_counts_by_province_quality_checks",
        "count": len(quality_rows),
        "items": quality_rows,
    }

    save_json(quality_payload, ANALYSIS_QUALITY_FILE)

    logger.info("Completed step_04_build_analysis_dataset")
    logger.info("Normalized rows: %s", len(normalized_rows))
    logger.info("Analysis JSON: %s", ANALYSIS_JSON_FILE)
    logger.info("Analysis CSV: %s", ANALYSIS_CSV_FILE)
    logger.info("Quality checks: %s", ANALYSIS_QUALITY_FILE)


if __name__ == "__main__":
    main()
