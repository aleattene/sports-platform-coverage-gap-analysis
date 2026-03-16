import csv
import logging
from typing import Any

from src.config import LOG_LEVEL, PLATFORM_COUNTS_CSV, PLATFORM_PROCESSED_DIR, PLATFORM_RAW_DIR
from src.utils.input_output import load_json
from src.utils.logging import configure_logging

configure_logging(LOG_LEVEL)
logger = logging.getLogger(__name__)

REGION_CODE_TO_NAME: dict[str, str] = {
    "ABR": "Abruzzo",
    "BAS": "Basilicata",
    "CAL": "Calabria",
    "CAM": "Campania",
    "EMR": "Emilia-Romagna",
    "FVG": "Friuli-Venezia Giulia",
    "LAZ": "Lazio",
    "LIG": "Liguria",
    "LOM": "Lombardia",
    "MAR": "Marche",
    "MOL": "Molise",
    "PIE": "Piemonte",
    "PUG": "Puglia",
    "SAR": "Sardegna",
    "SIC": "Sicilia",
    "TOS": "Toscana",
    "TAA": "Trentino-Alto Adige/Südtirol",
    "UMB": "Umbria",
    "VDA": "Valle d'Aosta/Vallée d'Aoste",
    "VEN": "Veneto",
}

RAW_INPUT = PLATFORM_RAW_DIR / "platform_coverage.json"
PROCESSED_OUTPUT = PLATFORM_COUNTS_CSV


def aggregate_by_province(organizations: list[dict[str, Any]]) -> list[dict[str, str | int]]:
    """
    Aggregate platform organizations by province (zone), counting unique organization IDs.
    """
    province_orgs: dict[str, set[str]] = {}
    province_region: dict[str, str] = {}

    for org in organizations:
        if not isinstance(org, dict):
            continue

        address = org.get("address") or {}
        if not isinstance(address, dict):
            continue

        zone = address.get("zone")
        region_code = address.get("region")
        org_id = org.get("organizationId")

        if not zone or not org_id:
            continue

        province_orgs.setdefault(zone, set()).add(org_id)

        if zone not in province_region and region_code:
            province_region[zone] = region_code

    rows: list[dict[str, str | int]] = []
    for zone in sorted(province_orgs):
        region_code = province_region.get(zone, "")
        rows.append({
            "region_code": region_code,
            "region_name": REGION_CODE_TO_NAME.get(region_code, region_code),
            "province_abbr": zone,
            "platform_entities": len(province_orgs[zone]),
        })

    return rows


def main() -> None:
    logger.info("Starting platform data processing")

    organizations = load_json(RAW_INPUT)

    if not isinstance(organizations, list):
        raise ValueError(f"Expected a JSON array in {RAW_INPUT}")

    logger.info("Raw organizations loaded: %s", len(organizations))

    rows = aggregate_by_province(organizations)

    fieldnames = ["region_code", "region_name", "province_abbr", "platform_entities"]

    PROCESSED_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with PROCESSED_OUTPUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logger.info("Processed rows: %s", len(rows))
    logger.info("Output saved: %s", PROCESSED_OUTPUT)


if __name__ == "__main__":
    main()
