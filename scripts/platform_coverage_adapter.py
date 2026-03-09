from __future__ import annotations
from typing import Any
import pandas as pd


REGION_CODE_TO_NAME = {
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
    "TAA": "Trentino-Alto Adige",
    "UMB": "Umbria",
    "VDA": "Valle d'Aosta",
    "VEN": "Veneto",
}


def _safe_get_coordinates(address: dict[str, Any]) -> tuple[float | None, float | None]:
    coordinates = address.get("coordinates")

    if not isinstance(coordinates, list) or len(coordinates) < 2:
        return None, None

    lat = coordinates[0]
    lon = coordinates[1]

    try:
        lat = float(lat) if lat is not None else None
        lon = float(lon) if lon is not None else None
    except (TypeError, ValueError):
        return None, None

    return lat, lon


def adapt_organizations_to_dataframe(
    organizations: list[dict[str, Any]],
) -> pd.DataFrame:
    """
    Transform a list of club JSON objects into a normalized DataFrame.
    A final row corresponds to a pair of organization + sport.
    If an organization has multiple sports, it will be duplicated in multiple rows, one per sport.
    If an organization has no sport, it will still have one row with sport=None.
    """
    rows: list[dict[str, Any]] = []

    for org in organizations:
        if not isinstance(org, dict):
            continue

        organization_id = org.get("organizationId")
        club_name = org.get("name")
        logo_url = org.get("logo_url")
        registration_year = org.get("registrationYear")

        address = org.get("address") or {}
        if not isinstance(address, dict):
            address = {}

        region_code = address.get("region")
        province = address.get("zone")
        town = address.get("town")
        country = address.get("country")
        postal_code = address.get("postal_code")
        full_address = address.get("address")
        latitude, longitude = _safe_get_coordinates(address)

        sports = org.get("sport") or []
        if not isinstance(sports, list):
            sports = []

        # If no sport is specified, we still want to include the organization with sport=None to count it
        # in the coverage analysis (it will be counted as "unspecified" sport)
        if not sports:
            sports = [None]

        for sport in sports:
            rows.append(
                {
                    "organization_id": organization_id,
                    "club_name": club_name,
                    "logo_url": logo_url,
                    "sport": sport,
                    "registration_year": registration_year,
                    "country": country,
                    "region_code": region_code,
                    "region": REGION_CODE_TO_NAME.get(region_code, region_code),
                    "province": province,
                    "town": town,
                    "postal_code": postal_code,
                    "address": full_address,
                    "latitude": latitude,
                    "longitude": longitude,
                }
            )

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    # Remove duplicates based on organization_id and sport, keeping the first occurrence.
    # This is to ensure that each club is counted only once per sport in the coverage analysis,
    # even if there are duplicate entries in the input data.
    df = df.drop_duplicates(subset=["organization_id", "sport"]).reset_index(drop=True)

    return df