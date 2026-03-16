import json
import logging

from scripts.platform_coverage_adapter import adapt_organizations_to_dataframe
from src.config import PLATFORM_PROCESSED_DIR, PLATFORM_RAW_DIR

logger = logging.getLogger(__name__)

json_path = PLATFORM_RAW_DIR / "platform_coverage.json"

with json_path.open("r", encoding="utf-8") as f:
    organizations = json.load(f)

df = adapt_organizations_to_dataframe(organizations)

logger.info("Shape: %s", df.shape)

output_path = PLATFORM_PROCESSED_DIR / "platform_coverage_normalized.csv"
df.to_csv(output_path, index=False)