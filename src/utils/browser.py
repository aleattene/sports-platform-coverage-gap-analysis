from playwright.sync_api import Page
from typing import Any
import logging

logger = logging.getLogger(__name__)


def handle_cookie_banner(page: Page, wait_ms: int) -> None:
    """
    Attempts to dismiss a cookie banner if present.
    The selectors are generic so the script remains reusable across similar pages.
    """
    reject_candidates = [
        "button:has-text('Rifiuta')",
        "button:has-text('Rifiuta tutti')",
        "button:has-text('Reject')",
        "button:has-text('Reject all')",
    ]

    for selector in reject_candidates:
        try:
            locator = page.locator(selector).first
            if locator.is_visible(timeout=2000):
                locator.click()
                page.wait_for_timeout(wait_ms)
                logger.info("Cookie banner handled with selector: %s", selector)
                return
        except Exception:
            continue

    # Log message displayed if no reject button was found, but continue execution without raising an error
    logger.info("No reject cookie button detected. Continuing execution.")


def extract_select_options(page: Page, select_name: str, placeholder_text: str) -> list[dict[str, str]]:
    """
    Extracts all valid options from a select input.
    :param page: current PW page instance
    :param select_name: HTML name attribute of the target select
    :param placeholder_text: placeholder label to exclude from results
    :return: a list of dictionaries in the form: [{"value": "...", "label": "..."}]
    """
    select_locator = page.locator(f"select[name='{select_name}']").first

    options: list[dict[str, Any]] = select_locator.locator("option").evaluate_all(
        """
        options => options.map(opt => ({
            value: opt.value,
            label: (opt.textContent || '').trim()
        }))
        """
    )

    cleaned = [
        { "value": item["value"], "label": item["label"] }
        for item in options
        if item.get("value")
        and item.get("label")
        and item["label"].strip().lower() != placeholder_text.strip().lower()
    ]

    if not cleaned:
        raise RuntimeError(f"No valid options found for select '{select_name}'")

    return cleaned