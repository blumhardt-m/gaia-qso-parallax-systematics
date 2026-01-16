Dataset: qso.parquet (500k, dev subset)

Holdout: NSIDE_COARSE=16, HOLDOUT_MOD=5, occupied-pixel hash

Results:

M0 RMSE = 1.7740

M1 RMSE = 1.6012

M2 RMSE = 1.5985

Observation: covariates reduce error but do not eliminate spatial term

Status: Gate 1 passed; proceed to multi-scale test

Gate 1: Covariate Control via Field-Disjoint Spatial Holdout

We assessed whether apparent spatial structure in Gaia QSO parallaxes collapses under known observational covariates using a preregistered, field-disjoint holdout. The analysis used a processed QSO table (qso.parquet, N = 500,000). Because this development dataset does not include a precomputed parallax residual, we set parallax_resid := parallax for diagnostic purposes only. The number of astrometric transits was defined as n_transits := astrometric_n_good_obs_al, and we used log_n_transits = log1p(n_transits) as the primary covariate; RUWE was included when present.

Spatial structure was modeled using a HEALPix median map constructed on the training set only, with NSIDE_FINE = 64. Predictions for test objects were obtained from the corresponding train-pixel median; unseen pixels were assigned a fixed fill value of zero. To enforce a deterministic, sky-disjoint evaluation, sources were partitioned into train and test sets using coarse HEALPix regions at NSIDE_COARSE = 16, applied to occupied pixels only. A coarse pixel was assigned to the test set if md5(str(pixel_id)) mod 5 == 0, yielding 20 occupied coarse regions in total, of which 3 were held out (67,442 test objects; 432,558 train objects). Runs were aborted if fewer than 1,000 test objects were produced.

Three models were evaluated on the same held-out set using RMSE: (M0) spatial-only prediction; (M1) spatial prediction plus a ridge regression (α = 1.0) fit on training residuals using log_n_transits; and (M2) the same residual correction including RUWE. The spatial map amplitude on the training set had RMS 0.816 and a 5–95% range of 0.148, with 231 populated fine pixels. Holdout RMSE decreased from 1.774 (M0) to 1.601 with log_n_transits (M1), with only a marginal additional reduction to 1.598 when RUWE was included (M2). All results are recorded under run ID run_20251227_234810.
