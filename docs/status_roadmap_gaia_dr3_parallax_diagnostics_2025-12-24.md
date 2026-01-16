Project Status Update and Forward Roadmap

Project: Quasar-Based Diagnostics of Gaia DR3 Parallax Systematics
Date: 2025-12-24
Author: Michael Blumhardt
Status: Active — Major Revision Phase

1. Current Status Summary

This project constructs HEALPix maps of median Gaia DR3 quasar parallaxes to diagnose spatially varying parallax systematics. The methodological stance is explicitly conservative: the maps are framed as diagnostic uncertainty fields rather than predictive correction models.

Core components currently implemented and validated include:

Median-based HEALPix aggregation at 
𝑁
s
i
d
e
=
32
N
side
	​

=32 (
∼
1.8
∘
∼1.8
∘
)

Bootstrap uncertainty estimation per pixel

Low-order ecliptic-latitude proxy model

Spatially disjoint holdout validation using coarse HEALPix regions

Quantification of spatial signal attenuation after conditioning on depth covariates

Clear separation of descriptive (training-sky) structure from predictive generalization

The manuscript has undergone a structural and clarity revision, reducing length and sharpening the diagnostic framing. However, several essential quantitative elements were removed or left incomplete during revision and must be restored for scientific completeness and evaluability.

2. Identified Deficiencies (Blocking Issues)

The following issues currently prevent external evaluation or submission:

2.1 Missing Quantitative Validation

Test-set performance metrics (wRMSE) under spatial holdout are not reported.

The empirical basis for the “diagnostic vs. predictive” distinction is therefore not verifiable.

2.2 Missing Coverage Metadata

Sky coverage fraction after masking is not reported.

Distribution of per-pixel source counts is not reported.

Users cannot assess applicability or heteroscedasticity of the maps.

2.3 Proxy Model Performance Not Quantified

No numerical measure of variance explained by the ecliptic-latitude proxy is provided.

Claims that the proxy captures a “substantial fraction” of global structure are qualitative only.

2.4 Figure Redundancy

Residual and raw median maps are visually similar at the chosen resolution.

One figure duplicates another at vector resolution without adding information.

2.5 Selection and Contamination Sensitivity

Dependence on the Gaia DR3 quasar candidate catalog is acknowledged but not stress-tested.

No sensitivity check using a cleaner external catalog is provided.

3. Roadmap Overview

The project is approximately 70% complete. The remaining 30% consists primarily of reporting, validation, and contextualization, not new methodological development.

The roadmap is divided into six sequential phases. Each phase has a clear exit criterion.

4. Phase-by-Phase Plan
Phase 1 — Restore Empirical Falsifiability (Highest Priority)

Goal: Make the diagnostic framing empirically testable.

Actions:

Restore a validation table reporting test-set wRMSE under spatial holdout for:

Zero baseline

Proxy model only

Proxy + residual field

Report mean ± standard deviation across spatial splits.

Explicitly state whether residuals fail to improve predictive performance.

Exit Criterion:
A skeptical reader can independently verify that residual maps do not generalize predictively.

Phase 2 — Restore Coverage and Sampling Metadata

Goal: Provide essential usage metadata.

Actions:

Report sky coverage fraction after masking.

Report median and 10–90% range of per-pixel source counts.

Report fraction of sky below 
𝑁
min
⁡
N
min
	​

.

Exit Criterion:
Downstream users can assess applicability and limitations of the diagnostic maps.

Phase 3 — Quantify Proxy Model Performance

Goal: Replace qualitative language with numerical bounds.

Actions:

Report variance explained (or equivalent metric) by the ecliptic-latitude proxy on the training sky.

Report mean absolute parallax residual before and after proxy subtraction.

Retain explicit statement that proxy is not physically complete.

Exit Criterion:
“Substantial fraction” is replaced by a bounded numerical statement.

Phase 4 — Resolve Figure Redundancy

Goal: Ensure each figure conveys unique information.

Actions (choose one):

Replace the residual map with a difference map (median minus proxy).

Or remove the residual figure entirely if differences are negligible at this scale.

Remove duplicate vector-only figures unless required by journal format.

Exit Criterion:
No two figures communicate the same content.

Phase 5 — Selection and Contamination Sensitivity Check

Goal: Address the strongest external skepticism with minimal scope expansion.

Actions:

Recompute a median parallax map using a cleaner external quasar catalog (e.g., CatNorth) or a stricter subset.

Compare morphology and amplitude qualitatively or via RMS difference.

Report whether major structures persist or attenuate.

Exit Criterion:
Evidence exists that major features are not driven solely by catalog contamination.

Phase 6 — Minimal External Contextualization

Goal: Situate the work within existing Gaia literature without competition claims.

Actions:

Add a short comparison paragraph referencing:

Gaia DR3 global parallax zero-point

One independent estimate (e.g., quasar- or binary-based)

Explicitly state that the work does not replace official corrections.

Exit Criterion:
Readers can contextualize amplitudes and limitations relative to known results.

5. External Feedback Strategy (Post-Phase 4)

After Phases 1–4 are complete, targeted feedback may be solicited from 2–3 mid-career astronomers with experience in Gaia systematics.

The request should:

Ask one specific methodological question

Emphasize diagnostic framing

Avoid requests for endorsement or collaboration

This step is intended for refinement, not validation rescue.

6. Intended End State

Upon completion of Phases 1–6, the project will constitute:

A falsifiable, conservative diagnostic contribution

Suitable for submission as a Research Note or short Letter

Explicitly bounded in scope and claims

Reproducible and interpretable by downstream users

The work will not claim predictive correction capability but will provide empirically grounded uncertainty diagnostics for Gaia DR3 analyses.
