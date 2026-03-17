# TODO

## P0 — Next steps

- [ ] Implement sport platform data collection pipeline (automated retrieval of platform coverage data)
- [ ] Review `requirements.txt`: missing `playwright`, `matplotlib`, `seaborn`, `python-dotenv` (used by project but absent)
- [ ] Verify alignment between workflow entrypoint (`src/run_analysis_pipeline.py`) and CLAUDE.md commands (`python -m run_pipeline`)

## P1 — Pipeline & data quality

- [ ] Consider splitting into `requirements.txt` (pipeline) and `requirements-dev.txt` (Jupyter, notebook tools)
- [ ] Evaluate whether `entity_counts.json` (intermediate step_03 → step_04) can be eliminated by merging validation logic directly into step_03
- [ ] Populate `data_sample/` with fictitious data matching the expected structure of real data (for testing and development)
- [ ] Remove `.gitkeep` placeholders from `data_sample/` subfolders once populated with sample data (`raw/`, `quality/`)

## P2 — CI/CD

- [ ] Remove `pages: write` and `id-token: write` from top-level workflow permissions (deploy-pages job is commented out)
- [ ] Uncomment `cache: "pip"` in setup-python step to speed up CI
- [ ] Add `timeout-minutes` to the `build-data` job (avoid 6h default timeout on stuck runs)
- [ ] Clean up commented-out code blocks in workflow (deploy-pages, notebook, artifacts) — recover from git history when needed

## P3 — Housekeeping

- [ ] Remove `.env` file from the project directory (currently gitignored but still present locally)
- [ ] Simplify `data_sample/` folder structure (currently 5 levels deep for sample files)
- [ ] Recreate `docs/` with real documentation when ready (e.g. methodology, dataset description, project scope)
