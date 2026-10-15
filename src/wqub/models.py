"""Prediction models. Each returns a mean, a native 1-alpha interval and an exceedance probability."""
from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
from scipy.stats import norm
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel
from sklearn.linear_model import Ridge
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

from wqub.data import Data


@dataclass
class Pred:
    mean: np.ndarray
    lo: np.ndarray
    hi: np.ndarray
    p_exceed: np.ndarray


def _gauss(mean, std, alpha, limit) -> Pred:
    std = np.maximum(std, 1e-6)
    z = norm.ppf(1 - alpha / 2)
    return Pred(mean, mean - z * std, mean + z * std, 1 - norm.cdf((limit - mean) / std))


class NaiveModel:
    """Global mean and standard deviation: the baseline every model must beat."""

    def fit(self, D: Data):
        self.m, self.s, self.limit = float(D.y.mean()), float(D.y.std()), D.limit
        return self

    def predict(self, D: Data, alpha: float) -> Pred:
        n = len(D)
        return _gauss(np.full(n, self.m), np.full(n, self.s), alpha, self.limit)


class IDWModel:
    """Inverse-distance-weighted neighbours (spatial only); local spread gives the uncertainty."""

    def __init__(self, k=8, power=2.0):
        self.k, self.power = k, power

    def fit(self, D: Data):
        self.y, self.limit = D.y, D.limit
        self.nn = NearestNeighbors(n_neighbors=min(self.k, len(D))).fit(D.coords)
        return self

    def predict(self, D: Data, alpha: float) -> Pred:
        d, idx = self.nn.kneighbors(D.coords)
        w = 1.0 / (d + 1e-3) ** self.power
        yn = self.y[idx]
        mean = (w * yn).sum(1) / w.sum(1)
        std = np.sqrt((w * (yn - mean[:, None]) ** 2).sum(1) / w.sum(1))
        return _gauss(mean, np.maximum(std, 0.05), alpha, self.limit)


class GPModel:
    """Universal kriging: ridge on covariates (and time), Matern-3/2 Gaussian process on the residuals."""

    def __init__(self, max_n=400, seed=0):
        self.max_n, self.seed = max_n, seed

    def _lin(self, D):
        return np.hstack([D.X] + ([D.t[:, None]] if D.t is not None else [])) if (D.X.shape[1] or D.t is not None) else np.zeros((len(D), 0))

    def _gpin(self, D):
        return np.column_stack([D.coords, D.t]) if D.t is not None else D.coords

    def fit(self, D: Data):
        self.limit, self.has_t = D.limit, D.t is not None
        L = self._lin(D)
        self.sc = StandardScaler().fit(L) if L.shape[1] else None
        self.lin = Ridge(alpha=1.0).fit(self.sc.transform(L), D.y) if L.shape[1] else None
        base = self.lin.predict(self.sc.transform(L)) if self.lin else np.full(len(D), D.y.mean())
        self.base_const = float(D.y.mean())
        rng = np.random.default_rng(self.seed)
        idx = np.arange(len(D)) if len(D) <= self.max_n else np.sort(rng.choice(len(D), self.max_n, replace=False))
        ls = [60.0, 60.0] + ([1.0] if self.has_t else [])
        kern = ConstantKernel(0.5, (1e-3, 1e2)) * Matern(length_scale=ls, length_scale_bounds=(0.1, 1000.0), nu=1.5) + WhiteKernel(0.1, (1e-4, 2.0))
        self.gp = GaussianProcessRegressor(kern, normalize_y=True, n_restarts_optimizer=0, random_state=self.seed)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # length-scale bound warnings are expected for smooth fields
            self.gp.fit(self._gpin(D)[idx], (D.y - base)[idx])
        return self

    def predict(self, D: Data, alpha: float) -> Pred:
        L = self._lin(D)
        base = self.lin.predict(self.sc.transform(L)) if self.lin else np.full(len(D), self.base_const)
        m, s = self.gp.predict(self._gpin(D), return_std=True)
        return _gauss(base + m, s, alpha, self.limit)


class QGBMModel:
    """Gradient boosting with quantile loss for the interval, plus a classifier for the exceedance probability."""

    def __init__(self, cfg: dict, seed=0):
        self.p, self.seed = cfg["qgbm"], seed

    def _reg(self, **kw):
        return HistGradientBoostingRegressor(max_iter=self.p["max_iter"], learning_rate=self.p["learning_rate"], max_leaf_nodes=self.p["max_leaf_nodes"],
                                             min_samples_leaf=self.p["min_samples_leaf"], random_state=self.seed, **kw)

    def fit(self, D: Data, alpha: float | None = None):
        self.alpha = None
        self.F, self.D = D.features(), D
        self.limit, self._yc = D.limit, D.exceed
        self.base_rate = float(self._yc.mean())
        self._D = D
        return self

    def predict(self, D: Data, alpha: float) -> Pred:
        if self.alpha != alpha:  # (re)fit the three quantile models for this alpha
            qs = (alpha / 2, 0.5, 1 - alpha / 2)
            self.models = [self._reg(loss="quantile", quantile=q).fit(self.F, self.D.y) for q in qs]
            if 0 < self._yc.sum() < len(self._yc):
                self.clf = HistGradientBoostingClassifier(max_iter=self.p["max_iter"], learning_rate=self.p["learning_rate"], max_leaf_nodes=self.p["max_leaf_nodes"],
                                                          min_samples_leaf=self.p["min_samples_leaf"], random_state=self.seed).fit(self.F, self._yc)
            else:
                self.clf = None
            self.alpha = alpha
        F = D.features()
        q = np.sort(np.column_stack([m.predict(F) for m in self.models]), axis=1)
        p = self.clf.predict_proba(F)[:, 1] if self.clf is not None else np.full(len(D), self.base_rate)
        return Pred(q[:, 1], q[:, 0], q[:, 2], p)


def make_model(name: str, cfg: dict, seed: int = 0):
    if name == "naive":
        return NaiveModel()
    if name == "idw":
        return IDWModel()
    if name == "gp":
        return GPModel(cfg["gp"]["max_n"], seed)
    if name == "qgbm":
        return QGBMModel(cfg, seed)
    raise ValueError(f"unknown model {name}")
