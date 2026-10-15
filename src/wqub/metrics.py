"""Accuracy, interval and probability metrics."""
from __future__ import annotations

import numpy as np


def rmse(y, p):
    return float(np.sqrt(np.mean((y - p) ** 2)))


def mae(y, p):
    return float(np.mean(np.abs(y - p)))


def r2(y, p):
    ss = np.sum((y - y.mean()) ** 2)
    return float(1 - np.sum((y - p) ** 2) / ss) if ss > 0 else float("nan")


def coverage(y, lo, hi):
    return float(np.mean((y >= lo) & (y <= hi)))


def mean_width(lo, hi):
    return float(np.mean(hi - lo))


def interval_score(y, lo, hi, alpha):
    """Winkler interval score (lower is better): width plus penalised misses."""
    return float(np.mean((hi - lo) + (2 / alpha) * (lo - y) * (y < lo) + (2 / alpha) * (y - hi) * (y > hi)))


def brier(obs, p):
    return float(np.mean((p - obs) ** 2))


def reliability_bins(obs, p, n_bins=10):
    idx = np.minimum((np.clip(p, 0, 1) * n_bins).astype(int), n_bins - 1)
    return [(b, int((idx == b).sum()), float(p[idx == b].sum()), float(obs[idx == b].sum())) for b in range(n_bins) if (idx == b).any()]


def ece(obs, p, n_bins=10):
    bins = reliability_bins(obs, p, n_bins)
    n = len(obs)
    return float(sum(abs(so - sp) for _, _, sp, so in bins) / n)
