from __future__ import annotations

import logging
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def create_client(timeout_s: int = 30) -> httpx.Client:
    """
    Create an httpx client with appropriate headers and timeout.
    """
    return httpx.Client(
        headers={
            "Accept": "application/json",
            "User-Agent": "sports-coverage-analysis/1.0 (data-research)",
        },
        timeout=httpx.Timeout(timeout_s),
        follow_redirects=True,
    )


def fetch_json_with_retry(
    client: httpx.Client,
    url: str,
    max_retries: int = 3,
    base_delay_s: int = 10,
) -> Any:
    """
    Fetch JSON from a URL with retry and exponential backoff.
    """
    for attempt in range(1, max_retries + 1):
        try:
            logger.info("GET %s (attempt %d/%d)", url, attempt, max_retries)
            response = client.get(url)
            response.raise_for_status()
            data = response.json()
            logger.info("Response OK — %d items", len(data) if isinstance(data, list) else 1)
            return data
        except (httpx.HTTPStatusError, httpx.RequestError) as exc:
            logger.warning("Attempt %d/%d failed: %s", attempt, max_retries, exc)
            if attempt == max_retries:
                raise
            delay = base_delay_s * (2 ** (attempt - 1))
            logger.info("Retrying in %d seconds", delay)
            time.sleep(delay)

    raise RuntimeError("Unreachable: retry loop exited without return or raise")
