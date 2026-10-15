import numpy as np
import pytest

from wqub.conformal import conformal_interval, density_ratio, weighted_quantile_inf
from wqub.data import Data
from wqub.metrics import brier, coverage, ece, interval_score, reliability_bins
from wqub.models import Pred


def _data(x, y):
    n = len(y)
    return Data(np.zeros((n, 0)), np.column_stack([x, np.zeros(n)]), y, np.zeros(n, int), 1.0)


def _pred(mean, half):
    return Pred(mean, mean - half, mean + half, np.zeros(len(mean)))


def test_weighted_quantile_matches_split_conformal_index():
    scores = np.arange(1, 100, dtype=float)
    assert weighted_quantile_inf(scores, np.ones(99), 1.0, 0.1)[0] == 90.0  # ceil(100 * 0.9)


@pytest.mark.parametrize("method", ["split", "cqr", "split+local", "cqr+iw"])
def test_exchangeable_data_reaches_nominal_coverage(method, cfg):
    rng = np.random.default_rng(5)
    xc, xt = rng.uniform(0, 100, 500), rng.uniform(0, 100, 3000)
    yc, yt = rng.normal(0, 1, 500), rng.normal(0, 1, 3000)
    Dc, Dt = _data(xc, yc), _data(xt, yt)
    lo, hi = conformal_interval(method, _pred(np.zeros(500), 0.5), Dc, _pred(np.zeros(3000), 0.5), Dt, 0.2, cfg)
    assert abs(coverage(yt, lo, hi) - 0.8) < 0.04


def test_importance_weights_near_one_without_shift():
    rng = np.random.default_rng(1)
    wc, wt = density_ratio(rng.normal(size=(800, 2)), rng.normal(size=(800, 2)), (0.05, 20.0))
    assert abs(wc.mean() - 1) < 0.3 and abs(wt.mean() - 1) < 0.3


def test_importance_weighting_helps_under_covariate_shift(cfg):
    rng = np.random.default_rng(7)
    xc, xt = rng.normal(0, 1, 3000), rng.normal(2.0, 1, 3000)
    yc, yt = rng.normal(0, 1 + np.abs(xc)), rng.normal(0, 1 + np.abs(xt))
    Dc, Dt = _data(xc, yc), _data(xt, yt)
    zero = np.zeros(3000)
    cov = {}
    for m in ("split", "split+iw"):
        lo, hi = conformal_interval(m, _pred(zero, 0.0), Dc, _pred(zero, 0.0), Dt, 0.2, cfg)
        cov[m] = coverage(yt, lo, hi)
    assert cov["split+iw"] > cov["split"] + 0.03


def test_metric_values():
    assert interval_score(np.array([0.0]), np.array([-1.0]), np.array([1.0]), 0.2) == pytest.approx(2.0)
    assert interval_score(np.array([2.0]), np.array([-1.0]), np.array([1.0]), 0.2) == pytest.approx(2.0 + 10.0)
    rng = np.random.default_rng(0)
    p = rng.uniform(0, 1, 20000)
    obs = (rng.uniform(0, 1, 20000) < p).astype(int)
    assert ece(obs, p) < 0.02 and brier(obs, p) < 0.18
    assert sum(b[1] for b in reliability_bins(obs, p)) == 20000
