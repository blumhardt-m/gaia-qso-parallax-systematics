from __future__ import annotations

import numpy as np
import healpy as hp

def radec_to_pix(ra_deg: np.ndarray, dec_deg: np.ndarray, nside: int) -> np.ndarray:
    """Convert RA/Dec in degrees to HEALPix RING pixel indices."""
    ra = np.asarray(ra_deg, dtype=float)
    dec = np.asarray(dec_deg, dtype=float)
    theta = np.deg2rad(90.0 - dec)  # colatitude
    phi = np.deg2rad(ra)
    return hp.ang2pix(nside, theta, phi, nest=False)

def per_pix_median_bootstrap(
    values: np.ndarray,
    pix: np.ndarray,
    nside: int,
    min_count: int = 50,
    n_boot: int = 60,
    seed: int = 0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per-pixel median and bootstrap std error of the median."""
    vals = np.asarray(values, dtype=float)
    pix = np.asarray(pix, dtype=np.int64)

    npix = hp.nside2npix(nside)
    med = np.full(npix, np.nan, dtype=float)
    se = np.full(npix, np.nan, dtype=float)
    cnt = np.zeros(npix, dtype=np.int64)

    m = np.isfinite(vals)
    vals = vals[m]
    pix = pix[m]

    order = np.argsort(pix)
    pix_s = pix[order]
    val_s = vals[order]

    boundaries = np.r_[0, np.where(np.diff(pix_s) != 0)[0] + 1, len(pix_s)]
    rng = np.random.default_rng(seed)

    for a, b in zip(boundaries[:-1], boundaries[1:]):
        p = int(pix_s[a])
        v = val_s[a:b]
        c = len(v)
        cnt[p] = c
        if c < min_count:
            continue
        med[p] = float(np.median(v))
        if n_boot > 0:
            idx = rng.integers(0, c, size=(n_boot, c))
            boots = np.median(v[idx], axis=1)
            se[p] = float(np.std(boots, ddof=1))

    return med, se, cnt
