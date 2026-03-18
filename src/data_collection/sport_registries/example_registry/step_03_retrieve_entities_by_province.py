import logging
import random
import time
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

from src.config import (
    DEV_MODE,
    DEV_SAMPLE_PROVINCES_PER_REGION,
    DEV_SAMPLE_REGIONS,
    LOG_LEVEL,
    MAX_PROVINCE_RETRIES,
    PROCESSED_DIR,
    PROVINCES_DIR,
    PWT_BETWEEN_REQUESTS_MS,
    PWT_COOKIE_WAIT_MS,
    PWT_HEADLESS,
    PWT_POST_LOAD_WAIT_MS,
    PWT_SLOW_MO,
    PWT_TIMEOUT_MS,
    QUALITY_DIR,
    SOURCE_PROVINCE_SELECT_NAME,
    SOURCE_PROVINCES_TASK_KEY,
    SOURCE_REGION_SELECT_NAME,
    SOURCE_URL,
    WAIT_AFTER_SEARCH_MS,
    WAIT_AFTER_SELECT_MS,
    WAIT_RETRY_MS,
)
from src.utils.browser import handle_cookie_banner
from src.utils.input_output import load_json, save_json
from src.utils.logging import configure_logging


configure_logging(LOG_LEVEL)
logger = logging.getLogger(__name__)

COUNTS_OUTPUT_FILE = PROCESSED_DIR / "registry_entity_counts_by_province.json"
QUALITY_OUTPUT_FILE = QUALITY_DIR / "entity_counts_checks.json"


def load_province_files(provinces_dir: Path) -> list[Path]:
    """
    Load all province JSON files produced in step 02 from the configured directory.
    :param provinces_dir: directory path where province JSON files are stored
    :return: list of Path objects for each province JSON file
    """
    files = sorted(provinces_dir.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No province files found in: {provinces_dir}")
    return files


def collect_all_provinces() -> list[dict[str, Any]]:
    """
    Build a flat list of all provinces from step 02 outputs.
    When DEV_MODE is enabled, randomly samples a subset of regions and
    provinces per region to minimize server load during development.
    """
    province_files = load_province_files(PROVINCES_DIR)

    regions_data: list[tuple[str, list[dict[str, Any]]]] = []

    for province_file in province_files:
        payload = load_json(province_file)

        if not isinstance(payload, dict):
            raise ValueError(f"Invalid province file format: {province_file}")

        region_name = payload.get("region_name")
        region_id = payload.get("region_id")
        provinces = payload.get("items", [])

        if not region_name or not region_id:
            raise ValueError(f"Missing region metadata in file: {province_file}")

        if not isinstance(provinces, list):
            raise ValueError(f"Invalid provinces list in file: {province_file}")

        province_rows = []
        for province in provinces:
            if not isinstance(province, dict):
                raise ValueError(f"Invalid province row in file: {province_file}")

            province_id = province.get("province_id")
            province_name = province.get("province_name")

            if not province_id or not province_name:
                raise ValueError(
                    f"Province row missing required fields in file: {province_file}"
                )

            province_rows.append(
                {
                    "region_id": region_id,
                    "region_name": region_name,
                    "province_id": province_id,
                    "province_name": province_name,
                    "province_abbr": province.get("province_abbr"),
                }
            )

        regions_data.append((region_name, province_rows))

    if DEV_MODE:
        sampled_regions = random.sample(
            regions_data, min(DEV_SAMPLE_REGIONS, len(regions_data))
        )
        rows: list[dict[str, Any]] = []
        for region_name, province_rows in sampled_regions:
            sampled_provinces = random.sample(
                province_rows,
                min(DEV_SAMPLE_PROVINCES_PER_REGION, len(province_rows)),
            )
            rows.extend(sampled_provinces)
            logger.info(
                "DEV_MODE: sampled %s/%s provinces from %s",
                len(sampled_provinces),
                len(province_rows),
                region_name,
            )
        return rows

    all_rows: list[dict[str, Any]] = []
    for _, province_rows in regions_data:
        all_rows.extend(province_rows)
    return all_rows


def extract_total_results(page: Page) -> int | None:
    """
    Extract the total number of results from the page DOM.
    The expected format is a number contained in an element with class "n-risultati".
    :param page: current PW page instance
    :return: the total number of results as an integer, or None if it cannot be determined
    """
    candidate_selectors = [
        "span.n-risultati",
        "div.risultati span.n-risultati",
    ]

    for selector in candidate_selectors:
        locator = page.locator(selector).first
        try:
            if locator.is_visible(timeout=5000):
                raw_text = locator.inner_text(timeout=5000).strip()
                digits_only = "".join(ch for ch in raw_text if ch.isdigit())
                if digits_only:
                    return int(digits_only)
        except Exception:
            continue

    return None


def normalize_count_row(
    region_row: dict[str, Any],
    total_results: int,
) -> dict[str, Any]:
    """
    Normalize a single province count row.
    """
    return {
        "region_id": region_row["region_id"],
        "region_name": region_row["region_name"],
        "province_id": region_row["province_id"],
        "province_name": region_row["province_name"],
        "province_abbr": region_row.get("province_abbr"),
        "entities_total": total_results,
    }


def run_single_province_count(
    page: Page,
    region_name: str,
    province_name: str,
) -> int:
    """
    Run the search flow for a single province and return the total number of results.
    """
    logger.info("Starting province count retrieval: %s / %s", region_name, province_name)

    region_select = page.locator(f"select[name='{SOURCE_REGION_SELECT_NAME}']").first

    with page.expect_response(
        lambda response: f"task={SOURCE_PROVINCES_TASK_KEY}" in response.url and response.status == 200,
        timeout=PWT_TIMEOUT_MS,
    ):
        region_select.select_option(label=region_name)

    page.wait_for_timeout(WAIT_AFTER_SELECT_MS)

    province_select = page.locator(f"select[name='{SOURCE_PROVINCE_SELECT_NAME}']").first
    province_select.select_option(label=province_name)

    page.wait_for_timeout(WAIT_AFTER_SELECT_MS)

    search_button = page.locator("button:has-text('Avvia la ricerca')").first
    search_button.click()

    page.wait_for_load_state("domcontentloaded", timeout=PWT_TIMEOUT_MS)
    page.wait_for_timeout(WAIT_AFTER_SEARCH_MS)

    total_results = extract_total_results(page)

    if total_results is None:
        raise RuntimeError(
            f"Unable to determine total results for {region_name}/{province_name}"
        )

    logger.info(
        "Retrieved total results for %s / %s: %s",
        region_name,
        province_name,
        total_results,
    )

    return total_results


def run_province_with_retry(
    context: Any,
    region_name: str,
    province_name: str,
) -> int:
    """
    Run run_single_province_count with retry and exponential backoff.
    Each attempt opens a fresh page to avoid stale DOM state.
    """
    last_exc: Exception | None = None

    for attempt in range(1, MAX_PROVINCE_RETRIES + 1):
        page = context.new_page()
        try:
            page.goto(
                SOURCE_URL,
                wait_until="domcontentloaded",
                timeout=PWT_TIMEOUT_MS,
            )
            page.wait_for_timeout(PWT_POST_LOAD_WAIT_MS)
            handle_cookie_banner(page, PWT_COOKIE_WAIT_MS)

            result = run_single_province_count(
                page=page,
                region_name=region_name,
                province_name=province_name,
            )
            page.close()
            return result

        except Exception as exc:
            last_exc = exc
            page.close()

            if attempt < MAX_PROVINCE_RETRIES:
                backoff_s = (WAIT_RETRY_MS / 1000) * (2 ** (attempt - 1))
                logger.warning(
                    "Attempt %s/%s failed for %s / %s: %s — retrying in %.1fs",
                    attempt,
                    MAX_PROVINCE_RETRIES,
                    region_name,
                    province_name,
                    exc,
                    backoff_s,
                )
                time.sleep(backoff_s)
            else:
                logger.error(
                    "All %s attempts failed for %s / %s",
                    MAX_PROVINCE_RETRIES,
                    region_name,
                    province_name,
                )

    if last_exc is not None:
        raise last_exc
    raise RuntimeError(f"No retry attempts executed for {region_name} / {province_name}")


def main() -> None:
    """
    Step 03 of the data collection pipeline.
    Objective:
    - load provinces from step 02 output files
    - iterate through all provinces (or a random sample in DEV_MODE)
    - retrieve the total number of entities for each province
    - save a JSON file with the counts
    - produce a quality report
    """
    logger.info("Starting step_03_retrieve_province_entity_counts")

    if DEV_MODE:
        logger.info(
            "DEV_MODE enabled: sampling %s regions, %s provinces per region",
            DEV_SAMPLE_REGIONS,
            DEV_SAMPLE_PROVINCES_PER_REGION,
        )

    provinces = collect_all_provinces()
    logger.info("Total provinces to process: %s", len(provinces))

    count_rows: list[dict[str, Any]] = []
    quality_rows: list[dict[str, Any]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=PWT_HEADLESS, slow_mo=PWT_SLOW_MO)
        context = browser.new_context()

        try:
            total_provinces = len(provinces)

            for province_index, province_row in enumerate(provinces, start=1):
                region_name = province_row["region_name"]
                province_name = province_row["province_name"]

                logger.info(
                    "Processing province %s/%s: %s / %s",
                    province_index,
                    total_provinces,
                    region_name,
                    province_name,
                )

                try:
                    total_results = run_province_with_retry(
                        context=context,
                        region_name=region_name,
                        province_name=province_name,
                    )

                    count_row = normalize_count_row(
                        region_row=province_row,
                        total_results=total_results,
                    )
                    count_rows.append(count_row)

                    quality_rows.append(
                        {
                            "region_name": region_name,
                            "province_name": province_name,
                            "entities_total": total_results,
                            "status": "ok",
                        }
                    )

                except Exception as exc:
                    quality_rows.append(
                        {
                            "region_name": region_name,
                            "province_name": province_name,
                            "entities_total": None,
                            "status": "failed",
                            "error": str(exc),
                        }
                    )
                    logger.exception(
                        "Province count retrieval failed for %s / %s",
                        region_name,
                        province_name,
                    )

                if province_index < total_provinces:
                    time.sleep(PWT_BETWEEN_REQUESTS_MS / 1000)

            logger.info("Completed step_03_retrieve_province_entity_counts")

        finally:
            counts_payload = {
                "generated_at_epoch": int(time.time()),
                "dimension": "province_entity_counts",
                "count": len(count_rows),
                "items": count_rows,
            }
            save_json(counts_payload, COUNTS_OUTPUT_FILE)

            quality_payload = {
                "dimension": "province_counts_quality_checks",
                "count": len(quality_rows),
                "items": quality_rows,
            }
            save_json(quality_payload, QUALITY_OUTPUT_FILE)

            logger.info("Saved province counts output: %s", COUNTS_OUTPUT_FILE)
            logger.info("Saved quality checks: %s", QUALITY_OUTPUT_FILE)

            context.close()
            browser.close()


if __name__ == "__main__":
    main()
