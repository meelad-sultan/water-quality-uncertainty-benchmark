"""Markdown summary tables from result CSVs (synthetic: no prefix; real data: prefix 'real_')."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


def md(df: pd.DataFrame) -> str:
    df = df.copy()
    df.columns = [str(c) for c in df.columns]
    cols = list(df.columns)
    rows = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    rows += ["| " + " | ".join(str(v) for v in r.values) + " |" for _, r in df.iterrows()]
    return "\n".join(rows)


def wmean(g: pd.DataFrame, col: str) -> float:
    return float(np.average(g[col], weights=g["n_test"]))


def _agg(df, keys, cols):
    return df.groupby(keys, sort=False).apply(lambda g: pd.Series({c: wmean(g, c) for c in cols}), include_groups=False).reset_index()


def tables(res: Path, prefix: str, alpha: float) -> str:
    out = []
    cv = pd.read_csv(res / f"{prefix}cv_study.csv")
    schemes = [s for s in ("random", "block", "region", "box", "site", "time") if s in set(cv.scheme)]
    base = cv[cv.method == "none"]
    out.append("##### Accuracy under different validation schemes (weighted mean over folds and repeats)\n")
    a = _agg(base[base.group == "all"] if "all" in set(base.group) else base, ["model", "scheme"], ["r2", "rmse"])
    w = a.pivot(index="model", columns="scheme", values="r2").reindex(columns=schemes).round(2)
    w2 = a.pivot(index="model", columns="scheme", values="rmse").reindex(columns=schemes).round(2)
    t = pd.concat({"R2": w, "RMSE (log1p scale)": w2}, axis=1)
    t.columns = [f"{x} {y}" for x, y in t.columns]
    out.append(md(t.reset_index()))
    out.append(f"\n##### Interval coverage by scheme (nominal {1 - alpha:.0%}); width in parentheses\n")
    for model in [m for m in ("qgbm", "gp") if m in set(cv.model)]:
        d = cv[(cv.model == model) & (cv.group.isin(["all"]))]
        a = _agg(d, ["method", "scheme"], ["coverage", "width"])
        cells = a.assign(v=a.apply(lambda r: f"{r.coverage:.2f} ({r.width:.2f})", axis=1)).pivot(index="method", columns="scheme", values="v")
        order = [m for m in dict.fromkeys(cv.method) if m in cells.index]
        out.append(f"Model: **{model}**\n")
        out.append(md(cells.reindex(order).reindex(columns=schemes).reset_index()))
        out.append("")
    if "region" in schemes:
        d = cv[(cv.scheme == "region") & (cv.model == "qgbm")]
        a = _agg(d, ["method", "fold"], ["coverage"])
        t = a.pivot(index="method", columns="fold", values="coverage").round(2)
        t.columns = [f"test region {c}" for c in t.columns]
        out.append("##### Leave-one-region-out coverage by held-out region (model qgbm)\n")
        out.append(md(t.reindex([m for m in dict.fromkeys(cv.method) if m in t.index]).reset_index()))
    pr = base[base.group == "all"] if "all" in set(base.group) else base
    a = _agg(pr, ["model", "scheme"], ["brier", "ece"])
    t = a.assign(v=a.apply(lambda r: f"{r.brier:.3f} / {r.ece:.3f}", axis=1)).pivot(index="model", columns="scheme", values="v")
    out.append("\n##### Exceedance probability: Brier score / expected calibration error\n")
    out.append(md(t.reindex(columns=schemes).reset_index()))
    p = res / f"{prefix}scarcity.csv"
    if p.exists():
        sc = pd.read_csv(p)
        out.append("\n##### Data scarcity under leave-region-out: coverage (RMSE) by training fraction\n")
        for model in dict.fromkeys(sc.model):
            a = _agg(sc[sc.model == model], ["method", "train_frac"], ["coverage", "rmse"])
            cells = a.assign(v=a.apply(lambda r: f"{r.coverage:.2f} ({r.rmse:.2f})", axis=1)).pivot(index="method", columns="train_frac", values="v")
            out.append(f"Model: **{model}**\n")
            out.append(md(cells.reset_index()))
            out.append("")
    p = res / "spatiotemporal.csv"
    if prefix == "" and p.exists():
        st = pd.read_csv(p)
        out.append("\n##### Spatiotemporal forecasting (synthetic): coverage by scheme and lead time, model qgbm\n")
        d = st[st.model == "qgbm"]
        a = _agg(d, ["method", "scheme", "group"], ["coverage"])
        a["col"] = a.scheme + " / " + a.group
        out.append(md(a.pivot(index="method", columns="col", values="coverage").round(2).reset_index()))
    return "\n".join(out)


def summarize(res: str | Path) -> str:
    res = Path(res)
    parts = []
    meta = next(iter(sorted(res.glob("run_metadata_*.json"))), None)
    alpha = json.loads(meta.read_text())["config"]["alpha"] if meta else 0.2
    if (res / "cv_study.csv").exists():
        parts.append("#### Synthetic benchmark (known truth)\n\n" + tables(res, "", alpha))
    if (res / "real_cv_study.csv").exists():
        cfgm = json.loads((res / "run_metadata_real.json").read_text())["config"]["real"]
        parts.append(f"#### Real data: {cfgm.get('name', 'dataset')}\n\n" + tables(res, "real_", alpha))
    return "\n\n".join(parts)
