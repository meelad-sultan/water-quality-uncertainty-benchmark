import numpy as np

from wqub.splits import block_folds, random_folds, region_folds, site_folds, time_split
from wqub.synth import make_synthetic


def test_synthetic_is_deterministic_and_shifted(cfg):
    a, b = make_synthetic(cfg, np.random.default_rng(1)), make_synthetic(cfg, np.random.default_rng(1))
    np.testing.assert_array_equal(a.y, b.y)
    assert abs(a.exceed.mean() - 0.2) < 0.02
    assert a.y[a.region == 3].mean() > a.y[a.region != 3].mean() + 0.5


def test_temporal_data_shape(cfg):
    D = make_synthetic(cfg, np.random.default_rng(2), temporal=True)
    t = cfg["synthetic"]["temporal"]
    assert len(D) == t["n_sites"] * t["obs_per_site"] and D.t is not None and D.site is not None
    assert D.features().shape[1] == D.X.shape[1] + 3


def _check_partition(folds, n):
    seen = np.concatenate([f["test"] for f in folds])
    assert len(seen) == len(set(seen)) and set(seen) <= set(range(n))
    for f in folds:
        assert not set(f["train"]) & set(f["test"]) and len(f["train"]) + len(f["test"]) == n


def test_random_and_block_folds_partition(small):
    rng = np.random.default_rng(0)
    _check_partition(random_folds(len(small), 4, rng), len(small))
    folds = block_folds(small.coords, 4, 80.0, rng)
    _check_partition(folds, len(small))
    blk = lambda idx: set(map(tuple, np.floor(small.coords[idx] / 80.0).astype(int)))  # noqa: E731
    for f in folds:
        assert not blk(f["train"]) & blk(f["test"])


def test_region_time_site_folds(cfg):
    D = make_synthetic(cfg, np.random.default_rng(2), temporal=True)
    for f in region_folds(D.region):
        assert len(set(D.region[f["test"]])) == 1 and f["fold"] not in set(D.region[f["train"]])
    f = time_split(D.t)[0]
    assert D.t[f["train"]].max() < f["cut"] <= D.t[f["test"]].min()
    for f in site_folds(D.site, 4, np.random.default_rng(0)):
        assert not set(D.site[f["train"]]) & set(D.site[f["test"]])
