# Data: sources, citations, licences, processing

This repository does **not** redistribute the raw datasets. Download them from the original sources, put the files in
`data/raw/` (git-ignored), and run `python -m wqub prepare`. Check each dataset's licence and terms of use on its landing
page before reusing or redistributing anything: the licence text was **not** part of the files used to build this repository.

## Datasets used

| Key | Dataset | Landing page | Use here |
|---|---|---|---|
| Punjab wells | Mushtaq, N., Farooqi, A., Khattak, J., Hussain, I., Mailloux, B., Bostick, B., Nghiem, A., van Geen, A., 2022. *Well water and drill cuttings from north Punjab, Pakistan v.2*, Version 1.0. Interdisciplinary Earth Data Alliance (IEDA). https://doi.org/10.26022/IEDA/112724 | https://ecl.earthchem.org/view.php?id=2724 | Individual-well workbook `2724-3_ECL_Mushtaq_Well_individual_Dataset_v2.xlsx` (20,578 wells; 20,575 used) |
| Global arsenic | Podgorski, J., and Berg, M. (2020). Global threat of arsenic in groundwater. *Science* 368(6493), 845-850. doi:10.1126/science.aba1510. Data package: `arsenic_concentrations_predictor_data.csv` (contact: joel.podgorski@eawag.ch, michael.berg@eawag.ch) | https://opendata.eawag.ch/dataset/global-threat-of-arsenic-in-groundwater (data DOI 10.25678/0001ZT as shown on that page; verify) | Table of 56,190 lines; 56,175 rows used (see processing) |

Files in the Punjab download that are **not** used here: the village-level well-arsenic workbook (221 locations, counts per category) and the
sediment/drill-cutting workbook. Files in the global download not used: `groundwater_utilization_by_country.csv`, the R scripts and the GeoTIFF maps.

## What the columns mean (and the caveats that matter)

**Punjab wells.** `as_ugL` is a **field test-kit reading**, reported in categories (0, 10, 25, 50, 100, ... ug/L); 70 % of wells read 0 (below
the kit's reading), 21 % read above 10 and 10 % above 50. It is neither a continuous nor a laboratory concentration. Other columns are co-measured
field parameters: depth (ft), electrical conductivity, pH, nitrate, iron, sulphate, fluoride. Coordinates and the arsenic reading are always present;
the other fields have some missing values, which are imputed with the median.

**Global arsenic.** Each row is a 1 km pixel with a concentration averaged from the compiled sources, plus 51 predictor variables (climate, soil, geology,
topography and others; see the paper's supplementary tables S1 and S2). Values of 1e-7 in the file stand in for non-detects (about a quarter of rows).

## Processing (`wqub prepare`)

* Punjab: the two sheets (sampling features and measurements) are aligned **by row** after checking that sample names agree on every row; three rows
  without coordinates or arsenic are dropped.
* Global: 11 malformed lines in the source file (records merged without a line break) are skipped and counted; 4 rows with missing values are dropped.
* `data/processed/prepare_log.json` records row counts, the skipped lines and the SHA-256 checksum of each raw file.

## Not used: USGS Water Quality Portal "Activity" export

The `Activity.csv` file supplied (39,807 sampling events, 95 columns) is the portal's **sampling-activity** profile: it describes sampling events
and has no measured values, so it cannot be used for modelling. To add a real time-series case study, download from https://www.waterqualitydata.us the
**Sample Results (physical/chemical metadata)** profile for one characteristic (for example arsenic, site type well, one state) **and** the matching
**Site** data (coordinates), then adapt `configs/real_template.yaml`. USGS data are generally public domain; check the portal's terms and cite it.
