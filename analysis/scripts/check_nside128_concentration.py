#!/usr/bin/env python3
"""
NSIDE robustness check for Top-20% concentration C_0.20.

PRIMARY (default) metric: SIGNED-aggregate concentration on a fixed parent grid.
  - Bin sources into HEALPix *child* pixels at NSIDE_child
  - Compute per-child median parallax (tilde{varpi}_c) and counts N_c
  - Define signed contribution s_c = N_c * tilde{varpi}_c
  - Aggregate to parent pixels at NSIDE_parent: S_P = sum_{c in P} s_c
  - Define parent weight W_P = |S_P|
  - Define C_0.20 = sum(top 20% of W_P) / sum(all W_P)
This is substantially more resolution-consistent because abs is applied *after* aggregation.

Cancellation diagnostic (printed with primary metric):
  cancel_ratio = (sum_P |S_P|) / (sum_c |s_c|)
Values < 1 indicate within-parent sign cancellation; smaller means stronger cancellation.

SECONDARY (legacy) metric (printed for continuity):
  - Compute per-pixel median parallax (tilde{varpi}_p) and counts N_p at NSIDE
  - Define weight w_p = N_p * |tilde{varpi}_p|
  - Define C_0.20 = sum(top 20% of w_p) / sum(all w_p)
This is not invariant under refinement because abs is applied before aggregation.

Optional diagnostics:
  --min_count m1 m2 ... :
      Legacy-only occupancy cut: keep only pixels with N_p >= m before computing legacy C_0.20 (prints grid).

  --degrade_to NSIDE_COMMON :
      Legacy degraded check: compute w_c = N_c * |median_c| at NSIDE_child, then aggregate weights to parent pixels
      at NSIDE_COMMON and compute C_0.20 on the common grid (demonstrates abs-before-sum instability).

  --degrade_signed :
      When used with --degrade_to, also print the SIGNED degraded check on that parent grid.

Usage (from analysis/scripts):
  python3 check_nside128_concentration.py \
    --parquet ../../data/processed/triage_outputs_2026-01-09/qso_merged_for_triage_analysis_ready.parquet \
    --nsides 64 128 256

  python3 check_nside128_concentration.py \
    --parquet ../../data/processed/triage_outputs_2026-01-09/qso_merged_for_triage_analysis_ready.parquet \
    --nsides 32 64 128 256 \
    --parent_nside 64

  # Optional diagnostics
  python3 check_nside128_concentration.py \
    --parquet ../../data/processed/triage_outputs_2026-01-09/qso_merged_for_triage_analysis_ready.parquet \
    --nsides 32 64 128 256 \
    --degrade_to 32 --degrade_signed

  python3 check_nside128_concentration.py \
    --parquet ../../data/processed/triage_outputs_2026-01-09/qso_merged_for_triage_analysis_ready.parquet \
    --nsides 32 64 128 256 \
    --min_count 1 5 10 20
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import healpy as hp
except Exception as e:
    raise SystemExit(
        "healpy is required. Install with:\n"
        "  pip install healpy\n"
        f"Original error: {e}"
    )

try:
    import pyarrow.parquet as pq
except Exception as e:
    raise SystemExit(
        "pyarrow is required for Parquet schema introspection. Install with:\n"
        "  pip install pyarrow\n"
        f"Original error: {e}"
    )


def guess_col(cols: list[str], candidates: list[str]) -> str | None:
    """Return first matching column name (case-insensitive) from candidates."""
    lower = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    return None


def _prep_arrays(df: pd.DataFrame, ra_col: str, dec_col: str, plx_col: str):
    ra = np.deg2rad(df[ra_col].to_numpy(dtype=float))
    dec = np.deg2rad(df[dec_col].to_numpy(dtype=float))
    theta = 0.5 * np.pi - dec
    phi = ra
    plx = df[plx_col].to_numpy(dtype=float)
    return theta, phi, plx


def _group_child_medians_counts(
    df: pd.DataFrame, ra_col: str, dec_col: str, plx_col: str, nside: int
):
    """Return (occupied_pix_ids, medians, counts) for child pixels at NSIDE=nside."""
    theta, phi, plx = _prep_arrays(df, ra_col, dec_col, plx_col)
    pix = hp.ang2pix(nside, theta, phi, nest=False)

    g = pd.DataFrame({"pix": pix, "plx": plx}).groupby("pix")["plx"]
    med = g.median()  # pandas Series indexed by pix
    cnt = g.size()    # pandas Series indexed by pix

    occ_pix = med.index.to_numpy(dtype=np.int64)
    med_arr = med.to_numpy(dtype=float)
    cnt_arr = cnt.to_numpy(dtype=np.int64)
    return occ_pix, med_arr, cnt_arr


def compute_c020(
    df: pd.DataFrame,
    ra_col: str,
    dec_col: str,
    plx_col: str,
    nside: int,
    top_frac: float,
) -> dict:
    """Legacy (paper-consistent): w_p = N_p * |median(plx)_p|, C0.20 on native NSIDE."""
    _occ_pix, med_arr, cnt_arr = _group_child_medians_counts(df, ra_col, dec_col, plx_col, nside=nside)

    w = cnt_arr.astype(float) * np.abs(med_arr)
    wsum = float(w.sum())

    if not np.isfinite(wsum) or wsum <= 0.0:
        return {
            "nside": int(nside),
            "C_0.20": float("nan"),
            "N_pix": int(len(w)),
            "median_sources_per_pixel": int(np.median(cnt_arr)) if len(cnt_arr) else 0,
            "k_top_pixels": 0,
            "note": "Non-finite or zero total weight; check parallax column / units.",
        }

    w_sorted = np.sort(w)[::-1]
    k = int(np.ceil(top_frac * len(w_sorted)))
    c020 = float(w_sorted[:k].sum() / wsum)

    return {
        "nside": int(nside),
        "C_0.20": c020,
        "N_pix": int(len(w_sorted)),
        "median_sources_per_pixel": int(np.median(cnt_arr)) if len(cnt_arr) else 0,
        "k_top_pixels": int(k),
    }


def compute_c020_min_count(
    df: pd.DataFrame,
    ra_col: str,
    dec_col: str,
    plx_col: str,
    nside: int,
    top_frac: float,
    min_count: int,
) -> dict:
    """Legacy occupancy-cut variant: drop pixels with N_p < min_count before computing legacy C0.20."""
    _occ_pix, med_arr, cnt_arr = _group_child_medians_counts(df, ra_col, dec_col, plx_col, nside=nside)

    keep = cnt_arr >= int(min_count)
    if not np.any(keep):
        return {
            "nside": int(nside),
            "min_count": int(min_count),
            "C_0.20": float("nan"),
            "N_pix": 0,
            "median_sources_per_pixel": 0,
            "k_top_pixels": 0,
        }

    w = cnt_arr[keep].astype(float) * np.abs(med_arr[keep])
    cnt2 = cnt_arr[keep]
    wsum = float(w.sum())

    if not np.isfinite(wsum) or wsum <= 0.0:
        return {
            "nside": int(nside),
            "min_count": int(min_count),
            "C_0.20": float("nan"),
            "N_pix": int(len(w)),
            "median_sources_per_pixel": int(np.median(cnt2)) if len(cnt2) else 0,
            "k_top_pixels": 0,
        }

    w_sorted = np.sort(w)[::-1]
    k = int(np.ceil(top_frac * len(w_sorted)))
    c020 = float(w_sorted[:k].sum() / wsum)

    return {
        "nside": int(nside),
        "min_count": int(min_count),
        "C_0.20": c020,
        "N_pix": int(len(w_sorted)),
        "median_sources_per_pixel": int(np.median(cnt2)) if len(cnt2) else 0,
        "k_top_pixels": int(k),
    }


def compute_c020_degraded(
    df: pd.DataFrame,
    ra_col: str,
    dec_col: str,
    plx_col: str,
    nside: int,
    top_frac: float,
    degrade_to: int,
) -> dict:
    """
    Legacy degraded check:
      child weight w_c = N_c * |median(plx)_c|
      parent W_P = sum_{c in P} w_c
      C0.20 computed on W_P over parent pixels.
    """
    degrade_to = int(degrade_to)
    nside = int(nside)

    if degrade_to <= 0:
        raise ValueError("degrade_to must be a positive integer.")
    if degrade_to > nside:
        return {
            "nside": nside,
            "degrade_to": degrade_to,
            "C_0.20": float("nan"),
            "N_parent_pix": 0,
            "k_top_parent": 0,
            "note": "degrade_to must be <= nside.",
        }

    occ_pix, med_arr, cnt_arr = _group_child_medians_counts(df, ra_col, dec_col, plx_col, nside=nside)
    w = cnt_arr.astype(float) * np.abs(med_arr)

    wsum_native = float(w.sum())
    if not np.isfinite(wsum_native) or wsum_native <= 0.0:
        return {
            "nside": nside,
            "degrade_to": degrade_to,
            "C_0.20": float("nan"),
            "N_parent_pix": 0,
            "k_top_parent": 0,
            "note": "Non-finite or zero total weight; check parallax column / units.",
        }

    theta_c, phi_c = hp.pix2ang(nside, occ_pix, nest=False)
    parent_pix = hp.ang2pix(degrade_to, theta_c, phi_c, nest=False)

    dfw = pd.DataFrame({"parent": parent_pix, "w": w})
    W = dfw.groupby("parent")["w"].sum().to_numpy(dtype=float)

    Wsum = float(W.sum())
    if not np.isfinite(Wsum) or Wsum <= 0.0:
        return {
            "nside": nside,
            "degrade_to": degrade_to,
            "C_0.20": float("nan"),
            "N_parent_pix": int(len(W)),
            "k_top_parent": 0,
            "note": "Non-finite or zero total parent weight; unexpected.",
        }

    W_sorted = np.sort(W)[::-1]
    k = int(np.ceil(top_frac * len(W_sorted)))
    c020 = float(W_sorted[:k].sum() / Wsum)

    return {
        "nside": nside,
        "degrade_to": degrade_to,
        "C_0.20": c020,
        "N_parent_pix": int(len(W_sorted)),
        "k_top_parent": int(k),
    }


def compute_c020_degraded_signed(
    df: pd.DataFrame,
    ra_col: str,
    dec_col: str,
    plx_col: str,
    nside: int,
    top_frac: float,
    degrade_to: int,
) -> dict:
    """
    Primary signed-aggregate metric on a parent grid:
      child: s_c = N_c * median(plx)_c   (SIGNED)
      parent: S_P = sum_c s_c
      weight: W_P = |S_P|
      C0.20 computed on W_P over parent pixels.

    Also returns cancel_ratio = (sum_P |S_P|) / (sum_c |s_c|).
    """
    degrade_to = int(degrade_to)
    nside = int(nside)

    if degrade_to <= 0:
        raise ValueError("degrade_to must be a positive integer.")
    if degrade_to > nside:
        return {
            "nside": nside,
            "degrade_to": degrade_to,
            "C_0.20_signed": float("nan"),
            "N_parent_pix": 0,
            "k_top_parent": 0,
            "cancel_ratio": float("nan"),
            "note": "degrade_to must be <= nside.",
        }

    occ_pix, med_arr, cnt_arr = _group_child_medians_counts(df, ra_col, dec_col, plx_col, nside=nside)
    s = cnt_arr.astype(float) * med_arr  # SIGNED
    sum_abs_s = float(np.sum(np.abs(s)))

    theta_c, phi_c = hp.pix2ang(nside, occ_pix, nest=False)
    parent_pix = hp.ang2pix(degrade_to, theta_c, phi_c, nest=False)

    dfs = pd.DataFrame({"parent": parent_pix, "s": s})
    S = dfs.groupby("parent")["s"].sum().to_numpy(dtype=float)

    W = np.abs(S)
    Wsum = float(W.sum())
    if not np.isfinite(Wsum) or Wsum <= 0.0:
        return {
            "nside": nside,
            "degrade_to": degrade_to,
            "C_0.20_signed": float("nan"),
            "N_parent_pix": int(len(W)),
            "k_top_parent": 0,
            "cancel_ratio": float("nan"),
            "note": "Non-finite or zero total |S_P|; unexpected.",
        }

    cancel_ratio = float(Wsum / sum_abs_s) if (np.isfinite(sum_abs_s) and sum_abs_s > 0.0) else float("nan")

    W_sorted = np.sort(W)[::-1]
    k = int(np.ceil(top_frac * len(W_sorted)))
    c020 = float(W_sorted[:k].sum() / Wsum)

    return {
        "nside": nside,
        "degrade_to": degrade_to,
        "C_0.20_signed": c020,
        "N_parent_pix": int(len(W_sorted)),
        "k_top_parent": int(k),
        "cancel_ratio": cancel_ratio,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", required=True, type=Path, help="Path to analysis-ready parquet")
    ap.add_argument("--nsides", nargs="+", type=int, default=[32, 128])
    ap.add_argument("--top_frac", type=float, default=0.20)

    # Primary metric control
    ap.add_argument(
        "--parent_nside",
        type=int,
        default=64,
        help="Parent NSIDE for the default signed-aggregate concentration (W_P = |sum N*median|).",
    )

    # Optional diagnostics (legacy degraded + signed degraded on arbitrary parent grid)
    ap.add_argument(
        "--degrade_to",
        type=int,
        default=0,
        help="If >0, also print degraded-grid checks on this parent NSIDE (legacy abs-before-sum, and optionally signed).",
    )
    ap.add_argument(
        "--degrade_signed",
        action="store_true",
        help="If set, also compute signed-aggregate degraded concentration on --degrade_to parent grid.",
    )

    # Legacy-only occupancy cut grid
    ap.add_argument(
        "--min_count",
        nargs="*",
        type=int,
        default=[],
        help="Legacy-only: list of minimum per-pixel counts (N_p >= min_count) to apply; prints a grid over (NSIDE x min_count).",
    )

    ap.add_argument("--ra_col", default="", help="Optional explicit RA column name")
    ap.add_argument("--dec_col", default="", help="Optional explicit Dec column name")
    ap.add_argument("--parallax_col", default="", help="Optional explicit parallax column name")
    args = ap.parse_args()

    if not args.parquet.exists():
        raise SystemExit(f"Parquet not found: {args.parquet}")

    # Schema introspection without reading full parquet
    cols = pq.ParquetFile(str(args.parquet)).schema.names

    ra_col = args.ra_col or guess_col(cols, ["ra", "ra_deg", "ra_icrs", "ra_j2000", "ra2000"])
    dec_col = args.dec_col or guess_col(cols, ["dec", "dec_deg", "dec_icrs", "dec_j2000", "dec2000"])
    plx_col = args.parallax_col or guess_col(cols, ["parallax", "plx", "parallax_mas", "varpi"])

    missing = [name for name, val in [("RA", ra_col), ("Dec", dec_col), ("parallax", plx_col)] if val is None]
    if missing:
        print("Required columns not found:", ", ".join(missing))
        print("Detected columns (first 60):", cols[:60])
        print("Tip: re-run with --ra_col/--dec_col/--parallax_col if your names differ.")
        return 2

    df = pd.read_parquet(args.parquet, columns=[ra_col, dec_col, plx_col])

    print("\nNSIDE robustness check (Top-20% concentration)")
    print(f"Parquet: {args.parquet}")
    print(f"Columns: RA={ra_col}  Dec={dec_col}  plx={plx_col}")
    print(f"Top fraction: {args.top_frac:.2f}\n")

    # --- Primary: signed-aggregate on fixed parent NSIDE ---
    parent = int(args.parent_nside)
    print(f"Primary metric: SIGNED-aggregate on parent NSIDE={parent}  (W_P = |sum_c N_c * median(plx)_c|)\n")
    for nside in args.nsides:
        nside_i = int(nside)
        rr = compute_c020_degraded_signed(
            df, ra_col, dec_col, plx_col,
            nside=nside_i, top_frac=args.top_frac, degrade_to=parent
        )
        c = rr["C_0.20_signed"]
        if not np.isfinite(c):
            note = rr.get("note", "nan")
            print(f"NSIDE={nside_i:4d} -> {parent:4d} | C_0.20_signed=nan | note={note}")
        else:
            cr = rr.get("cancel_ratio", float("nan"))
            print(
                f"NSIDE={nside_i:4d} -> {parent:4d} | "
                f"C_0.20_signed={c:.4f} | "
                f"N_parent_pix={rr['N_parent_pix']} | "
                f"k(top parent)={rr['k_top_parent']} | "
                f"cancel_ratio={cr:.4f}"
            )

    # --- Secondary: legacy paper-consistent metric on native NSIDE ---
    print("\nLegacy metric (paper-consistent): w_p = N_p * |median(plx)_p| (computed on the native NSIDE)\n")
    legacy_results: dict[int, dict] = {}
    for nside in args.nsides:
        nside_i = int(nside)
        r = compute_c020(df, ra_col, dec_col, plx_col, nside=nside_i, top_frac=args.top_frac)
        legacy_results[nside_i] = r
        print(
            f"NSIDE={nside_i:4d} | "
            f"C_0.20={r['C_0.20']:.4f} | "
            f"N_pix={r['N_pix']} | "
            f"median src/pix={r['median_sources_per_pixel']} | "
            f"k(top)={r['k_top_pixels']}"
        )

    # Legacy-only occupancy grid
    if args.min_count:
        mins = [int(m) for m in args.min_count]
        print("\nLegacy grid: C_0.20 with occupancy cut (keep legacy pixels with N_p >= min_count)")
        header = "NSIDE  " + "  ".join(f"min{m:>3d}" for m in mins)
        print(header)
        print("-" * len(header))
        for nside in args.nsides:
            nside_i = int(nside)
            row = [f"{nside_i:5d}"]
            for m in mins:
                rr = compute_c020_min_count(
                    df, ra_col, dec_col, plx_col,
                    nside=nside_i, top_frac=args.top_frac, min_count=m
                )
                c = rr["C_0.20"]
                row.append(f"{c:7.4f}" if np.isfinite(c) else "   nan ")
            print("  ".join(row))

    # Optional: degraded-grid diagnostics on arbitrary parent grid
    if args.degrade_to and int(args.degrade_to) > 0:
        dt = int(args.degrade_to)
        print(f"\nDegraded-grid diagnostic (LEGACY): aggregate w_c=N_c*|median_c| into parent NSIDE={dt}")
        for nside in args.nsides:
            nside_i = int(nside)
            rr = compute_c020_degraded(
                df, ra_col, dec_col, plx_col,
                nside=nside_i, top_frac=args.top_frac, degrade_to=dt
            )
            c = rr["C_0.20"]
            if not np.isfinite(c):
                note = rr.get("note", "nan")
                print(f"NSIDE={nside_i:4d} -> {dt:4d} | C_0.20=nan | note={note}")
            else:
                print(
                    f"NSIDE={nside_i:4d} -> {dt:4d} | "
                    f"C_0.20={c:.4f} | "
                    f"N_parent_pix={rr['N_parent_pix']} | "
                    f"k(top parent)={rr['k_top_parent']}"
                )

        if args.degrade_signed:
            print(f"\nDegraded-grid diagnostic (SIGNED): W_P=|sum_c (N_c*median_c)| into parent NSIDE={dt}")
            for nside in args.nsides:
                nside_i = int(nside)
                rr = compute_c020_degraded_signed(
                    df, ra_col, dec_col, plx_col,
                    nside=nside_i, top_frac=args.top_frac, degrade_to=dt
                )
                c = rr["C_0.20_signed"]
                if not np.isfinite(c):
                    note = rr.get("note", "nan")
                    print(f"NSIDE={nside_i:4d} -> {dt:4d} | C_0.20_signed=nan | note={note}")
                else:
                    cr = rr.get("cancel_ratio", float("nan"))
                    print(
                        f"NSIDE={nside_i:4d} -> {dt:4d} | "
                        f"C_0.20_signed={c:.4f} | "
                        f"N_parent_pix={rr['N_parent_pix']} | "
                        f"k(top parent)={rr['k_top_parent']} | "
                        f"cancel_ratio={cr:.4f}"
                    )

    # Keep your legacy delta line (explicitly legacy)
    if 32 in legacy_results and 128 in legacy_results:
        delta = legacy_results[128]["C_0.20"] - legacy_results[32]["C_0.20"]
        print(f"\nLegacy ΔC_0.20 (128 − 32) = {delta:+.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

