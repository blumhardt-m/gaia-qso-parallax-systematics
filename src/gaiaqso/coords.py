from __future__ import annotations

import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord, GeocentricTrueEcliptic
import astropy.units as u

def add_ecliptic_latitude(df: pd.DataFrame) -> pd.DataFrame:
    """Add ecliptic latitude features: ecl_lat_deg and sin_ecl_lat."""
    coords = SkyCoord(
        ra=df["ra"].to_numpy() * u.deg,
        dec=df["dec"].to_numpy() * u.deg,
        frame="icrs",
    )
    ecl = coords.transform_to(GeocentricTrueEcliptic())
    lat = ecl.lat.to_value(u.deg)

    out = df.copy()
    out["ecl_lat_deg"] = lat
    out["sin_ecl_lat"] = np.sin(np.deg2rad(lat))
    return out
