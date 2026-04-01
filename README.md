# Sports Platform Coverage Gap Analysis

![CI](https://github.com/aleattene/sports-platform-coverage-gap-analysis/actions/workflows/ci.yml/badge.svg)
[![Coverage](https://codecov.io/gh/aleattene/sports-platform-coverage-gap-analysis/branch/main/graph/badge.svg)](https://codecov.io/gh/aleattene/sports-platform-coverage-gap-analysis)
![Python](https://img.shields.io/badge/Python-3.13-blue)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-blue)
![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-orange)
![Matplotlib](https://img.shields.io/badge/Matplotlib-Visualization-green)
![License](https://img.shields.io/badge/License-MIT-blue)
![Last Commit](https://img.shields.io/github/last-commit/aleattene/sports-platform-coverage-gap-analysis)

An end-to-end **Data Analysis** project that maps the distribution of Italian sports entities
registered in an official sports registry and compares it with the coverage of a sports
management platform — identifying geographic and sport-level gaps to support data-driven
expansion decisions.

---

## Business Questions

This analysis addresses five key questions for a sports platform operating in Italy:

1. **Where should the platform expand first?** Which provinces show the largest gap between registered sports entities and platform coverage?
2. **Which sports represent the biggest untapped opportunity?** What is the sport mix on the platform, and which categories are under-represented?
3. **How is the platform growing over time?** What does the registration trajectory look like?
4. **What should a phased expansion strategy look like?** How can provinces be prioritized based on market size and current gap?
5. **What is the total addressable market not yet reached?** How large is the coverage gap in absolute terms?

---

## Key Findings

In the current dataset, the platform is present across all 107 Italian provinces, but coverage depth is highly uneven.
Where registry data is available, the gap between total registered entities and platform
presence is substantial — the market is largely untapped.

### Coverage Gap by Region

![Coverage Gap by Region](reports/figures/coverage_gap_by_region_stacked.png)

### Expansion Priority Matrix

![Priority Matrix](reports/figures/priority_matrix.png)

### Geographic Coverage Map

![Italy Choropleth](reports/figures/italy_choropleth.png)

The choropleth map shows the number of platform entities by province across all 107 Italian provinces (green = higher, red = lower). Coverage is concentrated in northern and central Italy, with southern regions and islands showing comparatively lower presence.

### Sport Distribution

![Sport Mix](reports/figures/sport_mix_distribution.png)

> For the full analysis with all visualizations, see the [Executive Report](reports/REPORT.md)
> and the [EDA Notebook](notebooks/01_coverage_gap_analysis.ipynb).

---

## Analysis Scope

- **Unit of analysis:** province (107 Italian provinces)
- **Dimensions:** geographic (region/province), sport category (174 sports, 12 macro-categories), temporal (registration year)
- **Core KPIs:**

| KPI | Formula | Interpretation |
|-----|---------|----------------|
| Coverage Ratio | `platform_entities / entities_total` | 0 = no coverage, 1 = full coverage |
| Coverage Gap | `entities_total - platform_entities` | Absolute number of unreached entities |
| Priority Score | `0.6 × gap_score + 0.4 × density_score` | Composite expansion priority (0–1) |

---

## Expected Outputs

| Output | Description |
|--------|-------------|
| Coverage gap ranking | By region and province, with coverage ratio and absolute gap |
| Expansion priority ranking | Provinces scored and tiered by market size and coverage gap |
| Sport-level opportunity analysis | Macro-category distribution, sport diversity index, under-served segments |
| Temporal growth trend | Year-over-year registration trajectory with cumulative view |
| Geographic visualization | Choropleth map of platform coverage across Italian provinces |
| Interactive dashboard | [Looker Studio Dashboard](https://lookerstudio.google.com/s/tDAIpFPxjls) |

---

## Data Sources

The analysis combines two public data sources:

| Source | Description | Granularity |
|--------|-------------|-------------|
| **Registry** | Official sports registry — total registered entities | Province |
| **Platform** | Sports management platform — entities currently on the platform | Province + Sport + Year |

> **Privacy by design:** Platform raw data is sanitized at collection time.
> No Personally Identifiable Information (PII) is analyzed or stored on disk.

---

## Project Structure

```text
project_root/
├── run_pipeline.py                  # Pipeline orchestrator
├── requirements.txt
├── src/
│   ├── config.py                    # Centralized configuration (env vars)
│   ├── utils/                       # Shared utilities (HTTP, I/O, logging)
│   └── data_collection/
│       ├── sport_registries/        # Registry pipeline (Playwright, 4 steps)
│       └── sport_platforms/         # Platform pipeline (REST API, 2 steps)
├── data/
│   ├── sources/
│   │   ├── sport_registries/        # Raw + processed registry data
│   │   └── sport_platforms/         # Raw + processed platform data
│   ├── analysis/                    # Notebook output (CSV)
│   └── quality/                     # Pipeline run summaries
├── data_sample/                     # Sample data and schemas (committed)
├── notebooks/
│   └── 01_coverage_gap_analysis.ipynb   # EDA notebook
└── reports/
    ├── REPORT.md                    # Executive report
    └── figures/                     # Charts generated by notebook
```

---

## Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.13 |
| Data manipulation | Pandas, NumPy |
| Visualization | Matplotlib, Seaborn |
| Notebook | Jupyter |
| Data collection | Playwright (registry), HTTP client with retry/backoff (platform) |
| Geographic visualization | GeoPandas |
| Dashboard | Looker Studio |

---

## Reproducibility

```bash
# 1. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 1b. Install pre-commit hooks (strips notebook outputs and empty cells before each commit)
pre-commit install

# 2. Copy geographic boundaries into data/
mkdir -p data/geo && cp data_sample/geo/. data/geo/

# 3. Configure environment (copy and edit as needed)
cp .env.example .env
# No values are required to run the default pipeline (local data only).
# Set SOURCE_URL and registry vars only when FETCH_REGISTRY_DATA=true.
# Set PLATFORM_BASE_URL and platform vars only when FETCH_PLATFORM_DATA=true.

# 4. Populate data/ by fetching from the configured sources
# 4a. Fetch data from platform API
FETCH_PLATFORM_DATA=true python -m run_pipeline

# 4b. Fetch data from registry
FETCH_REGISTRY_DATA=true python -m run_pipeline

# 5. Run pipeline (processes existing local data — no remote calls)
python -m run_pipeline

# Run EDA notebook
jupyter notebook notebooks/01_coverage_gap_analysis.ipynb
```

> By default the pipeline performs **no remote calls** — it processes existing raw data.
> Set the environment variables above to trigger fresh data collection.

---

## Report

For detailed methodology, results, and all visualizations:

- [Executive Report](reports/REPORT.md) — findings, strategy recommendations, and all charts
- [EDA Notebook](notebooks/01_coverage_gap_analysis.ipynb) — full exploratory analysis with code

---

## Author

Alessandro Attene
