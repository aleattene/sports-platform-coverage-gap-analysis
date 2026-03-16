import logging

import pandas as pd

from src.config import PLATFORM_PROCESSED_DIR, PROCESSED_DIR

logger = logging.getLogger(__name__)


def main() -> None:
    market_path = PROCESSED_DIR / "entity_counts_by_province.csv"
    coverage_path = PLATFORM_PROCESSED_DIR / "platform_coverage_by_region_sport.csv"
    output_path = PLATFORM_PROCESSED_DIR / "coverage_gap_analysis.csv"

    market_df = pd.read_csv(market_path)
    coverage_df = pd.read_csv(coverage_path)

    required_market_cols = {"region", "sport", "clubs_estimated"}
    required_coverage_cols = {"region", "sport", "platform_clubs"}

    missing_market = required_market_cols - set(market_df.columns)
    missing_coverage = required_coverage_cols - set(coverage_df.columns)

    if missing_market:
        raise ValueError(f"Missing columns in market dataset: {missing_market}")

    if missing_coverage:
        raise ValueError(f"Missing columns in coverage dataset: {missing_coverage}")

    market_df["clubs_estimated"] = pd.to_numeric(
        market_df["clubs_estimated"], errors="coerce"
    ).fillna(0)

    coverage_df["platform_clubs"] = pd.to_numeric(
        coverage_df["platform_clubs"], errors="coerce"
    ).fillna(0)

    analysis_df = market_df.merge(
        coverage_df,
        on=["region", "sport"],
        how="left",
    )

    analysis_df["platform_clubs"] = analysis_df["platform_clubs"].fillna(0).astype(int)
    analysis_df["clubs_estimated"] = analysis_df["clubs_estimated"].astype(int)

    analysis_df["coverage_gap"] = (
        analysis_df["clubs_estimated"] - analysis_df["platform_clubs"]
    ).clip(lower=0)

    analysis_df["coverage_rate"] = (
        analysis_df["platform_clubs"] / analysis_df["clubs_estimated"]
    ).fillna(0).round(3)

    analysis_df["priority_score"] = (
        analysis_df["coverage_gap"] * (1 - analysis_df["coverage_rate"])
    ).round(2)

    analysis_df = analysis_df.sort_values(
        by=["priority_score", "coverage_gap", "clubs_estimated"],
        ascending=[False, False, False],
    ).reset_index(drop=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    analysis_df.to_csv(output_path, index=False)

    logger.info("Coverage gap analysis dataset created.")
    logger.info("Saved to: %s", output_path)
    logger.info("\n%s", analysis_df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()