import logging

from src.config import DEV_MODE, LOG_LEVEL, PLATFORM_RAW_DIR, QUALITY_DIR
from src.data_collection.sport_platforms.example_platform.data_processing import (
    main as run_platform_processing,
)
from src.data_collection.sport_registries.example_registry.registry_pipeline import (
    main as run_registry_pipeline,
)
from src.utils.input_output import save_json
from src.utils.logging import configure_logging
from src.utils.runtime import elapsed_seconds, format_duration, start_timer, utc_now_iso

configure_logging(LOG_LEVEL)
logger = logging.getLogger(__name__)

PLATFORM_RAW_INPUT = PLATFORM_RAW_DIR / "platform_coverage.json"


def main() -> None:
    logger.info("Starting project pipeline")

    if DEV_MODE:
        logger.info("DEV_MODE enabled")

    pipeline_started_at_utc = utc_now_iso()
    pipeline_timer = start_timer()

    step_runs: list[dict[str, object]] = []
    pipeline_status = "ok"

    # --- Step 1: Registry pipeline ---
    step_started_at_utc = utc_now_iso()
    step_timer = start_timer()
    try:
        logger.info("Running registry pipeline")
        run_registry_pipeline()
        status = "ok"
    except Exception:
        logger.exception("Registry pipeline failed")
        status = "failed"
        pipeline_status = "failed"

    step_runs.append({
        "step_name": "registry_pipeline",
        "started_at_utc": step_started_at_utc,
        "duration_seconds": elapsed_seconds(step_timer),
        "status": status,
    })

    if pipeline_status == "failed":
        logger.error("Pipeline stopping after registry failure")
    else:
        # --- Step 2: Platform data processing (static) ---
        step_started_at_utc = utc_now_iso()
        step_timer = start_timer()

        if PLATFORM_RAW_INPUT.exists():
            try:
                logger.info("Running platform data processing")
                run_platform_processing()
                status = "ok"
            except Exception:
                logger.exception("Platform data processing failed")
                status = "failed"
                pipeline_status = "failed"
        else:
            logger.warning("Platform raw data not found at %s — skipping", PLATFORM_RAW_INPUT)
            status = "skipped"

        step_runs.append({
            "step_name": "platform_data_processing",
            "started_at_utc": step_started_at_utc,
            "duration_seconds": elapsed_seconds(step_timer),
            "status": status,
        })

    pipeline_duration_seconds = elapsed_seconds(pipeline_timer)
    pipeline_duration_hms = format_duration(pipeline_duration_seconds)

    pipeline_summary = {
        "started_at_utc": pipeline_started_at_utc,
        "finished_at_utc": utc_now_iso(),
        "duration_seconds": pipeline_duration_seconds,
        "duration_hms": pipeline_duration_hms,
        "dev_mode": DEV_MODE,
        "steps_count": len(step_runs),
        "steps": step_runs,
        "status": pipeline_status,
    }

    summary_path = QUALITY_DIR / "project_pipeline_run_summary.json"
    save_json(pipeline_summary, summary_path)

    logger.info("Pipeline %s", pipeline_status)
    logger.info("Summary: %s", summary_path)
    logger.info("Total duration: %s (%s seconds)", pipeline_duration_hms, pipeline_duration_seconds)

    if pipeline_status == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
