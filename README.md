# TERMINATED — historical research record

This repository contains a terminated study and an unpublished manuscript. Astronomy & Astrophysics rejected manuscript aa59070-26 on June 26, 2026. A subsequent local forensic audit led to termination of the project. The manuscript’s reported permutation-null result is unsupported and should not be relied upon.

**What the referee found.** Using a different, larger candidate sample, the referee reproduced the observed concentration statistic C₀.₂₀ approximately (0.602 versus the manuscript’s 0.601) and obtained a visually similar sky map. The referee reported a discrepancy in S (0.165 versus 0.241 mas), could not reproduce or interpret the reported permutation null near 0.34, and questioned the sample’s suitability because of undocumented selection and foreground contamination. Reproduction of the observed statistic and map did not validate the null comparison or its interpretation.

**What the subsequent local audit found.** The audit identified six separate failures:

1. The computation supporting the headline permutation-null result was not found in the repository’s version history.
2. The written null procedure could not produce the reported result for the unweighted estimator.
3. The manuscript’s headline analysis contradicted its own appendix; committed code followed the appendix.
4. The preregistered contract described a different study.
5. The provenance manifest contained unevaluated shell substitutions instead of computed checksums.
6. The analysis-ready dataset was recovered from system trash, with unresolved provenance limitations in some columns.

These are findings of the local audit, distinct from the referee’s findings. The repository is retained to preserve the historical record; retention does not endorse its scientific claims.

A separate concentration-methods successor was instantiated locally. It has no canonical public repository, and its existence does not rehabilitate the terminated study.

**Status reconciled October 30, 2026.** The original manuscript and historical artifacts are preserved below.

---

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
