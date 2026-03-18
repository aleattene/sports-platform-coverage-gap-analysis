import importlib
import logging
from collections.abc import Callable

from src.config import DEV_MODE, FETCH_REGISTRY_DATA, LOG_LEVEL, QUALITY_DIR, RAW_DIR
from src.utils.input_output import save_json
from src.utils.logging import configure_logging
from src.utils.runtime import elapsed_seconds, format_duration, start_timer, utc_now_iso

configure_logging(LOG_LEVEL)
logger = logging.getLogger(__name__)


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
    Run the registry pipeline.

    When FETCH_REGISTRY_DATA=true: fetch fresh data from source, then process.
    When FETCH_REGISTRY_DATA=false (default): process existing raw data only.
    """
    logger.info("Starting registry pipeline (fetch=%s)", FETCH_REGISTRY_DATA)

    if DEV_MODE:
        logger.info("DEV_MODE enabled")

    pipeline_started_at_utc = utc_now_iso()
    pipeline_timer = start_timer()

    step_runs: list[dict[str, object]] = []
    pipeline_status = "ok"

    # Steps 01-03: fetch from source (only when explicitly enabled)
    fetch_steps: list[tuple[str, str]] = [
        ("step_01_retrieve_regions", "src.data_collection.sport_registries.example_registry.step_01_retrieve_regions"),
        ("step_02_retrieve_provinces", "src.data_collection.sport_registries.example_registry.step_02_retrieve_provinces"),
        ("step_03_retrieve_entities_by_province", "src.data_collection.sport_registries.example_registry.step_03_retrieve_entities_by_province"),
    ]

    if FETCH_REGISTRY_DATA:
        for step_name, module_path in fetch_steps:
            step_module = importlib.import_module(module_path)
            step_result = run_step(step_name, step_module.main)
            step_runs.append(step_result)

            if step_result["status"] == "failed":
                pipeline_status = "failed"
                logger.error("Pipeline stopping: %s failed", step_name)
                break
    else:
        logger.info("Skipping data retrieval (FETCH_REGISTRY_DATA=false)")
        for step_name, _ in fetch_steps:
            step_runs.append({"step_name": step_name, "status": "skipped"})

    # Step 04: build analysis dataset (always, if raw data exists)
    if pipeline_status != "failed":
        if any(RAW_DIR.rglob("*.json")):
            from src.data_collection.sport_registries.example_registry.step_04_build_analysis_dataset import (
                main as step_04,
            )

            step_result = run_step("step_04_build_analysis_dataset", step_04)
            step_runs.append(step_result)

            if step_result["status"] == "failed":
                pipeline_status = "failed"
        else:
            logger.warning("No raw data found in %s — nothing to process", RAW_DIR)
            step_runs.append({"step_name": "step_04_build_analysis_dataset", "status": "skipped"})

    pipeline_duration_seconds = elapsed_seconds(pipeline_timer)
    pipeline_duration_hms = format_duration(pipeline_duration_seconds)

    pipeline_summary = {
        "started_at_utc": pipeline_started_at_utc,
        "finished_at_utc": utc_now_iso(),
        "duration_seconds": pipeline_duration_seconds,
        "duration_hms": pipeline_duration_hms,
        "fetch_enabled": FETCH_REGISTRY_DATA,
        "dev_mode": DEV_MODE,
        "steps_count": len(step_runs),
        "steps": step_runs,
        "status": pipeline_status,
    }

    summary_path = QUALITY_DIR / "pipeline_run_summary.json"
    save_json(pipeline_summary, summary_path)

    logger.info("Pipeline %s", pipeline_status)
    logger.info("Summary: %s", summary_path)
    logger.info("Total duration: %s (%s seconds)", pipeline_duration_hms, pipeline_duration_seconds)

    if pipeline_status == "failed":
        raise RuntimeError("Registry pipeline failed")


if __name__ == "__main__":
    main()
