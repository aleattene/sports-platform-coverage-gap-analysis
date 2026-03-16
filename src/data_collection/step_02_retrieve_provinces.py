import logging
from pathlib import Path
from typing import Any

from playwright.sync_api import Locator, Page, sync_playwright

from src.config import (
    LOG_LEVEL,
    PWT_BETWEEN_REQUESTS_MS,
    PWT_COOKIE_WAIT_MS,
    PWT_HEADLESS,
    PWT_POST_LOAD_WAIT_MS,
    PWT_SLOW_MO,
    PWT_TIMEOUT_MS,
    PROVINCES_DIR,
    QUALITY_DIR,
    REGIONS_DIR,
    SOURCE_PROVINCES_TASK_KEY,
    SOURCE_REGION_SELECT_NAME,
    SOURCE_URL,
)
from src.utils.browser import handle_cookie_banner
from src.utils.input_output import load_json, save_json
from src.utils.logging import configure_logging
from src.utils.strings import slugify

configure_logging(LOG_LEVEL)
logger = logging.getLogger(__name__)

def load_regions(regions_filepath: Path) -> list[dict[str, Any]]:
    """
    Load previously saved regions data from a JSON file.
    Expected structure:
    {
        "source": "...",
        "dimension": "regions",
        "count": ...,
        "items": [...]
    }
    :param regions_filepath: path to the regions JSON file
    :return: list of regions, each as a dict with "value" and "label" keys
    """
    data = load_json(regions_filepath)

    # Support both {"items": [...]} and [...] formats
    if isinstance(data, dict) and "items" in data:
        regions = data["items"]
    elif isinstance(data, list):
        regions = data
    else:
        raise ValueError("Unsupported regions file format.")

    # Check if the regions list is empty and raise an error if so
    if not regions:
        raise ValueError("Regions file is empty.")

    # Check that each region is a dict with "value" and "label" keys
    for idx, region in enumerate(regions, start=1):
        if not isinstance(region, dict):
            raise ValueError(f"Region at position {idx} is not a dictionary.")

        if "value" not in region or "label" not in region:
            raise ValueError(
                f"Region at position {idx} must contain 'value' and 'label' keys."
            )
    # Return the list of regions loaded from the file
    return regions


def find_region_select(page: Page) -> Locator:
    """
    Attempts to find the region select element using first a specific selector, then falling back to more generic ones.
    :param page: current PW page instance
    :return: locator of the found select element
    """
    candidate_selectors = [
        f"select[name='{SOURCE_REGION_SELECT_NAME}']",
        f"select#{SOURCE_REGION_SELECT_NAME}",
        "select[name*='regione']",
        "select[id*='regione']",
        "select[name*='region']",
        "select[id*='region']",
    ]

    for selector in candidate_selectors:
        # Use .first to avoid issues if multiple elements match the selector, but we only care about the first one
        locator = page.locator(selector).first
        try:
            if locator.is_visible(timeout=2000):
                logger.info("Region select found with selector: %s", selector)
                return locator
        except Exception:
            continue

    # No visible select found with any of the candidate selectors
    raise RuntimeError("No visible region select found on source page.")


def normalize_province_payload(
        region: dict[str, Any],
        payload: list[dict[str, Any]]
    ) -> dict[str, Any]:
    """
    Normalizes the raw payload of provinces for a given region into a consistent structure.
    Expected input payload is a list of items with keys like "codR", "nomeR", "codP", "nomeP", "siglaP".
    :param region: dictionary with "value" and "label" keys representing the region
    :param payload: list of raw province items as returned by the source endpoint
    :return: a dictionary with normalized structure:
    """
    # Check that region dictionary contains "value" and "label" keys
    if "value" not in region or "label" not in region:
        raise ValueError("Region must contain 'value' and 'label' keys.")

    # Normalize each item in the payload to have consistent keys and structure
    # from { "codR": ..., "nomeR": ..., "codP": ..., "nomeP": ..., "siglaP": ... }
    # to { "region_id": ..., "region_name": ..., "province_id": ..., "province_name": ..., "province_abbr": ... }
    cleaned_items = [
        {
            "region_id": item.get("codR"),
            "region_name": item.get("nomeR"),
            "province_id": item.get("codP"),
            "province_name": item.get("nomeP"),
            "province_abbr": item.get("siglaP"),
        }
        for item in payload
    ]

    # Return the normalized data in a consistent structure, for example:
    # {
    #   "source": "public_source", "dimension": "provinces", "region_id": ..., "region_name": ..., "count": ...,
    #   "items": [
    #       { "region_id": ..., "region_name": ..., "province_id": ..., "province_name": ..., "province_abbr": ... }
    #       { ... }
    #    ]
    #  }
    return {
        "dimension": "provinces",
        "region_id": int(region["value"]),
        "region_name": region["label"],
        "count": len(cleaned_items),
        "items": cleaned_items,
    }


def save_region_provinces(region: dict[str, Any], payload: list[dict[str, Any]]) -> Path:
    """
    Save a region's provinces data to a dedicated JSON file with a consistent structure.
    :param region: dictionary with "value" and "label" keys representing the region
    :param payload: list of raw province items as returned by the source endpoint
    :return: path to the saved JSON file
    """
    # Normalize the raw payload into a consistent structure
    output_data = normalize_province_payload(region, payload)
    # Generate a slugified filename based on the region label to ensure it's filesystem-friendly
    output_path = PROVINCES_DIR / f"{slugify(region['label'])}.json"
    # Save the normalized data to the output JSON file
    save_json(output_data, output_path)
    # Return the path to the saved file for reference, logging and quality checks
    return output_path


def main() -> None:
    """
    Step 02 of the data collection pipeline.
    Objective:
    - load regions from step 01 output
    - open the configured source page
    - iterate through regions
    - retrieve provinces for each region
    - save one JSON file per region
    - store quality checks
    """
    logger.info("Starting step_02_retrieve_provinces")

    regions_file = REGIONS_DIR / "regions.json"
    regions = load_regions(regions_file)

    quality_rows: list[dict[str, Any]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=PWT_HEADLESS, slow_mo=PWT_SLOW_MO)
        context = browser.new_context()

        try:
            page = context.new_page()
            logger.info("Opening source page")
            page.goto(SOURCE_URL, wait_until="domcontentloaded", timeout=PWT_TIMEOUT_MS)
            page.wait_for_timeout(PWT_POST_LOAD_WAIT_MS)

            handle_cookie_banner(page, PWT_COOKIE_WAIT_MS)

            region_select = find_region_select(page)

            total_regions = len(regions)

            for idx, region in enumerate(regions, start=1):
                region_name = region["label"]
                region_value = region["value"]

                logger.info(
                    "Processing region %s/%s: %s (%s)",
                    idx,
                    total_regions,
                    region_name,
                    region_value,
                )

                try:
                    with page.expect_response(
                            lambda res: f"task={SOURCE_PROVINCES_TASK_KEY}" in res.url and
                                             res.status == 200,
                            timeout=PWT_TIMEOUT_MS,
                    ) as response_info:
                        region_select.select_option(value=str(region_value))

                    response = response_info.value
                    payload = response.json()

                    if not isinstance(payload, list):
                        raise ValueError(f"Unexpected provinces payload format for region {region_name}")

                    output_path = save_region_provinces(region, payload)

                    quality_rows.append(
                        {
                            "region_id": region_value,
                            "region_name": region_name,
                            "count": len(payload),
                            "status": "ok",
                        }
                    )

                    logger.info("Retrieved %s provinces for %s", len(payload), region_name)
                    logger.info("Saved provinces file: %s", output_path)

                    page.wait_for_timeout(PWT_BETWEEN_REQUESTS_MS)

                except Exception as exc:
                    logger.exception("Failed retrieving provinces for region %s", region_name)
                    quality_rows.append(
                        {
                            "region_id": region_value,
                            "region_name": region_name,
                            "count": 0,
                            "status": "failed",
                            "error": str(exc),
                        }
                    )

            logger.info("Completed step_02_retrieve_provinces")

        finally:
            quality_payload = {
                "dimension": "provinces_quality_checks",
                "count": len(quality_rows),
                "items": quality_rows,
            }
            quality_output = QUALITY_DIR / "provinces_checks.json"
            save_json(quality_payload, quality_output)
            logger.info("Saved quality checks: %s", quality_output)

            context.close()
            browser.close()


if __name__ == "__main__":
    main()