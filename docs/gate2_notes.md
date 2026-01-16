Across NSIDE_FINE = 16, 32, 64, 128:

RMSE M0: 1.7739976 (identical at all scales)

RMSE M1: 1.6012075, 1.6011040, 1.6012115, 1.6016360

RMSE M2: 1.5984901, 1.5983857, 1.5984933, 1.5989190

Interpretation: There is no meaningful scale-dependent collapse in predictive performance over this range. If a “collapse scale” exists, it is not identifiable from RMSE in this dataset/configuration, because the holdout error is essentially invariant to NSIDE_FINE.

Across NSIDE_FINE ∈ {16, 32, 64, 128}, holdout RMSE was effectively invariant (M0 constant to machine precision; M1/M2 varying at the ~10⁻³ level), so no collapse scale is identifiable under the preregistered field-disjoint evaluation.

Multi-scale HEALPix decomposition (NSIDE_FINE = 16–128) shows no monotonic improvement in held-out RMSE; predictive performance is flat, with negligible differences across scales, indicating a large-scale, calibration-like residual rather than fine-scale structure.
