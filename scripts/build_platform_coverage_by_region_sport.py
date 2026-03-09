from pathlib import Path
import pandas as pd


def get_project_root() -> Path:
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / "data").exists():
            return parent
    raise RuntimeError("Project root not found")


def main():

    project_root = get_project_root()

    input_path = project_root / "data" / "processed" / "platform_coverage_normalized.csv"
    output_path = project_root / "data" / "processed" / "platform_coverage_by_region_sport.csv"

    df = pd.read_csv(input_path)

    platform_clubs = (
        df.dropna(subset=["region", "sport"])
        .groupby(["region", "sport"], as_index=False)["organization_id"]
        .nunique()
        .rename(columns={"organization_id": "platform_clubs"})
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    platform_clubs.to_csv(output_path, index=False)

    print("Platform coverage dataset created.")
    print(platform_clubs.head())


if __name__ == "__main__":
    main()