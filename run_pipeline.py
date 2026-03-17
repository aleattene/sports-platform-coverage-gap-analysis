import logging

from src.config import (
    DEV_MODE,
    FETCH_PLATFORM_DATA,
    FETCH_REGISTRY_DATA,
    LOG_LEVEL,
    QUALITY_DIR,
)
from src.utils.input_output import save_json
from src.utils.logging import configure_logging
from src.utils.runtime import elapsed_seconds, format_duration, start_timer, utc_now_iso

configure_logging(LOG_LEVEL)
logger = logging.getLogger(__name__)


def _run_step(step_name: str, step_fn: object) -> tuple[dict[str, object], str]:
    """
    Run a pipeline step, returning (step_result_dict, status).
    """
    from typing import Callable
    assert callable(step_fn)

    step_started_at_utc = utc_now_iso()
    step_timer = start_timer()
    try:
        step_fn()
        status = "ok"
    except Exception:
        logger.exception("%s failed", step_name)
        status = "failed"

    return {
        "step_name": step_name,
        "started_at_utc": step_started_at_utc,
        "duration_seconds": elapsed_seconds(step_timer),
        "status": status,
    }, status


def main() -> None:
    logger.info("Starting project pipeline")

    if DEV_MODE:
        logger.info("DEV_MODE enabled")

    logger.info(
        "FETCH_REGISTRY_DATA=%s  FETCH_PLATFORM_DATA=%s",
        FETCH_REGISTRY_DATA, FETCH_PLATFORM_DATA,
    )

    pipeline_started_at_utc = utc_now_iso()
    pipeline_timer = start_timer()

    step_runs: list[dict[str, object]] = []
    pipeline_status = "ok"

    # --- Registry pipeline ---
    from src.data_collection.sport_registries.example_registry.registry_pipeline import (
        main as run_registry_pipeline,
    )

    if FETCH_REGISTRY_DATA:
        logger.info("Running registry pipeline (fetch enabled)")
        step_result, status = _run_step("registry_pipeline", run_registry_pipeline)
        step_runs.append(step_result)

        if status == "failed":
            pipeline_status = "failed"
            logger.error("Pipeline stopping after registry failure")
    else:
        logger.info("Registry data fetch skipped (FETCH_REGISTRY_DATA=false)")
        step_runs.append({"step_name": "registry_pipeline", "status": "skipped"})

    # --- Platform pipeline (always runs, fetch controlled internally) ---
    if pipeline_status != "failed":
        from src.data_collection.sport_platforms.example_platform.platform_pipeline import (
            main as run_platform_pipeline,
        )

        logger.info("Running platform pipeline")
        step_result, status = _run_step("platform_pipeline", run_platform_pipeline)
        step_runs.append(step_result)

        if status == "failed":
            pipeline_status = "failed"
    else:
        logger.error("Platform pipeline skipped due to previous failure")

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
