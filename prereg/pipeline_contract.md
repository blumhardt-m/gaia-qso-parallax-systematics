# Gaia QSO Parallax Systematics — Pipeline Contract (Gate 1)

Purpose: Rigid, human-readable specification for Gate 1 (covariate control) with deterministic sky/field-disjoint holdout.

## Data
- Input: data/processed/qso.parquet (one row per source)
- Required columns: ra, dec, parallax, astrometric_n_good_obs_al
- Optional columns: ruwe

## Canonicalization (dev dataset; plumbing only)
- NOTE: This dev dataset does not yet include a DR3 parallax zero-point correction.
- parallax_resid := parallax   (TEMPORARY for plumbing validation only)
- n_transits := astrometric_n_good_obs_al
- log_n_transits := log1p(n_transits)
- Stop condition: Before any scientific interpretation, regenerate qso.parquet with
  a fixed ZP-corrected parallax_resid definition (see Gate 0 / preprocessing spec).


## Target
- y := parallax_resid

## Spatial model (S)
- HEALPix median map on TRAIN only
- NSIDE_FINE = 64
- Prediction on test: per-pixel train median; unseen pixels filled with FILL_VALUE

## Holdout (deterministic; disjoint regions)
- Define coarse HEALPix regions using NSIDE_COARSE = 16 (applied to occupied coarse pixels)
- A coarse pixel p is in TEST iff md5(str(p)) mod HOLDOUT_MOD == 0
- HOLDOUT_MOD = 5
- All rows with coarse pixel in TEST are test rows; all others are train rows
- Sanity: abort if n_test < 1000

## Models / metrics
- M0: spatial-only prediction (S) → RMSE on test
- M1: S + Ridge correction on train residuals using log_n_transits → RMSE on test
- M2 (if ruwe present): S + Ridge correction using log_n_transits + ruwe → RMSE on test
- Ridge: alpha = 1.0, fit_intercept = True, trained on r_tr := y_tr - S_tr

## Outputs
- results/run_YYYYMMDD_HHMMSS/gate1_summary.csv
- results/run_YYYYMMDD_HHMMSS/run_manifest.json

## Gate 0 (preprocessing; not yet executed)
- Objective: Populate parallax_resid as ZP-corrected parallax residual.
- Constraint: Holdout, covariates, model class, metrics unchanged.
- Inputs required for standard correction: nu_eff_used_in_astrometry or pseudocolour plus ecliptic latitude (computed from ra/dec if not present).
- Output: data/processed/qso.parquet with parallax_resid, zpt_mas, and required inputs persisted.

