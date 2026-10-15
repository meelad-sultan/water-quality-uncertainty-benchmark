"""Dataset container and CSV loader for real monitoring data."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

from wqub.coords import project_km


@dataclass
class Data:
    X: np.ndarray  # covariates (n, p); may have zero columns
    coords: np.ndarray  # projected km (n, 2)
    y: np.ndarray  # target on the log1p scale
    region: np.ndarray  # integer region labels
    limit: float  # exceedance threshold on the log1p scale
    t: np.ndarray | None = None  # time in years
    site: np.ndarray | None = None  # site ids (repeated measurements)
    names: list = field(default_factory=list)
    meta: dict = field(default_factory=dict)
    lonlat: np.ndarray | None = None

    def __len__(self) -> int:
        return len(self.y)

    @property
    def exceed(self) -> np.ndarray:
        return (self.y > self.limit).astype(int)

    def features(self) -> np.ndarray:
        parts = [self.X, self.coords]
        if self.t is not None:
            parts.append(self.t[:, None])
        return np.hstack(parts)

    def subset(self, idx) -> Data:
        idx = np.asarray(idx)
        return Data(self.X[idx], self.coords[idx], self.y[idx], self.region[idx], self.limit,
                    None if self.t is None else self.t[idx], None if self.site is None else self.site[idx], self.names, self.meta,
                    None if self.lonlat is None else self.lonlat[idx])


def load_csv(cfg: dict) -> Data:
    """Load a monitoring CSV using the column mapping in ``cfg['real']``."""
    r = cfg["real"]
    c = r["columns"]
    df = pd.read_csv(r["path"])
    need = [c["lat"], c["lon"], c["target"]]
    n0 = len(df)
    df = df.dropna(subset=need).copy()
    val = pd.to_numeric(df[c["target"]], errors="coerce")
    df = df[val.notna()].copy()
    val = val[val.notna()]
    mode = r.get("nonpositive", "half_min")
    if mode == "zero":  # non-detects are recorded as 0 and kept as 0 (e.g. field test kits)
        val = val.clip(lower=0)
    elif (val <= 0).any():
        if mode == "drop":
            df, val = df[val > 0], val[val > 0]
        else:  # replace non-positive (e.g. below detection limit) by half of the smallest positive value
            floor = 0.5 * val[val > 0].min()
            val = val.where(val > 0, floor)
    covs = c.get("covariates") or []
    if covs == "all":
        skip = {c["lat"], c["lon"], c["target"], c.get("time"), c.get("site"), c.get("region")}
        covs = [k for k in df.columns if k not in skip and pd.api.types.is_numeric_dtype(df[k])]
    covs = list(covs)
    X = df[covs].apply(pd.to_numeric, errors="coerce") if covs else pd.DataFrame(index=df.index)
    miss = float(X.isna().mean().mean()) if covs else 0.0
    X = X.fillna(X.median()) if covs else X
    lat, lon = pd.to_numeric(df[c["lat"]]).to_numpy(float), pd.to_numeric(df[c["lon"]]).to_numpy(float)
    if r.get("coords") == "global":  # plate carree in km: only used for grouping and as a rough location feature
        coords = np.column_stack([lon * 111.32, lat * 111.32])
        sph = np.column_stack([np.cos(np.radians(lat)) * np.cos(np.radians(lon)), np.cos(np.radians(lat)) * np.sin(np.radians(lon)), np.sin(np.radians(lat))])
    else:
        coords = project_km(lat, lon)
        sph = coords
    if c.get("region"):
        region = pd.factorize(df[c["region"]])[0]
    else:
        k = int(r.get("region_clusters", 5))
        region = KMeans(n_clusters=k, n_init=10, random_state=0).fit_predict(sph)
    t = pd.to_numeric(df[c["time"]]).to_numpy(float) if c.get("time") else None
    site = pd.factorize(df[c["site"]])[0] if c.get("site") else None
    y = np.log1p(val.to_numpy(float))
    meta = {"name": r.get("name", "real"), "n_rows_in_file": n0, "n_used": len(df), "covariate_missing_fraction": miss,
            "limit_raw": r["limit"], "limit_note": r.get("limit_note", ""), "target_column": c["target"]}
    return Data(X.to_numpy(float), coords, y, region, float(np.log1p(r["limit"])), t, site, covs, meta, np.column_stack([lon, lat]))


def summarize(D: Data) -> dict:
    return {"n": len(D), "regions": {int(k): int((D.region == k).sum()) for k in np.unique(D.region)},
            "target_log1p_mean": float(D.y.mean()), "target_log1p_sd": float(D.y.std()),
            "exceedance_rate": float(D.exceed.mean()), "covariates": D.names, "has_time": D.t is not None, "meta": D.meta}
