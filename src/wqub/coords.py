"""Simple local projection of lat/lon to kilometres (adequate for regional extents)."""
from __future__ import annotations

import numpy as np

EARTH_RADIUS_KM = 6371.0088


def project_km(lat, lon, lat0=None, lon0=None):
    lat, lon = np.asarray(lat, float), np.asarray(lon, float)
    lat0 = float(np.mean(lat)) if lat0 is None else lat0
    lon0 = float(np.mean(lon)) if lon0 is None else lon0
    x = EARTH_RADIUS_KM * np.radians(lon - lon0) * np.cos(np.radians(lat0))
    y = EARTH_RADIUS_KM * np.radians(lat - lat0)
    return np.column_stack([x, y])
