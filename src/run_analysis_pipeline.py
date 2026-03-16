from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_step(step_name: str, command: list[str], cwd: Path) -> None:
    print(f"\n--- {step_name} ---")
    print(" ".join(command))
    result = subprocess.run(command, cwd=cwd, check=False)
    if result.returncode != 0:
        raise SystemExit(f"{step_name} failed with exit code {result.returncode}")


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]

    run_step(
        "Build platform coverage by region and sport ...",
        [sys.executable, "scripts/build_platform_coverage_by_region_sport.py"],
        cwd=project_root,
    )

    run_step(
        "Build coverage gap analysis ...",
        [sys.executable, "scripts/build_coverage_gap_analysis.py"],
        cwd=project_root,
    )


if __name__ == "__main__":
    main()