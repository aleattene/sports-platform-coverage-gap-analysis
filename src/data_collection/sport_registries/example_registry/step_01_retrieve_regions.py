import logging
import random

from playwright.sync_api import sync_playwright

from src.config import (
    DEV_MODE,
    DEV_SAMPLE_REGIONS,
    LOG_LEVEL,
    PWT_COOKIE_WAIT_MS,
    PWT_HEADLESS,
    PWT_POST_LOAD_WAIT_MS,
    PWT_SLOW_MO,
    PWT_TIMEOUT_MS,
    REGIONS_DIR,
    SOURCE_REGION_SELECT_NAME,
    SOURCE_URL,
)
from src.utils.browser import extract_select_options, handle_cookie_banner
from src.utils.input_output import save_json
from src.utils.logging import configure_logging

configure_logging(LOG_LEVEL)
logger = logging.getLogger(__name__)

EXPECTED_REGIONS_COUNT = 20


def main() -> None:
    """
    Step 01 of the data collection pipeline.
    Objective:
    - open the source page
    - dismiss the cookie banner if present
    - retrieve the list of available regions
    - in DEV_MODE, save only a random sample of N regions
    - store the extracted data as JSON in the defined output directory
    """
    logger.info("Starting step_01_retrieve_regions")

    if DEV_MODE:
        logger.info("DEV_MODE enabled: will sample %s regions", DEV_SAMPLE_REGIONS)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=PWT_HEADLESS, slow_mo=PWT_SLOW_MO)
        context = browser.new_context()

        try:
            page = context.new_page()

            logger.info("Opening source page")
            page.goto(
                SOURCE_URL,
                wait_until="domcontentloaded",
                timeout=PWT_TIMEOUT_MS,
            )

            page.wait_for_timeout(PWT_POST_LOAD_WAIT_MS)

            handle_cookie_banner(page, PWT_COOKIE_WAIT_MS)

            regions = extract_select_options(
                page=page,
                select_name=SOURCE_REGION_SELECT_NAME,
                placeholder_text="scegli la regione",
            )

            if len(regions) != EXPECTED_REGIONS_COUNT:
                logger.warning(
                    "Unexpected number of regions: %s (expected %s)",
                    len(regions),
                    EXPECTED_REGIONS_COUNT,
                )

            if DEV_MODE:
                regions = random.sample(
                    regions, min(DEV_SAMPLE_REGIONS, len(regions))
                )
                logger.info(
                    "DEV_MODE: sampled %s regions: %s",
                    len(regions),
                    [r["label"] for r in regions],
                )

            payload = {
                "dimension": "regions",
                "count": len(regions),
                "items": regions,
            }

            output_path = REGIONS_DIR / "regions.json"
            save_json(payload, output_path)
            logger.info("Output saved to %s", output_path)

            logger.info("Retrieved %s regions", len(regions))
            logger.info("Completed step_01_retrieve_regions.")
        except Exception as exc:
            logger.exception("Step 01 failed: %s", exc)
            raise
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()