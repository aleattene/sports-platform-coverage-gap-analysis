import json
import logging
import os
import subprocess
import sys
from pathlib import Path

from src.config import DEV_MODE, LOG_LEVEL, QUALITY_DIR
from src.utils.logging import configure_logging
from src.utils.runtime import elapsed_seconds, format_duration, start_timer, utc_now_iso

configure_logging(LOG_LEVEL)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
CURRENT_FILE = Path(__file__).name


def get_pipeline_steps() -> list[Path]:
    """
    Discover and return a sorted list of pipeline step script paths in the current directory.
    Expected step files follow the naming pattern: step_[0-9][0-9]_*.py.
    :return: list of Paths to step scripts, sorted by filename
    """
    steps = sorted(
        step
        for step in BASE_DIR.glob("step_[0-9][0-9]_*.py")
        if step.name != CURRENT_FILE
    )
    return steps


def run_script(script_path: Path) -> dict[str, object]:
    """
    Run a single pipeline step script and measure its execution time.
    Propagates the current environment (including DEV_MODE, PYTHONPATH, etc.)
    to the subprocess.
    :param script_path: path to the step script to run
    :return: a dictionary containing step execution details
    """
    step_started_at_utc = utc_now_iso()
    step_timer = start_timer()

    logger.info("Running %s", script_path.name)

    result = subprocess.run(
        [sys.executable, str(script_path)],
        env=os.environ.copy(),
        check=False,
    )

    step_finished_at_utc = utc_now_iso()
    step_duration_seconds = elapsed_seconds(step_timer)
    step_duration_hms = format_duration(step_duration_seconds)

    status = "ok" if result.returncode == 0 else "failed"

    if result.returncode != 0:
        logger.error(
            "%s failed with exit code %s", script_path.name, result.returncode
        )

    return {
        "step_name": script_path.name,
        "started_at_utc": step_started_at_utc,
        "finished_at_utc": step_finished_at_utc,
        "duration_seconds": step_duration_seconds,
        "duration_hms": step_duration_hms,
        "exit_code": result.returncode,
        "status": status,
    }


def main() -> None:
    logger.info("Starting data collection pipeline")

    if DEV_MODE:
        logger.info("DEV_MODE enabled")

    pipeline_started_at_utc = utc_now_iso()
    pipeline_timer = start_timer()

    steps = get_pipeline_steps()

    if not steps:
        raise FileNotFoundError(
            f"No pipeline step files found in {BASE_DIR} matching pattern 'step_[0-9][0-9]_*.py'."
        )

    logger.info("Steps discovered: %s", [s.name for s in steps])

    step_runs: list[dict[str, object]] = []
    pipeline_status = "ok"

    for step in steps:
        step_result = run_script(step)
        step_runs.append(step_result)

        if step_result["status"] == "failed":
            pipeline_status = "failed"
            logger.error("Pipeline stopping: %s failed", step_result["step_name"])
            break

    pipeline_finished_at_utc = utc_now_iso()
    pipeline_duration_seconds = elapsed_seconds(pipeline_timer)
    pipeline_duration_hms = format_duration(pipeline_duration_seconds)

    pipeline_summary = {
        "started_at_utc": pipeline_started_at_utc,
        "finished_at_utc": pipeline_finished_at_utc,
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
        raise SystemExit(1)


if __name__ == "__main__":
    main()
