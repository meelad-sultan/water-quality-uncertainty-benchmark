"""Turn the raw downloads into clean CSVs (see data/README.md for sources, licences and citations).

* Punjab wells (EarthChem/IEDA, Mushtaq et al. 2022): reads the two sheets of the individual-well workbook and aligns them by row.
* Global arsenic (Eawag, Podgorski and Berg 2020): reads the predictor table, skipping the few malformed lines in the source file.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _norm(v) -> str:
    return re.sub(r"\s+", " ", str(v)).strip().lower()


def _sheet(path: Path, key: str, exact: bool = False) -> str:
    for name in pd.ExcelFile(path).sheet_names:
        n = _norm(name)
        if (n == key) if exact else (key in n):
            return name
    raise ValueError(f"no sheet matching '{key}' in {path.name}")


def _header_row(df: pd.DataFrame, cell_prefix: str) -> int:
    for i in range(min(60, len(df))):
        if any(_norm(v).startswith(cell_prefix) for v in df.iloc[i].tolist()):
            return i
    raise ValueError(f"no header row containing '{cell_prefix}'")


def _col(header: list, prefix: str) -> int:
    for j, v in enumerate(header):
        if _norm(v).startswith(prefix):
            return j
    raise ValueError(f"no column starting with '{prefix}'")


def prepare_punjab(xlsx: Path, out_csv: Path) -> dict:
    sf = pd.read_excel(xlsx, sheet_name=_sheet(xlsx, "sampling features"), header=None)
    dt = pd.read_excel(xlsx, sheet_name=_sheet(xlsx, "data", exact=True), header=None)
    hs, hd = _header_row(sf, "latitude"), _header_row(dt, "as (ug/l)")
    fh, dh = sf.iloc[hs].tolist(), dt.iloc[hd].tolist()
    feat = sf.iloc[hs + 3:].reset_index(drop=True)  # two description rows follow the header
    dat = dt.iloc[hd + 3:].reset_index(drop=True)  # two instruction rows follow the header
    n = min(len(feat), len(dat))
    key = lambda ser: np.array(["<na>" if pd.isna(v) else str(v).strip().lower() for v in ser], dtype=object)  # noqa: E731
    a, b = key(feat.iloc[:n, _col(fh, "sample name")]), key(dat.iloc[:n, _col(dh, "sample name")])
    mismatches = int((a != b).sum())
    if mismatches:
        raise ValueError(f"{mismatches} rows differ between the two sheets; the workbook layout changed")
    out = pd.DataFrame({
        "name": feat.iloc[:n, _col(fh, "sample name")].to_numpy(),
        "lat": feat.iloc[:n, _col(fh, "latitude")], "lon": feat.iloc[:n, _col(fh, "longitude")],
        "depth_ft": dat.iloc[:n, _col(dh, "depth")], "ec": dat.iloc[:n, _col(dh, "ec (")], "ph": dat.iloc[:n, _col(dh, "ph")],
        "no3": dat.iloc[:n, _col(dh, "no3")], "fe": dat.iloc[:n, _col(dh, "fe")], "so4": dat.iloc[:n, _col(dh, "so4")],
        "as_ugL": dat.iloc[:n, _col(dh, "as (ug/l)")], "f": dat.iloc[:n, _col(dh, "f (")],
    })
    for c in out.columns[1:]:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    before = len(out)
    out = out.dropna(subset=["lat", "lon", "as_ugL"])
    out.to_csv(out_csv, index=False)
    return {"rows_in_workbook": before, "rows_written": len(out), "as_values": {str(k): int(v) for k, v in out.as_ugL.value_counts().sort_index().items()},
            "share_gt_10": float((out.as_ugL > 10).mean()), "share_gt_50": float((out.as_ugL > 50).mean()),
            "missing_fraction": {c: round(float(out[c].isna().mean()), 4) for c in ("depth_ft", "ec", "ph", "no3", "fe", "so4", "f")}}


def prepare_global(csv: Path, out_csv: Path) -> dict:
    bad: list = []
    g = pd.read_csv(csv, engine="python", on_bad_lines=lambda row: bad.append(len(row)))  # type: ignore[arg-type]
    for c in g.columns:
        g[c] = pd.to_numeric(g[c], errors="coerce")
    n0 = len(g)
    g = g.dropna().rename(columns={"Latitude": "lat", "Longitude": "lon", "As_ppb": "as_ppb"})
    g.to_csv(out_csv, index=False)
    return {"rows_parsed": n0, "malformed_lines_skipped": len(bad), "rows_with_missing_values_dropped": n0 - len(g), "rows_written": len(g),
            "n_predictors": g.shape[1] - 3, "share_gt_10": float((g.as_ppb > 10).mean()), "share_nondetect_placeholder": float((g.as_ppb <= 1e-6).mean())}


def prepare(raw_dir: str | Path, out_dir: str | Path) -> dict:
    raw, out = Path(raw_dir), Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    log: dict = {}
    xl = sorted(raw.glob("*Well_individual*.xlsx"))
    if xl:
        log["punjab"] = {"source_file": xl[0].name, "sha256": _sha256(xl[0]), **prepare_punjab(xl[0], out / "punjab_wells.csv")}
    gl = raw / "arsenic_concentrations_predictor_data.csv"
    if gl.exists():
        log["global"] = {"source_file": gl.name, "sha256": _sha256(gl), **prepare_global(gl, out / "global_arsenic.csv")}
    if not log:
        raise FileNotFoundError(f"no recognised raw files in {raw}; see data/README.md")
    (out / "prepare_log.json").write_text(json.dumps(log, indent=2))
    return log


__all__ = ["prepare", "prepare_punjab", "prepare_global", "np"]
