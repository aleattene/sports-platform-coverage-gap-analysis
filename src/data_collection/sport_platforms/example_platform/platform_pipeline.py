import logging
from typing import Callable

from src.config import FETCH_PLATFORM_DATA, LOG_LEVEL, PLATFORM_QUALITY_DIR, PLATFORM_RAW_DIR
from src.utils.input_output import save_json
from src.utils.logging import configure_logging
from src.utils.runtime import elapsed_seconds, format_duration, start_timer, utc_now_iso

configure_logging(LOG_LEVEL)
logger = logging.getLogger(__name__)

RAW_INPUT = PLATFORM_RAW_DIR / "platform_entities.json"


def run_step(step_name: str, step_fn: Callable[[], None]) -> dict[str, object]:
    """
    Run a single pipeline step function and measure its execution time.
    """
    step_started_at_utc = utc_now_iso()
    step_timer = start_timer()

    logger.info("Running %s", step_name)

    try:
        step_fn()
        status = "ok"
    except Exception:
        logger.exception("%s failed", step_name)
        status = "failed"

    return {
        "step_name": step_name,
        "started_at_utc": step_started_at_utc,
        "finished_at_utc": utc_now_iso(),
        "duration_seconds": elapsed_seconds(step_timer),
        "status": status,
    }


def main() -> None:
    """
    Run the platform pipeline.

    When FETCH_PLATFORM_DATA=true: fetch fresh data from API, then process.
    When FETCH_PLATFORM_DATA=false (default): process existing raw data only.
    """
    logger.info("Starting platform pipeline (fetch=%s)", FETCH_PLATFORM_DATA)

    pipeline_started_at_utc = utc_now_iso()
    pipeline_timer = start_timer()

    step_runs: list[dict[str, object]] = []
    pipeline_status = "ok"

    # Step 01: fetch from API (only when explicitly enabled)
    if FETCH_PLATFORM_DATA:
        from src.data_collection.sport_platforms.example_platform.step_01_retrieve_entities import (
            main as step_01,
        )

        step_result = run_step("step_01_retrieve_entities", step_01)
        step_runs.append(step_result)

        if step_result["status"] == "failed":
            pipeline_status = "failed"
            logger.error("Pipeline stopping: data retrieval failed")
    else:
        logger.info("Skipping data retrieval (FETCH_PLATFORM_DATA=false)")
        step_runs.append({"step_name": "step_01_retrieve_entities", "status": "skipped"})

    # Step 02: process raw data (always, if raw data exists)
    if pipeline_status != "failed":
        if RAW_INPUT.exists():
            from src.data_collection.sport_platforms.example_platform.step_02_build_analysis_dataset import (
                main as step_02,
            )

            step_result = run_step("step_02_build_analysis_dataset", step_02)
            step_runs.append(step_result)

            if step_result["status"] == "failed":
                pipeline_status = "failed"
        else:
            logger.warning("No raw data found at %s — nothing to process", RAW_INPUT)
            step_runs.append({"step_name": "step_02_build_analysis_dataset", "status": "skipped"})

    pipeline_duration_seconds = elapsed_seconds(pipeline_timer)
    pipeline_duration_hms = format_duration(pipeline_duration_seconds)

    pipeline_summary = {
        "started_at_utc": pipeline_started_at_utc,
        "finished_at_utc": utc_now_iso(),
        "duration_seconds": pipeline_duration_seconds,
        "duration_hms": pipeline_duration_hms,
        "fetch_enabled": FETCH_PLATFORM_DATA,
        "steps_count": len(step_runs),
        "steps": step_runs,
        "status": pipeline_status,
    }

    summary_path = PLATFORM_QUALITY_DIR / "pipeline_run_summary.json"
    save_json(pipeline_summary, summary_path)

    logger.info("Pipeline %s", pipeline_status)
    logger.info("Summary: %s", summary_path)
    logger.info("Total duration: %s (%s seconds)", pipeline_duration_hms, pipeline_duration_seconds)

    if pipeline_status == "failed":
        raise RuntimeError("Platform pipeline failed")


if __name__ == "__main__":
    main()
