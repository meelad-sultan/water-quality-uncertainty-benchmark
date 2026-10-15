"""Synthetic monitoring data with a known data-generating process.

Spatially correlated latent field + covariate effects + heteroscedastic noise + a region (region 3) whose covariates,
mean level and noise differ from the others, so distribution shift is controlled. Optional seasonal/trend/site effects.
"""
from __future__ import annotations

import numpy as np

from wqub.data import Data


def _rff_field(coords, rng, range_km, sd, m=300):
    w = rng.normal(0.0, 1.0 / range_km, size=(m, 2))
    b = rng.uniform(0, 2 * np.pi, m)
    return sd * np.sqrt(2.0 / m) * np.cos(coords @ w.T + b).sum(axis=1)


def _sites(n, extent, k, rng):
    centers = rng.uniform(0.1 * extent, 0.9 * extent, (k, 2))
    n_cl = int(0.8 * n)
    pts = centers[rng.integers(0, k, n_cl)] + rng.normal(0, 0.06 * extent, (n_cl, 2))
    pts = np.vstack([pts, rng.uniform(0, extent, (n - n_cl, 2))])
    return np.clip(pts, 0, extent)


def make_synthetic(cfg: dict, rng: np.random.Generator, temporal: bool = False) -> Data:
    s = cfg["synthetic"]
    ext = float(s["extent_km"])
    tcfg = s.get("temporal", {})
    n_sites = int(tcfg["n_sites"] if temporal else s["n_sites"])
    coords = _sites(n_sites, ext, int(s["n_clusters"]), rng)
    region = (coords[:, 0] > ext / 2).astype(int) + 2 * (coords[:, 1] > ext / 2).astype(int)
    field = _rff_field(coords, rng, s["field_range_km"], s["field_sd"])
    shifted = region == 3
    sh = s["shift"]
    c1 = 0.6 * field + rng.normal(0, 0.5, n_sites) + sh["covariate_shift"] * shifted
    river = ext / 2 + 0.2 * ext * np.sin(2 * np.pi * coords[:, 0] / ext)
    c2 = np.abs(coords[:, 1] - river) / ext
    c3 = rng.normal(0, 1, n_sites) + 0.5 * sh["covariate_shift"] * shifted
    mean = 0.8 * c1 + 0.6 * np.tanh(2 * (c2 - 0.3)) + field + sh["region_offset"] * shifted
    noise_sd = s["noise_sd"] * (1 + sh["noise_inflation"] * shifted)
    X = np.column_stack([c1, c2, c3])
    if not temporal:
        z = mean + rng.normal(0, 1, n_sites) * noise_sd
        t = site = None
    else:
        m_obs, years = int(tcfg["obs_per_site"]), float(tcfg["years"])
        site = np.repeat(np.arange(n_sites), m_obs)
        t = np.sort(rng.uniform(0, years, (n_sites, m_obs)), axis=1).ravel()
        phase = 0.5 * np.pi * _rff_field(coords, rng, 120.0, 1.0)
        slope = np.array([0.05, -0.03, 0.10, 0.20])[region]
        u = rng.normal(0, 0.3, n_sites)
        seasonal = 0.4 * np.sin(2 * np.pi * t + np.repeat(phase, m_obs))
        z = (np.repeat(mean, m_obs) + np.repeat(u, m_obs) + seasonal + np.repeat(slope, m_obs) * (t - years / 2)
             + rng.normal(0, 1, len(t)) * np.repeat(noise_sd, m_obs))
        coords, X, region = np.repeat(coords, m_obs, axis=0), np.repeat(X, m_obs, axis=0), np.repeat(region, m_obs)
    y = z - z.min()  # log1p-scale concentration, non-negative
    limit = float(np.quantile(y, s["exceed_quantile"]))
    return Data(X, coords, y, region, limit, t, site, ["c1", "c2", "c3"], {"name": "synthetic", "temporal": temporal})
