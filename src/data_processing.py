import json
from pathlib import Path
from scripts.platform_coverage_adapter import adapt_organizations_to_dataframe

PROJECT_ROOT = Path(__file__).resolve().parents[1]
json_path = PROJECT_ROOT / "data" / "raw" / "platform_coverage_mock.json"

with json_path.open("r", encoding="utf-8") as f:
    organizations = json.load(f)

df = adapt_organizations_to_dataframe(organizations)

print(df.head())
print(df.shape)

output_path = json_path = PROJECT_ROOT / "data" / "processed" / "platform_coverage_normalized.csv"
df.to_csv(output_path, index=False)