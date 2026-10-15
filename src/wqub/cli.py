"""Command line: python -m wqub <prepare|run|real|check|figures|summary>."""
from __future__ import annotations

import argparse
import json


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="wqub", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="synthetic benchmark")
    r.add_argument("--config", default="configs/default.yaml")
    r.add_argument("--out", default="results/metrics")
    r.add_argument("--only", nargs="+", choices=["cv_study", "scarcity", "spatiotemporal"])
    rr = sub.add_parser("real", help="run the same study on your own monitoring CSV")
    rr.add_argument("--config", required=True)
    rr.add_argument("--out", default="results/real")
    pp = sub.add_parser("prepare", help="convert raw downloads into clean CSVs")
    pp.add_argument("--raw", default="data/raw")
    pp.add_argument("--out", default="data/processed")
    c = sub.add_parser("check", help="load a real CSV with your column mapping and print a summary")
    c.add_argument("--config", required=True)
    f = sub.add_parser("figures")
    f.add_argument("--results", default="results/metrics")
    f.add_argument("--out", default="results/figures")
    s = sub.add_parser("summary")
    s.add_argument("--results", default="results/metrics")
    a = ap.parse_args(argv)
    if a.cmd == "run":
        from wqub.experiments import run_all

        run_all(a.config, a.out, "synthetic", a.only)
    elif a.cmd == "real":
        from wqub.experiments import run_all

        run_all(a.config, a.out, "real")
    elif a.cmd == "prepare":
        from wqub.prepare import prepare

        print(json.dumps(prepare(a.raw, a.out), indent=2))
    elif a.cmd == "check":
        from wqub.config import load_config
        from wqub.data import load_csv, summarize

        print(json.dumps(summarize(load_csv(load_config(a.config))), indent=2, default=str))
    elif a.cmd == "figures":
        from wqub.plotting import make_all

        for p in make_all(a.results, a.out):
            print("wrote", p)
    else:
        from wqub.summary import summarize

        print(summarize(a.results))


if __name__ == "__main__":
    main()
