from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv


def get_env(name: str, default: str | None = None, required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value or ""


def get_env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def get_env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer.") from exc


PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")

APP_ENV = get_env("APP_ENV", "development")
if APP_ENV not in ("development", "production"):
    raise ValueError(f"APP_ENV must be 'development' or 'production', got: '{APP_ENV}'")

DATA_DIR = PROJECT_ROOT / "data"

ANALYSIS_DIR = DATA_DIR / "analysis"
SOURCES_DIR = DATA_DIR / "sources"
SPORT_PLATFORMS_DIR = SOURCES_DIR / "sport_platforms"
SPORT_REGISTRIES_DIR = SOURCES_DIR / "sport_registries"

PLATFORM_NAME = get_env("PLATFORM_NAME", "example_platform")
PLATFORM_DIR = SPORT_PLATFORMS_DIR / PLATFORM_NAME
PLATFORM_RAW_DIR = PLATFORM_DIR / "raw"
PLATFORM_PROCESSED_DIR = PLATFORM_DIR / "processed"

REGISTRY_NAME = get_env("REGISTRY_NAME", "example_registry")
REGISTRY_DIR = SPORT_REGISTRIES_DIR / REGISTRY_NAME

RAW_DIR = REGISTRY_DIR / "raw"
SOURCE_OUTPUT_DIR = RAW_DIR / get_env("SOURCE_OUTPUT_SUBDIR", "source")

REGIONS_DIR = SOURCE_OUTPUT_DIR / "regions"
PROVINCES_DIR = SOURCE_OUTPUT_DIR / "provinces"
ENTITIES_DIR = SOURCE_OUTPUT_DIR / "entities"

PROCESSED_DIR = REGISTRY_DIR / "processed"
QUALITY_DIR = REGISTRY_DIR / "quality"

REGISTRY_COUNTS_CSV = PROCESSED_DIR / "registry_entity_counts_by_province.csv"
PLATFORM_COUNTS_CSV = PLATFORM_PROCESSED_DIR / "platform_entity_counts_by_province.csv"

SOURCE_URL = get_env("SOURCE_URL", required=True)

SOURCE_REGION_SELECT_NAME = get_env("SOURCE_REGION_SELECT_NAME")
SOURCE_PROVINCE_SELECT_NAME = get_env("SOURCE_PROVINCE_SELECT_NAME")
SOURCE_PROVINCES_TASK_KEY = get_env("SOURCE_PROVINCES_TASK_KEY")

PWT_HEADLESS = get_env_bool("PW_HEADLESS", True)
PWT_SLOW_MO = get_env_int("PW_SLOW_MO", 250)
PWT_TIMEOUT_MS = get_env_int("PW_TIMEOUT_MS", 60000)
PWT_POST_LOAD_WAIT_MS = get_env_int("PW_POST_LOAD_WAIT_MS", 3000)
PWT_COOKIE_WAIT_MS = get_env_int("PW_COOKIE_WAIT_MS", 1000)
PWT_BETWEEN_REQUESTS_MS = get_env_int("PW_BETWEEN_REQUESTS_MS", 5000)
SOURCE_PAGE_SIZE = get_env_int("SOURCE_PAGE_SIZE", 30)

MAX_PAGE_RETRIES = get_env_int("MAX_PAGE_RETRIES", 3)
MAX_PROVINCE_RETRIES = get_env_int("MAX_PROVINCE_RETRIES", 3)
WAIT_AFTER_SELECT_MS = get_env_int("WAIT_AFTER_SELECT_MS", 3000)
WAIT_AFTER_SEARCH_MS = get_env_int("WAIT_AFTER_SEARCH_MS", 4000)
WAIT_RETRY_MS = get_env_int("WAIT_RETRY_MS", 5000)
CARDS_CONTAINER_TIMEOUT_MS = get_env_int("CARDS_CONTAINER_TIMEOUT_MS", 10000)

LOG_LEVEL = get_env("LOG_LEVEL", "INFO")

# Dev sampling: when DEV_MODE=true, step_03 randomly samples a subset of
# regions/provinces instead of scraping all ~107 provinces.
# Set DEV_MODE=false (or unset) for a full production run.
DEV_MODE = get_env_bool("DEV_MODE", False)
DEV_SAMPLE_REGIONS = get_env_int("DEV_SAMPLE_REGIONS", 3)
DEV_SAMPLE_PROVINCES_PER_REGION = get_env_int("DEV_SAMPLE_PROVINCES_PER_REGION", 2)

# Validation of critical configuration values
if not SOURCE_REGION_SELECT_NAME.strip():
    raise ValueError("SOURCE_REGION_SELECT_NAME cannot be empty.")

if not SOURCE_PROVINCE_SELECT_NAME.strip():
    raise ValueError("SOURCE_PROVINCE_SELECT_NAME cannot be empty.")

if not SOURCE_PROVINCES_TASK_KEY.strip():
    raise ValueError("SOURCE_PROVINCES_TASK_KEY cannot be empty.")




for path in (
        DATA_DIR,
        ANALYSIS_DIR,
        SOURCES_DIR,
        SPORT_PLATFORMS_DIR,
        SPORT_REGISTRIES_DIR,
        PLATFORM_DIR,
        PLATFORM_RAW_DIR,
        PLATFORM_PROCESSED_DIR,
        REGISTRY_DIR,
        RAW_DIR,
        SOURCE_OUTPUT_DIR,
        REGIONS_DIR,
        PROVINCES_DIR,
        ENTITIES_DIR,
        PROCESSED_DIR,
        QUALITY_DIR,
):
    path.mkdir(parents=True, exist_ok=True)