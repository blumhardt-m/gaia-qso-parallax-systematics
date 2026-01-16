# NSIDE effective pixelization closure (signed-aggregate)

Date: 2026-01-14

Dataset:
- ../../data/processed/triage_outputs_2026-01-09/qso_merged_for_triage_analysis_ready.parquet
Columns: ra, dec, parallax

Locked production choice:
- Primary concentration metric: signed-aggregate on fixed parent NSIDE=64
- Child NSIDE (medians): 128

Result (locked):
- NSIDE_child=128 -> parent=64: C_0.20_signed = 0.5617
- cancel_ratio = 0.6372
- N_parent_pix = 49111, k_top_parent = 9823

Legacy (secondary/continuity):
- NSIDE=128: C_0.20_legacy = 0.5548
- N_pix = 192571, median src/pix = 14, k_top = 38515

Mechanism:
- cancel_ratio decreases with NSIDE_child, demonstrating within-parent sign cancellation.
- This explains why abs-before-sum (legacy) is resolution-sensitive and why signed-aggregate is preferred.

