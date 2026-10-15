import json

import numpy as np
import pandas as pd

from wqub.conformal import conformal_interval, weighted_quantile_inf
from wqub.data import Data, load_csv
from wqub.prepare import prepare
from wqub.splits import box_folds


def test_box_folds_hold_out_only_the_box():
    rng = np.random.default_rng(0)
    ll = np.column_stack([rng.uniform(50, 90, 500), rng.uniform(10, 50, 500)])
    f = box_folds(ll, [{"name": "b", "lat": [23, 37], "lon": [60, 78]}], min_n=5)[0]
    inside = (ll[:, 1] >= 23) & (ll[:, 1] <= 37) & (ll[:, 0] >= 60) & (ll[:, 0] <= 78)
    assert set(f["test"]) == set(np.flatnonzero(inside)) and not set(f["train"]) & set(f["test"]) and f["label"] == "b"


def _local_reference(scores, coords_c, coords_t, h, alpha):
    q = np.empty(len(coords_t))
    for j in range(len(coords_t)):
        d2 = ((coords_c - coords_t[j]) ** 2).sum(1)
        q[j] = weighted_quantile_inf(scores, np.exp(-d2 / (2 * h * h)) + 1e-12, 1.0, alpha)[0]
    return q


def test_vectorised_local_conformal_matches_reference(cfg):
    from wqub.models import Pred

    rng = np.random.default_rng(3)
    nc, nt = 350, 950  # more than one 400-row chunk
    cc, ct = rng.uniform(0, 200, (nc, 2)), rng.uniform(0, 200, (nt, 2))
    yc = rng.normal(0, 1, nc)
    mk = lambda c, y: Data(np.zeros((len(y), 0)), c, y, np.zeros(len(y), int), 1.0)  # noqa: E731
    pc, pt = Pred(np.zeros(nc), np.zeros(nc), np.zeros(nc), np.zeros(nc)), Pred(np.zeros(nt), np.zeros(nt), np.zeros(nt), np.zeros(nt))
    lo, hi = conformal_interval("split+local", pc, mk(cc, yc), pt, mk(ct, np.zeros(nt)), 0.2, cfg)
    ref = _local_reference(np.abs(yc), cc, ct, cfg["cv"]["local_bandwidth_km"], 0.2)
    np.testing.assert_allclose(hi, ref)
    np.testing.assert_allclose(lo, -ref)


def test_loader_all_covariates_zero_mode_and_global_coords(tmp_path, cfg_copy):
    rng = np.random.default_rng(1)
    n = 300
    df = pd.DataFrame({"lat": rng.uniform(10, 50, n), "lon": rng.uniform(-100, 100, n), "as": rng.choice([0, 0, 10, 50, 100], n).astype(float),
                       "a": rng.normal(size=n), "b": rng.normal(size=n), "tag": ["x"] * n})
    p = tmp_path / "g.csv"
    df.to_csv(p, index=False)
    cfg_copy["real"] = {"path": str(p), "name": "g", "columns": {"lat": "lat", "lon": "lon", "target": "as", "covariates": "all"}, "limit": 10.0,
                        "nonpositive": "zero", "coords": "global", "region_clusters": 4}
    D = load_csv(cfg_copy)
    assert D.names == ["a", "b"] and D.y.min() == 0.0 and D.lonlat.shape == (n, 2) and len(np.unique(D.region)) == 4
    np.testing.assert_allclose(D.coords[:, 0], D.lonlat[:, 0] * 111.32)


def _punjab_xlsx(path, n=40):
    rng = np.random.default_rng(2)
    names = [f"w{i}" for i in range(n)]
    names[7] = None
    pre = [["note"]] * 4
    f_hdr = ["SAMPLE NAME", "IGSN", "LATITUDE", "LONGITUDE", "Elevation", "LOCATION KEYWORDS", "Location name", "SAMPLING FEATURE TYPE"]
    f_rows = pre + [f_hdr, ["desc"] * 8, [None] * 8] + [[nm, None, 30 + rng.random(), 72 + rng.random(), None, "Punjab", None, "Individual well"] for nm in names]
    d_hdr = ["SAMPLE NAME", "IGSN", "aaaa/mm/gg", "Depth (ft)", "EC (μS/cm)", "pH", "NO3 (mg/L)", "Fe  (mg/L)", "SO4 (mg/L)", "As (ug/L)", "F (mg/L)"]
    d_rows = pre + [["IDENTIFICATION"] + [None] * 10, d_hdr, ["well location ID"] + [None] * 10, ["must match sample tab"] + [None] * 10]
    d_rows += [[nm, None, None, 50, 100, 7.1, 1, 0.5, 70, float(rng.choice([0, 10, 50])), 0.8] for nm in names]
    with pd.ExcelWriter(path) as w:
        pd.DataFrame([["meta"]]).to_excel(w, sheet_name="1 Data source", header=False, index=False)
        pd.DataFrame(f_rows).to_excel(w, sheet_name="2 Sampling Features", header=False, index=False)
        pd.DataFrame(d_rows).to_excel(w, sheet_name="Data ", header=False, index=False)


def test_prepare_parses_both_raw_formats(tmp_path):
    raw, out = tmp_path / "raw", tmp_path / "out"
    raw.mkdir()
    _punjab_xlsx(raw / "2724-3_ECL_Mushtaq_Well_individual_Dataset_v2.xlsx")
    lines = ["Latitude,Longitude,As_ppb,pet,precip"] + [f"{10 + i},{20 + i},{i % 7},1.5,2.5" for i in range(30)]
    lines.insert(10, "1,2,3,4,5,6,7,8,9")  # malformed (too many fields)
    (raw / "arsenic_concentrations_predictor_data.csv").write_text("\n".join(lines))
    log = prepare(raw, out)
    assert log["punjab"]["rows_written"] == 40 and set(log["punjab"]["as_values"]) <= {"0", "10", "50"}
    assert log["global"]["malformed_lines_skipped"] == 1 and log["global"]["rows_written"] == 30 and log["global"]["n_predictors"] == 2
    pj = pd.read_csv(out / "punjab_wells.csv")
    assert list(pj.columns) == ["name", "lat", "lon", "depth_ft", "ec", "ph", "no3", "fe", "so4", "as_ugL", "f"]
    assert json.loads((out / "prepare_log.json").read_text())["global"]["sha256"]
