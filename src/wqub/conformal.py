"""Conformal prediction variants: split and CQR scores, with optional spatial-kernel or importance weighting.

method = "none" (model's own interval) | "<score>" | "<score>+<weighting>" with
score in {split, cqr} and weighting in {local, iw}.
  split : |y - mean| residual scores           -> mean +/- q
  cqr   : max(lo - y, y - hi) (Romano et al.)  -> [lo - q, hi + q]
  local : calibration scores weighted by a Gaussian kernel of spatial distance to the test point
  iw    : calibration scores weighted by an estimated density ratio p_test(x)/p_cal(x) (Tibshirani et al. 2019)
"""
from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


def weighted_quantile_inf(scores, w, w_test, alpha):
    """(1-alpha) quantile of the weighted score distribution with the test point's mass placed at +infinity.

    ``w_test`` may be an array (one weight per test point). Returns the largest calibration score where the
    quantile falls beyond the calibration set (conservative, finite)."""
    order = np.argsort(scores)
    s, ww = scores[order], w[order]
    cum, total = np.cumsum(ww), ww.sum()
    thr = (1 - alpha) * (total + np.atleast_1d(w_test))
    idx = np.searchsorted(cum, thr, side="left")
    return s[np.minimum(idx, len(s) - 1)]


def density_ratio(Fc, Ft, clip):
    sc = StandardScaler().fit(np.vstack([Fc, Ft]))
    Z = sc.transform(np.vstack([Fc, Ft]))
    lab = np.r_[np.zeros(len(Fc)), np.ones(len(Ft))]
    clf = LogisticRegression(C=1.0, max_iter=500).fit(Z, lab)
    p = np.clip(clf.predict_proba(Z)[:, 1], 1e-4, 1 - 1e-4)
    ratio = np.clip(p / (1 - p) * (len(Fc) / len(Ft)), clip[0], clip[1])
    return ratio[: len(Fc)], ratio[len(Fc):]


def conformal_interval(method, pc, Dc, pt, Dt, alpha, cfg):
    if method == "none":
        return pt.lo, pt.hi
    base, _, weighting = method.partition("+")
    scores = np.abs(Dc.y - pc.mean) if base == "split" else np.maximum(pc.lo - Dc.y, Dc.y - pc.hi)
    n_t = len(Dt)
    if weighting == "":
        q = np.full(n_t, weighted_quantile_inf(scores, np.ones(len(scores)), 1.0, alpha)[0])
    elif weighting == "iw":
        wc, wt = density_ratio(Dc.features(), Dt.features(), cfg["cv"]["iw_clip"])
        q = weighted_quantile_inf(scores, wc, wt, alpha)
    elif weighting == "local":
        h = cfg["cv"]["local_bandwidth_km"]
        order = np.argsort(scores)
        s_sorted, cc = scores[order], Dc.coords[order]
        q = np.empty(n_t)
        for a in range(0, n_t, 400):  # chunked: weights of every calibration point for each test point in the chunk
            d2 = ((Dt.coords[a:a + 400, None, :] - cc[None, :, :]) ** 2).sum(-1)
            cum = np.cumsum(np.exp(-d2 / (2 * h * h)) + 1e-12, axis=1)
            idx = (cum < (1 - alpha) * (cum[:, -1] + 1.0)[:, None]).sum(axis=1)
            q[a:a + 400] = s_sorted[np.minimum(idx, len(s_sorted) - 1)]
    else:
        raise ValueError(f"unknown weighting {weighting}")
    return (pt.mean - q, pt.mean + q) if base == "split" else (pt.lo - q, pt.hi + q)
