from __future__ import annotations

import json
import random
import uuid
from pathlib import Path

# -----------------------------
# Config
# -----------------------------
OUTPUT_PATH = Path("data/raw/platform_coverage_mock.json")
N_ORGANIZATIONS = 3000
SEED = 42

random.seed(SEED)

# -----------------------------
# Region metadata
# -----------------------------
REGIONS = [
    {
        "name": "Abruzzo",
        "code": "ABR",
        "capital": "L'Aquila",
        "province": "AQ",
        "lat_range": (42.20, 42.45),
        "lon_range": (13.20, 13.60),
        "weight": 2800,
    },
    {
        "name": "Basilicata",
        "code": "BAS",
        "capital": "Potenza",
        "province": "PZ",
        "lat_range": (40.50, 40.75),
        "lon_range": (15.70, 15.95),
        "weight": 1200,
    },
    {
        "name": "Calabria",
        "code": "CAL",
        "capital": "Catanzaro",
        "province": "CZ",
        "lat_range": (38.80, 39.15),
        "lon_range": (16.45, 16.80),
        "weight": 2300,
    },
    {
        "name": "Campania",
        "code": "CAM",
        "capital": "Napoli",
        "province": "NA",
        "lat_range": (40.75, 41.05),
        "lon_range": (14.10, 14.45),
        "weight": 6400,
    },
    {
        "name": "Emilia-Romagna",
        "code": "EMR",
        "capital": "Bologna",
        "province": "BO",
        "lat_range": (44.40, 44.65),
        "lon_range": (11.20, 11.50),
        "weight": 8000,
    },
    {
        "name": "Friuli-Venezia Giulia",
        "code": "FVG",
        "capital": "Trieste",
        "province": "TS",
        "lat_range": (45.55, 45.75),
        "lon_range": (13.65, 13.95),
        "weight": 2600,
    },
    {
        "name": "Lazio",
        "code": "LAZ",
        "capital": "Roma",
        "province": "RM",
        "lat_range": (41.75, 42.05),
        "lon_range": (12.35, 12.70),
        "weight": 9000,
    },
    {
        "name": "Liguria",
        "code": "LIG",
        "capital": "Genova",
        "province": "GE",
        "lat_range": (44.35, 44.50),
        "lon_range": (8.80, 9.05),
        "weight": 3100,
    },
    {
        "name": "Lombardia",
        "code": "LOM",
        "capital": "Milano",
        "province": "MI",
        "lat_range": (45.35, 45.60),
        "lon_range": (9.00, 9.35),
        "weight": 12000,
    },
    {
        "name": "Marche",
        "code": "MAR",
        "capital": "Ancona",
        "province": "AN",
        "lat_range": (43.55, 43.75),
        "lon_range": (13.40, 13.60),
        "weight": 3000,
    },
    {
        "name": "Molise",
        "code": "MOL",
        "capital": "Campobasso",
        "province": "CB",
        "lat_range": (41.50, 41.70),
        "lon_range": (14.55, 14.80),
        "weight": 900,
    },
    {
        "name": "Piemonte",
        "code": "PIE",
        "capital": "Torino",
        "province": "TO",
        "lat_range": (45.00, 45.20),
        "lon_range": (7.55, 7.85),
        "weight": 7200,
    },
    {
        "name": "Puglia",
        "code": "PUG",
        "capital": "Bari",
        "province": "BA",
        "lat_range": (41.00, 41.20),
        "lon_range": (16.75, 17.10),
        "weight": 5600,
    },
    {
        "name": "Sardegna",
        "code": "SAR",
        "capital": "Cagliari",
        "province": "CA",
        "lat_range": (39.15, 39.30),
        "lon_range": (9.05, 9.20),
        "weight": 2400,
    },
    {
        "name": "Sicilia",
        "code": "SIC",
        "capital": "Palermo",
        "province": "PA",
        "lat_range": (38.05, 38.20),
        "lon_range": (13.25, 13.45),
        "weight": 6000,
    },
    {
        "name": "Toscana",
        "code": "TOS",
        "capital": "Firenze",
        "province": "FI",
        "lat_range": (43.70, 43.85),
        "lon_range": (11.15, 11.35),
        "weight": 6800,
    },
    {
        "name": "Trentino-Alto Adige",
        "code": "TAA",
        "capital": "Trento",
        "province": "TN",
        "lat_range": (46.00, 46.15),
        "lon_range": (11.05, 11.20),
        "weight": 2500,
    },
    {
        "name": "Umbria",
        "code": "UMB",
        "capital": "Perugia",
        "province": "PG",
        "lat_range": (43.05, 43.20),
        "lon_range": (12.30, 12.45),
        "weight": 1900,
    },
    {
        "name": "Valle d'Aosta",
        "code": "VDA",
        "capital": "Aosta",
        "province": "AO",
        "lat_range": (45.70, 45.78),
        "lon_range": (7.25, 7.40),
        "weight": 600,
    },
    {
        "name": "Veneto",
        "code": "VEN",
        "capital": "Venezia",
        "province": "VE",
        "lat_range": (45.40, 45.55),
        "lon_range": (12.20, 12.45),
        "weight": 8500,
    },
]

# -----------------------------
# Sports taxonomy
# -----------------------------
SPORTS = [
    ("football", 0.32),
    ("tennis", 0.10),
    ("basketball", 0.09),
    ("volleyball", 0.09),
    ("swimming", 0.08),
    ("athletics", 0.06),
    ("martial_arts", 0.07),
    ("cycling", 0.05),
    ("gymnastics", 0.05),
    ("padel", 0.05),
    ("futsal", 0.02),
    ("rugby", 0.01),
    ("baseball", 0.005),
    ("handball", 0.005),
]

SPORT_KEYS = [sport[0] for sport in SPORTS]
SPORT_WEIGHTS = [sport[1] for sport in SPORTS]

# -----------------------------
# Naming pools
# -----------------------------
PREFIXES = [ "A.S.D.", "S.S.D.", "U.S.D.", "A.C.", "Polisportiva", "Club", "Sporting Club", "Associazione Sportiva" ]

NAME_PARTS = [ "Aurora", "Atletico", "Virtus", "Libertas", "Olimpia", "Pro", "Real", "Nuova", "San Marco", "San Paolo",
    "Stella Azzurra", "Sporting", "Accademia", "Union", "Junior", "Elite" ]

SUFFIXES = [ "Academy", "Team", "Sport", "Center", "Club", "2020", "2021", "2022", "2023", "Italia" ]

STREET_NAMES = [ "Via Roma", "Via Garibaldi", "Via Dante", "Via Mazzini", "Via dello Sport", "Viale Europa",
    "Via Leonardo da Vinci", "Via Marconi", "Piazza Italia", "Piazzale dello Sport" ]

# -----------------------------
# Helpers
# -----------------------------
def weighted_region_choice() -> dict:
    weights = [region["weight"] for region in REGIONS]
    return random.choices(REGIONS, weights=weights, k=1)[0]


def generate_coordinates(region: dict) -> list[float]:
    lat = round(random.uniform(*region["lat_range"]), 7)
    lon = round(random.uniform(*region["lon_range"]), 7)
    return [lat, lon]


def generate_postal_code() -> str:
    """
    Generate a random simulated 5-digit postal code (CAP) for Italy.
    :return: A string representing the postal code.
    """
    return f"{random.randint(1000, 99999):05d}"


def generate_street_address() -> str:
    """
    Generate a random simulated street address using common Italian street names and a random number.
    :return: A string representing the street address (street name + house number).
    """
    street = random.choice(STREET_NAMES)
    number = random.randint(1, 120)
    return f"{street}, {number}"


def generate_club_name(region: dict) -> str:
    prefix = random.choice(PREFIXES)
    part1 = random.choice(NAME_PARTS)
    geo = random.choice([region["capital"], region["name"], random.choice(NAME_PARTS)])
    suffix = random.choice(SUFFIXES)

    patterns = [
        f"{prefix} {part1} {geo}",
        f"{prefix} {geo} {suffix}",
        f"{prefix} {part1} {suffix}",
        f"{prefix} {part1} {geo} {suffix}",
    ]
    return random.choice(patterns)


def generate_organization_id() -> str:
    return uuid.uuid4().hex[:24]


def generate_registration_year() -> int:
    return random.randint(2000, 2025)


def generate_sports() -> list[str]:
    # 82% monosport, 15% bisport, 3% trisport
    n_sports = random.choices(
        population=[1, 2, 3],
        weights=[0.82, 0.15, 0.03],
        k=1,
    )[0]

    sports = random.choices(SPORT_KEYS, weights=SPORT_WEIGHTS, k=n_sports * 2)
    unique_sports = []
    for sport in sports:
        if sport not in unique_sports:
            unique_sports.append(sport)
        if len(unique_sports) == n_sports:
            break

    # fallback - if the above loop doesn't yield enough unique sports (unlikely), we fill the rest randomly
    while len(unique_sports) < n_sports:
        candidate = random.choice(SPORT_KEYS)
        if candidate not in unique_sports:
            unique_sports.append(candidate)

    return unique_sports


def build_organization() -> dict:
    region = weighted_region_choice()
    coordinates = generate_coordinates(region)

    return {
        "name": generate_club_name(region),
        "organizationId": generate_organization_id(),
        "logo_url": None,
        "sport": generate_sports(),
        "registrationYear": generate_registration_year(),
        "address": {
            "coordinates": coordinates,
            "address": generate_street_address(),
            "country": "ITA",
            "zone": region["province"],
            "region": region["code"],
            "town": region["capital"],
            "postal_code": generate_postal_code(),
        },
    }


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    output_path = project_root / "data" / "raw" / "platform_coverage_mock.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    organizations = [build_organization() for _ in range(N_ORGANIZATIONS)]

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(organizations, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(organizations)} organizations to {output_path}")


if __name__ == "__main__":
    main()