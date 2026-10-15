# Next steps for the repository owner

1. Run `python -m pytest` and the quick synthetic run on your machine.
2. Re-run the real-data pipeline (README section 8) and compare your `prepare_log.json` checksums with `docs/prepare_log.json`; compare `summary.md` with the committed one. Small numerical differences are expected only if library versions differ.
3. Read `src/wqub/conformal.py`, `splits.py` and `experiments.py` until you can explain every step, especially why CQR does nothing on the zero-inflated targets.
4. Check the licence and citation requirements on both data landing pages, and verify the methods references.
5. Optional: download the USGS sample-results and site files (not the activity export) for one characteristic and state to add a real time-series case study.
6. Tag `v0.1.0`, enable Zenodo, add the DOI to `CITATION.cff` and the README.
