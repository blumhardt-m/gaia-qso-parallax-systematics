# Gaia DR3 QSO Parallax Systematics

Empirical, quasar-based mapping and correction of Gaia DR3 parallax zero-point systematics.

## Quickstart
1) Create environment:
   - conda: `conda env create -f environment.yml && conda activate gaiaqso`
   - or pip: `pip install -e .`

2) Run pipeline (in order):
   - `python scripts/01_query_gaia.py`
   - `python scripts/02_build_maps.py`
   - `python scripts/03_validate_holdout.py`
   - `python scripts/04_make_figures.py`

3) Outputs:
   - Maps: `outputs/maps/`
   - Figures: `outputs/figures/`
   - Tables: `outputs/tables/`

## Project conventions
- Raw downloads go in `data/raw/` (never edited by hand).
- Derived tables go in `data/processed/`.
- All generated artifacts go in `outputs/`.
- Parameters live in `configs/default.yaml`.
