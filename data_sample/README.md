# data_sample/

Sample data mirroring the structure of `data/` (which is gitignored).
Use this folder for testing, development, and documentation purposes.

## Expected structure

```
data_sample/
└── sources/
    ├── sport_registries/<registry_name>/
    │   ├── raw/            # Raw data collected from the registry source
    │   ├── processed/      # Cleaned and normalized datasets
    │   └── quality/        # Quality check outputs from pipeline steps
    └── sport_platforms/<platform_name>/
        ├── raw/            # Raw data from the sport platform
        ├── processed/      # Aggregated and analysis-ready datasets
        └── quality/        # Quality check outputs
```

## Column schemas

### Registry — `registry_entity_counts_by_province.csv`

| Column          | Type   | Description                              |
|-----------------|--------|------------------------------------------|
| region_id       | int    | Numeric ID of the region                 |
| region_name     | string | Full name of the region                  |
| province_id     | int    | Numeric ID of the province               |
| province_name   | string | Full name of the province                |
| province_abbr   | string | Two-letter province abbreviation         |
| entities_total  | int    | Total registered sport entities          |

### Platform — `platform_entity_counts_by_province.csv`

| Column            | Type   | Description                              |
|-------------------|--------|------------------------------------------|
| region_code       | string | Three-letter region code                 |
| region_name       | string | Full name of the region                  |
| province_abbr     | string | Two-letter province abbreviation         |
| platform_entities | int    | Number of entities listed on the platform|

### Sample — `platform_coverage_by_region_sport.csv`

| Column         | Type   | Description                              |
|----------------|--------|------------------------------------------|
| region         | string | Full name of the region                  |
| sport          | string | Sport discipline (English)               |
| platform_clubs | int    | Number of clubs on the platform          |

### Sample — `market_supply_italy_simulated.csv`

| Column          | Type   | Description                              |
|-----------------|--------|------------------------------------------|
| region          | string | Full name of the region                  |
| sport           | string | Sport discipline (Italian)               |
| clubs_estimated | int    | Estimated number of clubs                |

> **Note**: Sport names use English in platform data and Italian in registry
> simulated data. Standardization to English is planned for future iterations.
