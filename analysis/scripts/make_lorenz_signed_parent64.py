#!/usr/bin/env python3
"""
Primary Lorenz curve for signed-aggregate concentration metric.

child: NSIDE_child=128
  - compute per-child median parallax: tilde{varpi}_c
  - compute per-child occupancy: N_c
  - signed contribution: s_c = N_c * tilde{varpi}_c

parent: NSIDE_parent=64
  - aggregate signed contributions: S_P = sum_{c in P} s_c
  - weight for ranking/Lorenz: W_P = |S_P|

Outputs:
  figures/lorenz_curve_signed.pdf
Prints:
  C_0.20_signed
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import healpy as hp


def guess_col(cols: list[str], candidates: list[str]) -> str | None:
    lower = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", required=True, type=Path)
    ap.add_argument("--out", default="figures/lorenz_curve_signed.pdf", type=Path)
    ap.add_argument("--nside_child", type=int, default=128)
    ap.add_argument("--nside_parent", type=int, default=64)
    ap.add_argument("--top_frac", type=float, default=0.20)
    ap.add_argument("--ra_col", default="")
    ap.add_argument("--dec_col", default="")
    ap.add_argument("--parallax_col", default="")
    args = ap.parse_args()

    if not args.parquet.exists():
        raise SystemExit(f"Parquet not found: {args.parquet}")

    # Resolve column names
    cols = list(pd.read_parquet(args.parquet, engine="pyarrow", columns=None).columns)
    ra_col = args.ra_col or guess_col(cols, ["ra", "ra_deg", "ra_icrs"])
    dec_col = args.dec_col or guess_col(cols, ["dec", "dec_deg", "dec_icrs"])
    plx_col = args.parallax_col or guess_col(cols, ["parallax", "plx", "parallax_mas", "varpi"])

    missing = [name for name, val in [("RA", ra_col), ("Dec", dec_col), ("parallax", plx_col)] if val is None]
    if missing:
        print("Required columns not found:", ", ".join(missing))
        print("Detected columns (first 60):", cols[:60])
        return 2

    df = pd.read_parquet(args.parquet, columns=[ra_col, dec_col, plx_col])

    # -------------------------
    # Step A: Compute W_P
    # -------------------------
    ra = np.deg2rad(df[ra_col].to_numpy(dtype=float))
    dec = np.deg2rad(df[dec_col].to_numpy(dtype=float))
    theta = 0.5 * np.pi - dec
    phi = ra
    plx = df[plx_col].to_numpy(dtype=float)

    pix_child = hp.ang2pix(args.nside_child, theta, phi, nest=False)

    g = pd.DataFrame({"pix": pix_child, "plx": plx}).groupby("pix")["plx"]
    med_c = g.median()   # tilde{varpi}_c
    cnt_c = g.size()     # N_c

    # signed child contributions s_c
    s_c = cnt_c.to_numpy(dtype=float) * med_c.to_numpy(dtype=float)

    # Map each child pixel id -> parent pixel id using child pixel center
    child_pix_ids = med_c.index.to_numpy(dtype=int)
    th_c, ph_c = hp.pix2ang(args.nside_child, child_pix_ids, nest=False)
    pix_parent = hp.ang2pix(args.nside_parent, th_c, ph_c, nest=False)

    # Aggregate signed contributions into parent pixels
    S_P = pd.DataFrame({"parent": pix_parent, "s": s_c}).groupby("parent")["s"].sum().to_numpy(dtype=float)

    # Parent weights W_P = |S_P|
    W_P = np.abs(S_P)
    W_P = W_P[np.isfinite(W_P)]
    W_P = W_P[W_P > 0]

    if W_P.size == 0:
        raise SystemExit("No finite positive parent weights produced; check data/columns.")

    # -------------------------
    # Step B: Lorenz curve arrays
    #   (sort ascending for standard Lorenz curve; we care about top tail via C_0.20)
    # -------------------------
    W_sorted = np.sort(W_P)           # ascending
    cumW = np.cumsum(W_sorted)
    cumW = cumW / cumW[-1]

    n = W_sorted.size
    x = np.arange(1, n + 1) / n       # cumulative sky fraction
    y = cumW                          # cumulative contribution

    # -------------------------
    # Step C: Top-20% contribution C_0.20_signed
    # -------------------------
    top_frac = float(args.top_frac)
    if not (0 < top_frac < 1):
        raise SystemExit("--top_frac must be in (0,1).")

    # Top-20% means the largest 20% weights
    k_tail = int(np.ceil(top_frac * n))   # number of top items
    C20_signed = float(W_sorted[-k_tail:].sum() / W_sorted.sum())

    # -------------------------
    # Step D: Plot and save
    # -------------------------
    args.out.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(5.5, 5.0))
    plt.plot(x, y, lw=2, label=f"Signed-aggregate (128→64), $C_{{0.20}}$={C20_signed:.4f}")
    plt.plot([0, 1], [0, 1], "k--", lw=1, alpha=0.5, label="Uniform")

    # Mark 80% point (since top 20% is the tail)
    x80 = 1.0 - top_frac
    idx80 = int(np.floor(x80 * n)) - 1
    idx80 = max(0, min(idx80, n - 1))
    y80 = y[idx80]
    plt.axvline(x80, linestyle=":", lw=1)
    plt.axhline(y80, linestyle=":", lw=1)

    plt.xlabel("Cumulative sky fraction (parent pixels)")
    plt.ylabel("Cumulative weighted contribution")
    plt.title("Alternative Lorenz Curve (Signed-Aggregate Construction)")
    plt.legend(loc="lower right", fontsize=8)
    plt.tight_layout()
    plt.savefig(args.out)
    plt.close()

    print(f"Wrote: {args.out}")
    print(f"C_0.20_signed = {C20_signed:.4f}  (child NSIDE={args.nside_child} -> parent NSIDE={args.nside_parent})")
    print(f"N_parent_pix_used = {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

