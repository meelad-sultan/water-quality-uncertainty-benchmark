"""Figures from the result CSVs."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

PAL = ["#1b9e77", "#d95f02", "#7570b3", "#e7298a", "#66a61e", "#e6ab02", "#666666"]
SCHEMES = ["random", "block", "region", "box", "site", "time"]


def _save(fig, out, name):
    fig.tight_layout()
    fig.savefig(out / name, dpi=160)
    plt.close(fig)
    return out / name


def _w(g, col):
    return float(np.average(g[col], weights=g["n_test"]))


def _agg(df, keys, col):
    return df.groupby(keys, sort=False).apply(lambda g: _w(g, col), include_groups=False).rename(col).reset_index()


def fig_map(D, out, name, title):
    fig, ax = plt.subplots(1, 2, figsize=(10, 4.2))
    sc = ax[0].scatter(D.coords[:, 0], D.coords[:, 1], c=D.y, s=6, cmap="viridis")
    fig.colorbar(sc, ax=ax[0], label="target (log1p)")
    ax[0].set_title(f"{title}: target", fontsize=9)
    ax[1].scatter(D.coords[:, 0], D.coords[:, 1], c=D.region, s=6, cmap="tab10")
    ax[1].set_title("regions (leave-one-region-out folds)", fontsize=9)
    for a in ax:
        a.set_xlabel("x (km)")
        a.set_ylabel("y (km)")
        a.set_aspect("equal")
    return _save(fig, out, name)


def fig_optimism(res, out, prefix, alpha):
    cv = pd.read_csv(res / f"{prefix}cv_study.csv")
    b = cv[(cv.method == "none") & (cv.group == "all")] if "all" in set(cv.group) else cv[cv.method == "none"]
    a = _agg(b, ["model", "scheme"], "r2")
    schemes = [s for s in SCHEMES if s in set(a.scheme)]
    fig, ax = plt.subplots(figsize=(7, 4))
    models = list(dict.fromkeys(a.model))
    for i, m in enumerate(models):
        v = a[a.model == m].set_index("scheme").reindex(schemes).r2
        ax.bar(np.arange(len(schemes)) + i * 0.8 / len(models), v.values, 0.8 / len(models), label=m, color=PAL[i])
    ax.set_xticks(np.arange(len(schemes)) + 0.4 - 0.4 / len(models))
    ax.set_xticklabels(schemes)
    ax.set_ylabel("R2 on held-out data")
    ax.set_title("Random cross-validation overstates skill (higher bars = more optimistic)", fontsize=9)
    ax.axhline(0, color="k", lw=0.8)
    ax.legend(fontsize=8)
    return _save(fig, out, f"{prefix}fig2_optimism.png")


def fig_coverage(res, out, prefix, alpha):
    cv = pd.read_csv(res / f"{prefix}cv_study.csv")
    cv = cv[cv.group == "all"] if "all" in set(cv.group) else cv
    models = [m for m in ("qgbm", "gp") if m in set(cv.model)]
    fig, axes = plt.subplots(1, len(models), figsize=(6.5 * len(models), 4.2), squeeze=False)
    for ax, model in zip(axes[0], models, strict=True):
        a = _agg(cv[cv.model == model], ["method", "scheme"], "coverage")
        methods, schemes = list(dict.fromkeys(a.method)), [s for s in SCHEMES if s in set(a.scheme)]
        for i, s in enumerate(schemes):
            v = a[a.scheme == s].set_index("method").reindex(methods).coverage
            ax.bar(np.arange(len(methods)) + i * 0.8 / len(schemes), v.values, 0.8 / len(schemes), label=s, color=PAL[i])
        ax.axhline(1 - alpha, color="k", ls="--", lw=1)
        ax.set_xticks(np.arange(len(methods)) + 0.4 - 0.4 / len(schemes))
        ax.set_xticklabels(methods, rotation=40, ha="right", fontsize=8)
        ax.set_ylabel("empirical coverage")
        ax.set_title(f"{model}: coverage of nominal {1 - alpha:.0%} intervals", fontsize=9)
        ax.legend(fontsize=8, loc="center left", bbox_to_anchor=(1.0, 0.5))
    return _save(fig, out, f"{prefix}fig3_coverage.png")


def fig_efficiency(res, out, prefix, alpha):
    cv = pd.read_csv(res / f"{prefix}cv_study.csv")
    d = cv[(cv.scheme == ("region" if "region" in set(cv.scheme) else cv.scheme.iloc[0])) & (cv.group == "all")] if "all" in set(cv.group) else cv
    fig, ax = plt.subplots(figsize=(6, 4.2))
    for i, m in enumerate(dict.fromkeys(d.model)):
        a = d[d.model == m].groupby("method", sort=False).apply(lambda g: pd.Series({"coverage": _w(g, "coverage"), "width": _w(g, "width")}), include_groups=False)
        ax.scatter(a.width, a.coverage, color=PAL[i], label=m)
        for meth, r in a.iterrows():
            ax.annotate(meth, (r.width, r.coverage), fontsize=6, xytext=(3, 3), textcoords="offset points")
    ax.axhline(1 - alpha, color="k", ls="--", lw=1)
    ax.set_xlabel("mean interval width (log1p units)")
    ax.set_ylabel("coverage")
    ax.set_title("Leave-region-out: coverage vs interval width", fontsize=9)
    ax.legend(fontsize=8)
    return _save(fig, out, f"{prefix}fig4_efficiency.png")


def fig_reliability(res, out, prefix):
    rel = pd.read_csv(res / f"{prefix}reliability.csv")
    models = [m for m in ("qgbm", "gp") if m in set(rel.model)]
    fig, axes = plt.subplots(1, len(models), figsize=(5 * len(models), 4.2), squeeze=False)
    for ax, model in zip(axes[0], models, strict=True):
        for i, s in enumerate([s for s in SCHEMES if s in set(rel.scheme)]):
            g = rel[(rel.model == model) & (rel.scheme == s)].groupby("bin")[["n", "sum_p", "sum_obs"]].sum()
            g = g[g.n >= 15]
            ax.plot(g.sum_p / g.n, g.sum_obs / g.n, "-o", color=PAL[i], label=s, ms=4)
        ax.plot([0, 1], [0, 1], "k--", lw=1)
        ax.set_xlabel("predicted exceedance probability")
        ax.set_ylabel("observed frequency")
        ax.set_title(f"{model}: reliability of exceedance probabilities", fontsize=9)
        ax.legend(fontsize=8)
    return _save(fig, out, f"{prefix}fig5_reliability.png")


def fig_scarcity(res, out, prefix, alpha):
    sc = pd.read_csv(res / f"{prefix}scarcity.csv")
    models = list(dict.fromkeys(sc.model))
    fig, axes = plt.subplots(1, len(models), figsize=(5.5 * len(models), 4), squeeze=False)
    for ax, m in zip(axes[0], models, strict=True):
        a = _agg(sc[sc.model == m], ["method", "train_frac"], "coverage")
        for i, meth in enumerate(dict.fromkeys(a.method)):
            g = a[a.method == meth]
            ax.plot(g.train_frac, g.coverage, "-o", color=PAL[i % 7], label=meth, ms=4)
        ax.axhline(1 - alpha, color="k", ls="--", lw=1)
        ax.set_xlabel("fraction of training data kept")
        ax.set_ylabel("coverage (leave-region-out)")
        ax.set_title(f"{m}: data scarcity", fontsize=9)
        ax.legend(fontsize=7)
    return _save(fig, out, f"{prefix}fig6_scarcity.png")


def fig_horizon(res, out, alpha):
    st = pd.read_csv(res / "spatiotemporal.csv")
    st = st[(st.scheme == "time") & (st.model == "qgbm")]
    a = _agg(st, ["method", "group"], "coverage")
    fig, ax = plt.subplots(figsize=(6, 4))
    for i, meth in enumerate(dict.fromkeys(a.method)):
        g = a[a.method == meth]
        ax.plot(g.group, g.coverage, "-o", color=PAL[i], label=meth)
    ax.axhline(1 - alpha, color="k", ls="--", lw=1)
    ax.set_ylabel("coverage")
    ax.set_title("Synthetic forecasting: coverage vs lead time (model qgbm)", fontsize=9)
    ax.legend(fontsize=8)
    return _save(fig, out, "fig7_horizon.png")


def make_all(res: str | Path, out: str | Path):
    res, out = Path(res), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    made = []
    for mode, prefix in (("synthetic", ""), ("real", "real_")):
        if not (res / f"{prefix}cv_study.csv").exists():
            continue
        meta = json.loads((res / f"run_metadata_{mode}.json").read_text())
        cfg, alpha = meta["config"], meta["config"]["alpha"]
        made += [fig_optimism(res, out, prefix, alpha), fig_coverage(res, out, prefix, alpha), fig_efficiency(res, out, prefix, alpha), fig_reliability(res, out, prefix)]
        if (res / f"{prefix}scarcity.csv").exists():
            made.append(fig_scarcity(res, out, prefix, alpha))
        if mode == "synthetic":
            from wqub.experiments import rng_for
            from wqub.synth import make_synthetic
            made.append(fig_map(make_synthetic(cfg, rng_for(cfg["seed"], 1, 0)), out, "fig1_synthetic_map.png", "Synthetic world"))
            if (res / "spatiotemporal.csv").exists():
                made.append(fig_horizon(res, out, alpha))
        else:
            from wqub.data import load_csv
            made.append(fig_map(load_csv(cfg), out, "real_fig1_map.png", cfg["real"].get("name", "Real data")))
    return made
