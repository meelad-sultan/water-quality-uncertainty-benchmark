"""Validation schemes: random, spatial-block, leave-region-out, forward-in-time, leave-site-out."""
from __future__ import annotations

import numpy as np


def _balanced(groups: dict, k: int, rng):
    keys = list(groups)
    rng.shuffle(keys)
    keys.sort(key=lambda g: -len(groups[g]))
    folds, sizes = [[] for _ in range(k)], np.zeros(k)
    for g in keys:
        j = int(np.argmin(sizes))
        folds[j].extend(groups[g])
        sizes[j] += len(groups[g])
    return [np.array(sorted(f)) for f in folds if len(f)]


def _pairs(n, test_sets, name):
    allidx = np.arange(n)
    out = []
    for i, te in enumerate(test_sets):
        mask = np.ones(n, bool)
        mask[te] = False
        out.append({"scheme": name, "fold": i, "train": allidx[mask], "test": te})
    return out


def random_folds(n, k, rng):
    perm = rng.permutation(n)
    return _pairs(n, [np.sort(f) for f in np.array_split(perm, k)], "random")


def block_folds(coords, k, block_km, rng):
    bx, by = np.floor(coords[:, 0] / block_km).astype(int), np.floor(coords[:, 1] / block_km).astype(int)
    groups: dict = {}
    for i, key in enumerate(zip(bx, by, strict=True)):
        groups.setdefault(key, []).append(i)
    return _pairs(len(coords), _balanced(groups, k, rng), "block")


def region_folds(region, min_n=30):
    n = len(region)
    tests = [np.flatnonzero(region == r) for r in np.unique(region) if (region == r).sum() >= min_n]
    out = _pairs(n, tests, "region")
    for f, te in zip(out, tests, strict=True):
        f["fold"] = int(region[te[0]])
    return out


def time_split(t, frac=0.7):
    cut = float(np.quantile(t, frac))
    te = np.flatnonzero(t >= cut)
    out = _pairs(len(t), [te], "time")
    out[0]["cut"] = cut
    return out


def site_folds(site, k, rng):
    groups: dict = {}
    for i, s in enumerate(site):
        groups.setdefault(int(s), []).append(i)
    return _pairs(len(site), _balanced(groups, k, rng), "site")


def box_folds(lonlat, boxes, min_n=30):
    """Hold out every point inside a lat/lon box (transfer test); boxes: [{name, lat: [a, b], lon: [c, d]}]."""
    n = len(lonlat)
    tests, names = [], []
    for b in boxes:
        m = (lonlat[:, 1] >= b["lat"][0]) & (lonlat[:, 1] <= b["lat"][1]) & (lonlat[:, 0] >= b["lon"][0]) & (lonlat[:, 0] <= b["lon"][1])
        if m.sum() >= min_n:
            tests.append(np.flatnonzero(m))
            names.append(b["name"])
    out = _pairs(n, tests, "box")
    for f, nm in zip(out, names, strict=True):
        f["label"] = nm
    return out
