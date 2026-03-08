# Sports Platform Coverage Gap Analysis

Analysis of the territorial coverage gap of a sports platform by comparing
estimated territorial sports supply with simulated platform coverage.

## Project Goal
Identify regions and sports that are not yet served (or only partially served) by the platform,
highlighting areas where there may be greater potential for coverage, visibility, or adoption.

## Main Business Question
Which Italian regions show the largest gap between estimated territorial sports supply and
the coverage provided by a sports platform?

## Scope (MVP)
- Main unit of analysis: **region**
- Comparison between **market supply** and **platform coverage**
- Coverage simulated on a structured dataset in **JSON/CSV format**
- Main KPIs:
    - **coverage rate**
    - **coverage gap**
    - **sports coverage rate**
    - **priority score**

## Planned Stack
- Python
- Pandas
- Jupyter
- Matplotlib
- Git / GitHub

## Data Sources
The analysis combines multiple data sources to estimate territorial sports supply and platform coverage.
Possible sources include:
- Italian open data on sports clubs and facilities
- Federations or regional sports registries
- Simulated platform dataset representing registered clubs or organizations
- Manually curated datasets when public data is unavailable
- Datasets are stored following a typical data project structure:
```text
    data/
      raw/        # original datasets
      interim/    # cleaned intermediate datasets
      processed/  # final analysis-ready datasets
```

## Project Structure
```text
data/
  raw/
  interim/
  processed/
notebooks/
src/
reports/
docs/
```

## Folder Description
```text
data/           # contains all datasets used during the project lifecycle
notebooks/      # jupyter notebooks used for exploration, cleaning, and analysis
src/            # python scripts for reusable data processing and KPI calculation
reports/        # final charts, visualizations, and insights
docs/           # sdditional documentation or methodology notes
```

## Expected Outputs

The project will generate:
- Territorial **coverage maps**
- **Coverage gap ranking** by region or province
- Sport-specific coverage analysis
- A **priority score** highlighting areas where platform expansion could have the highest impact

These outputs can support **strategic decisions for sports platforms**, such as:
- identifying underserved territories
- prioritizing expansion
- improving platform adoption among sports organizations.

