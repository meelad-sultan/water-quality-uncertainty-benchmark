"""Experiments: cross-validation optimism and conformal calibration under shift, data scarcity, spatiotemporal forecasting."""
from __future__ import annotations

import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from wqub import __version__
from wqub.config import load_config
from wqub.conformal import conformal_interval
from wqub.data import load_csv, summarize
from wqub.metrics import brier, coverage, ece, interval_score, mae, mean_width, r2, reliability_bins, rmse
from wqub.models import make_model
from wqub.splits import block_folds, box_folds, random_folds, region_folds, site_folds, time_split
from wqub.synth import make_synthetic


def rng_for(seed, *keys):
    return np.random.default_rng(np.random.SeedSequence([int(seed), *[int(k) for k in keys]]))


def make_folds(D, scheme, cfg, rng):
    k = cfg["cv"]["k"]
    if scheme == "random":
        return random_folds(len(D), k, rng)
    if scheme == "block":
        return block_folds(D.coords, k, cfg["cv"]["block_km"], rng)
    if scheme == "region":
        return region_folds(D.region)
    if scheme == "box":
        return box_folds(D.lonlat, cfg["real"]["boxes"])
    if scheme == "time":
        return time_split(D.t)
    if scheme == "site":
        return site_folds(D.site, k, rng)
    raise ValueError(scheme)


def lead_groups(Dt, fold):
    if "cut" not in fold:
        return [("all", np.ones(len(Dt), bool))]
    lead = Dt.t - fold["cut"]
    edges = np.quantile(lead, [0, 1 / 3, 2 / 3, 1.0])
    b = np.minimum(np.searchsorted(edges, lead, side="right") - 1, 2)
    return [(f"lead {i + 1}", b == i) for i in range(3)]


def evaluate_fold(D, fold, cfg, models, methods, rng, seed, groups_fn=None, train_frac=1.0):
    tr, te = fold["train"], fold["test"]
    if train_frac < 1:
        tr = np.sort(rng.choice(tr, max(int(len(tr) * train_frac), 60), replace=False))
    perm = rng.permutation(tr)
    n_cal = max(int(cfg["cv"]["calib_frac"] * len(tr)), 30)
    cal, fit = np.sort(perm[:n_cal]), np.sort(perm[n_cal:])
    Df, Dc, Dt = D.subset(fit), D.subset(cal), D.subset(te)
    alpha = cfg["alpha"]
    groups = groups_fn(Dt, fold) if groups_fn else [("all", np.ones(len(Dt), bool))]
    rows, rel = [], []
    for m in models:
        model = make_model(m, cfg, seed).fit(Df)
        pc, pt = model.predict(Dc, alpha), model.predict(Dt, alpha)
        for meth in methods:
            lo, hi = conformal_interval(meth, pc, Dc, pt, Dt, alpha, cfg)
            for gname, mask in groups:
                if mask.sum() < 10:
                    continue
                y = Dt.y[mask]
                rows.append({"scheme": fold["scheme"], "fold": fold["fold"], "model": m, "method": meth, "group": gname, "n_train": len(fit),
                             "n_cal": len(cal), "n_test": int(mask.sum()), "rmse": rmse(y, pt.mean[mask]), "mae": mae(y, pt.mean[mask]),
                             "r2": r2(y, pt.mean[mask]), "coverage": coverage(y, lo[mask], hi[mask]), "width": mean_width(lo[mask], hi[mask]),
                             "iscore": interval_score(y, lo[mask], hi[mask], alpha), "brier": brier(Dt.exceed[mask], pt.p_exceed[mask]),
                             "ece": ece(Dt.exceed[mask], pt.p_exceed[mask])})
        for b, n, sp, so in reliability_bins(Dt.exceed, pt.p_exceed):
            rel.append({"scheme": fold["scheme"], "model": m, "bin": b, "n": n, "sum_p": sp, "sum_obs": so})
    return rows, rel


def run_cv_study(cfg, get_data, reps, schemes, models, methods, tag, groups_fn=None, train_fractions=(1.0,), seed_key=1):
    rows, rel = [], []
    t0 = time.perf_counter()
    for rep in range(reps):
        rng = rng_for(cfg["seed"], seed_key, rep)
        D = get_data(rep, rng)
        for scheme in schemes:
            for fold in make_folds(D, scheme, cfg, rng):
                for frac in train_fractions:
                    r, b = evaluate_fold(D, fold, cfg, models, methods, rng, int(cfg["seed"]) + rep, groups_fn, frac)
                    for x in r:
                        x.update({"rep": rep, "train_frac": frac})
                    for x in b:
                        x.update({"rep": rep})
                    rows += r
                    rel += b
        print(f"  [{tag}] rep {rep + 1}/{reps} done ({time.perf_counter() - t0:.0f}s)", flush=True)
    return pd.DataFrame(rows), pd.DataFrame(rel)


def run_synthetic(cfg, out: Path, only=None):
    ex = cfg["experiments"]
    steps = only or ["cv_study", "scarcity", "spatiotemporal"]
    if "cv_study" in steps:
        e = ex["cv_study"]
        df, rel = run_cv_study(cfg, lambda rep, rng: make_synthetic(cfg, rng), e["reps"], e["schemes"], cfg["models"], cfg["methods"], "cv_study")
        df.to_csv(out / "cv_study.csv", index=False)
        rel.to_csv(out / "reliability.csv", index=False)
    if "scarcity" in steps:
        e = ex["scarcity"]
        df, _ = run_cv_study(cfg, lambda rep, rng: make_synthetic(cfg, rng), e["reps"], ["region"], e["models"], e["methods"], "scarcity",
                             train_fractions=e["fractions"], seed_key=2)
        df.to_csv(out / "scarcity.csv", index=False)
    if "spatiotemporal" in steps:
        e = ex["spatiotemporal"]
        df, _ = run_cv_study(cfg, lambda rep, rng: make_synthetic(cfg, rng, temporal=True), e["reps"], ["time", "site"], e["models"], e["methods"],
                             "spatiotemporal", groups_fn=lead_groups, seed_key=3)
        df.to_csv(out / "spatiotemporal.csv", index=False)


def run_real(cfg, out: Path):
    D = load_csv(cfg)
    (out / "real_data_summary.json").write_text(json.dumps(summarize(D), indent=2, default=str))
    e = cfg["experiments"]["cv_study"]
    r = cfg["real"]
    schemes = list(r.get("schemes") or e["schemes"]) + (["site"] if D.site is not None else []) + (["time"] if D.t is not None else [])
    df, rel = run_cv_study(cfg, lambda rep, rng: D, r.get("reps", e["reps"]), schemes, cfg["models"], cfg["methods"], "real_cv", groups_fn=lead_groups, seed_key=11)
    df.to_csv(out / "real_cv_study.csv", index=False)
    rel.to_csv(out / "real_reliability.csv", index=False)
    if r.get("run_scarcity", True):
        s = cfg["experiments"]["scarcity"]
        df2, _ = run_cv_study(cfg, lambda rep, rng: D, s["reps"], ["region"], s["models"], s["methods"], "real_scarcity", train_fractions=s["fractions"], seed_key=12)
        df2.to_csv(out / "real_scarcity.csv", index=False)


def run_all(config, out_dir, mode="synthetic", only=None):
    cfg = load_config(config)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    print(f"wqub {__version__} | {mode} | config {config} | out {out}", flush=True)
    (run_synthetic if mode == "synthetic" else run_real)(*((cfg, out, only) if mode == "synthetic" else (cfg, out)))
    import scipy
    import sklearn
    meta = {"wqub_version": __version__, "mode": mode, "config_path": str(config), "config": cfg, "total_s": round(time.perf_counter() - t0, 1),
            "python": sys.version.split()[0], "platform": platform.platform(),
            "packages": {"numpy": np.__version__, "scipy": scipy.__version__, "pandas": pd.__version__, "scikit-learn": sklearn.__version__}}
    (out / f"run_metadata_{mode}.json").write_text(json.dumps(meta, indent=2, default=str))
    print(f"done in {meta['total_s']} s", flush=True)
