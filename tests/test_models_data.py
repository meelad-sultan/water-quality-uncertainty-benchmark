import numpy as np
import pandas as pd
import yaml

from wqub.data import load_csv, summarize
from wqub.experiments import run_all
from wqub.metrics import rmse
from wqub.models import make_model
from wqub.plotting import make_all
from wqub.splits import random_folds
from wqub.summary import summarize as summarize_results


def test_models_predict_sensibly(cfg, small):
    f = random_folds(len(small), 4, np.random.default_rng(0))[0]
    Dtr, Dte = small.subset(f["train"]), small.subset(f["test"])
    scores = {}
    for name in ("naive", "idw", "gp", "qgbm"):
        p = make_model(name, cfg, 0).fit(Dtr).predict(Dte, 0.2)
        assert np.isfinite(p.mean).all() and (p.lo <= p.hi).all() and ((p.p_exceed >= 0) & (p.p_exceed <= 1)).all()
        assert (p.lo <= p.mean + 1e-9).all() and (p.mean <= p.hi + 1e-9).all()
        scores[name] = rmse(Dte.y, p.mean)
    assert scores["gp"] < scores["naive"] and scores["qgbm"] < scores["naive"]


def _csv(tmp_path, cfg_small):
    from wqub.synth import make_synthetic

    D = make_synthetic(cfg_small, np.random.default_rng(4))
    lat = 30.0 + D.coords[:, 1] / 111.0
    lon = 72.0 + D.coords[:, 0] / (111.0 * np.cos(np.radians(30.0)))
    df = pd.DataFrame({"lat": lat, "lon": lon, "arsenic": np.expm1(D.y), "c1": D.X[:, 0], "c2": D.X[:, 1]})
    df.loc[0, "arsenic"] = 0.0  # below detection limit
    df.loc[1, "lat"] = np.nan  # dropped
    df.loc[2, "c1"] = np.nan  # imputed
    p = tmp_path / "obs.csv"
    df.to_csv(p, index=False)
    return p, len(df)


def test_csv_loader_and_summary(tmp_path, cfg_copy):
    p, n = _csv(tmp_path, cfg_copy)
    cfg_copy["real"] = {"path": str(p), "name": "t", "columns": {"lat": "lat", "lon": "lon", "target": "arsenic", "covariates": ["c1", "c2"]},
                        "limit": 5.0, "region_clusters": 4}
    D = load_csv(cfg_copy)
    assert len(D) == n - 1 and D.X.shape == (n - 1, 2) and np.isfinite(D.X).all() and (D.y >= 0).all()
    assert abs(D.limit - np.log1p(5.0)) < 1e-12 and set(summarize(D)) >= {"n", "exceedance_rate", "regions"}


def test_end_to_end_synthetic_and_real(tmp_path, cfg):
    base = yaml.safe_load(open("configs/quick.yaml"))
    base["extends"] = str(__import__("pathlib").Path("configs/default.yaml").resolve())
    base["synthetic"]["n_sites"] = 220
    base["synthetic"]["temporal"] = {"n_sites": 50, "obs_per_site": 6, "years": 3}
    base["models"], base["methods"] = ["naive", "gp", "qgbm"], ["none", "split", "cqr", "cqr+iw", "cqr+local"]
    p, _ = _csv(tmp_path, cfg)
    base["real"] = {"path": str(p), "name": "t", "columns": {"lat": "lat", "lon": "lon", "target": "arsenic", "covariates": ["c1", "c2"]},
                    "limit": 5.0, "region_clusters": 4}
    cfgp = tmp_path / "c.yaml"
    cfgp.write_text(yaml.safe_dump(base))
    out = tmp_path / "res"
    run_all(cfgp, out, "synthetic")
    run_all(cfgp, out, "real")
    for f in ("cv_study.csv", "reliability.csv", "scarcity.csv", "spatiotemporal.csv", "real_cv_study.csv", "real_scarcity.csv", "real_data_summary.json"):
        assert (out / f).exists()
    assert len(make_all(out, tmp_path / "fig")) >= 12
    s = summarize_results(out)
    assert "Synthetic benchmark" in s and "Real data" in s
