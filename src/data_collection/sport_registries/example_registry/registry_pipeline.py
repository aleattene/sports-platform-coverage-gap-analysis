import json
import logging
from typing import Callable

from src.config import DEV_MODE, LOG_LEVEL, QUALITY_DIR
from src.data_collection.sport_registries.example_registry.step_01_retrieve_regions import (
    main as step_01,
)
from src.data_collection.sport_registries.example_registry.step_02_retrieve_provinces import (
    main as step_02,
)
from src.data_collection.sport_registries.example_registry.step_03_retrieve_entities_by_province import (
    main as step_03,
)
from src.data_collection.sport_registries.example_registry.step_04_build_analysis_dataset import (
    main as step_04,
)
from src.utils.logging import configure_logging
from src.utils.runtime import elapsed_seconds, format_duration, start_timer, utc_now_iso

configure_logging(LOG_LEVEL)
logger = logging.getLogger(__name__)

PIPELINE_STEPS: list[tuple[str, Callable[[], None]]] = [
    ("step_01_retrieve_regions", step_01),
    ("step_02_retrieve_provinces", step_02),
    ("step_03_retrieve_entities_by_province", step_03),
    ("step_04_build_analysis_dataset", step_04),
]


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
    logger.info("Starting registry data collection pipeline")

    if DEV_MODE:
        logger.info("DEV_MODE enabled")

    pipeline_started_at_utc = utc_now_iso()
    pipeline_timer = start_timer()

    step_runs: list[dict[str, object]] = []
    pipeline_status = "ok"

    for step_name, step_fn in PIPELINE_STEPS:
        step_result = run_step(step_name, step_fn)
        step_runs.append(step_result)

        if step_result["status"] == "failed":
            pipeline_status = "failed"
            logger.error("Pipeline stopping: %s failed", step_name)
            break

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

    summary_path = QUALITY_DIR / "pipeline_run_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(pipeline_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    logger.info("Pipeline %s", pipeline_status)
    logger.info("Summary: %s", summary_path)
    logger.info("Total duration: %s (%s seconds)", pipeline_duration_hms, pipeline_duration_seconds)

    if pipeline_status == "failed":
        raise RuntimeError("Registry pipeline failed")


if __name__ == "__main__":
    main()
