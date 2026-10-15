# Does cross-validation overstate skill and interval coverage in groundwater arsenic prediction? A spatial-validation and conformal-prediction benchmark

**Muhammad Meelad Sultan** · technical report accompanying the repository `water-quality-uncertainty-benchmark` (v0.1.0) · not peer reviewed

## Abstract
Models of groundwater contamination are usually evaluated with random cross-validation, although they are meant to predict where nothing has been measured. Using two open arsenic datasets
(20,575 wells in north Punjab, Pakistan, and 56,175 global 1 km pixels) and a synthetic world with known truth, we compare random, spatial-block, leave-region-out and transfer validation, and four
interval methods built on conformal prediction. For the probability of exceeding 10 ug/L, gradient boosting reaches a Brier score of 0.087 under random validation of the Punjab wells but 0.136 under spatial blocks and 0.132 when whole regions
are held out (naive baseline 0.171 to 0.190). Transferring the global model to a South Asia window yields 80 % intervals that cover only 0.31 of observations. Conformal corrections did not repair coverage on these zero-inflated
targets, although importance weighting restored average coverage in a controlled synthetic shift. We provide code, tests and data-preparation steps to reproduce the results.

## 1. Introduction
Wells are spatially clustered and nearby measurements are alike. Random folds therefore let a model predict a well from a neighbour a few hundred metres away, which a new area will not offer. Spatial validation and conformal prediction are established
remedies (Roberts et al. 2017; Ploton et al. 2020; Vovk et al. 2005; Romano et al. 2019; Tibshirani et al. 2019), but their behaviour on water-quality data in data-scarce regions is rarely shown with open data and open code. We ask (i) how much random validation
overstates skill, (ii) whether intervals and exceedance probabilities stay calibrated when predicting into a new area, and (iii) whether conformal variants restore calibration and at what cost in width.

## 2. Data
**North Punjab wells** (Mushtaq et al. 2022): 20,578 individual wells (20,575 used) with coordinates, a field test-kit arsenic reading in categories (0, 10, 25, 50, 100, ... ug/L; 70 % read 0; 21 % exceed 10 ug/L) and co-measured depth, conductivity, pH, nitrate, iron, sulphate and fluoride.
**Global arsenic** (Podgorski and Berg 2020): 56,190 lines of 1 km pixels with an averaged concentration and 51 predictors; 11 malformed lines were skipped and 4 rows with missing values dropped (56,175 used); a quarter of values are non-detect placeholders; 19 % exceed 10 ug/L.
**Synthetic world:** a smooth spatial field, three covariates, heteroscedastic noise and one region with shifted covariates, higher mean and more noise; optional season, trend and site effects. Sources, caveats and licences to check are in `data/README.md`.

## 3. Methods
Targets are modelled as `log1p(value)`. Models: a naive baseline, inverse-distance weighting, universal kriging (400-point cap) and quantile gradient boosting with a classifier for the exceedance probability. Intervals: the model's own, split conformal, conformalised quantile regression (CQR), each optionally weighted by a spatial kernel (`local`)
or by an estimated test/calibration density ratio (`iw`). Validation: random folds; spatial blocks (30 km for Punjab, 1,000 km globally); leave-one-region-out over k-means clusters (5 and 8); a held-out South Asia box (23-37 N, 60-78 E; 881 pixels); and, for the synthetic world, forward-in-time and leave-site-out. A quarter of each training set is held out at random for conformal calibration.
Metrics are coverage and width of nominal 80 % intervals, the Winkler interval score, and the Brier score and expected calibration error (ECE) of the exceedance probability. Details: `docs/method.md`.

## 4. Results
**Exceedance probability (gradient boosting; naive in brackets).**

| Dataset | Random | Spatial block | Leave-region-out | Transfer |
|---|---|---|---|---|
| Punjab, Brier | 0.087 (0.169) | 0.136 (0.171) | 0.132 (0.190) | n/a |
| Punjab, ECE | 0.020 | 0.087 | 0.069 | n/a |
| Global, Brier | 0.112 (0.155) | 0.150 (0.158) | 0.161 (0.164) | 0.216 (0.305) |
| Global, ECE | 0.018 | 0.080 | 0.123 | 0.192 |

**Interval coverage (nominal 0.80, gradient boosting).** Own interval, Punjab: 0.91 / 0.84 / 0.83 (random / block / region); global: 0.87 / 0.86 / 0.80 / 0.31 (plus transfer). Split conformal, global: 0.80 / 0.69 / 0.63 / 0.39.
Inverse-distance weighting has R2 = 0.52 under random validation on the Punjab wells and -0.17 under spatial blocks. Coordinates alone give Brier 0.153 (block) and 0.153 (region) against 0.136 and 0.132 with water-chemistry covariates.
**Conformal correction.** For CQR, 21 % (global) and 69 % (Punjab) of calibration scores equal 0, so the conformal quantile is 0 and CQR and importance-weighted CQR return the model's own interval. Spatial-local weighting produced very wide intervals when the held-out region was far from the calibration data (Punjab kriging, region scheme: mean width 17.7 log-units against about 4 for the others).
**Synthetic world.** Split-conformal coverage of gradient boosting falls from 0.81 (random) to 0.73 (block) and 0.52 (region); importance weighting restores average coverage under region shift (0.83) at about twice the width, while the shifted region stays under-covered.

## 5. Discussion
Random validation is optimistic on both real datasets, and the gap is largest where a neighbour-based predictor is used and where the target region differs from the training data. The South Asia transfer result shows the practical risk: a model trained elsewhere under-predicts the local exceedance rate
(mean predicted probability 0.31 against an observed 0.45) and its stated 80 % intervals cover about a third of observations. Exceedance probabilities remain better than the naive baseline, so the models carry information, but their calibration should not be taken from random validation.
Conformal prediction did not rescue calibration here. The reasons differ: on zero-inflated, non-negative targets the CQR correction vanishes; kernel weighting can blow up widths far from the calibration data; and importance weighting corrects covariate shift but not changes in noise or mean level, as the synthetic world shows. Calibrating on data from the target region, or using methods designed for shifted conditional distributions, is the natural next step.

## 6. Limitations
Field-kit categories are not laboratory concentrations; regression metrics are weak on these targets; held-out regions are arbitrary clusters; the kriging baseline is capped at 400 points; no deep or graph models, tuning or external covariates were used; repeats re-draw folds on one dataset and so understate sampling uncertainty; the real data have no usable time dimension, so the temporal results are synthetic; wells are not a random sample of aquifers. Nothing here should inform drinking-water decisions.

## 7. Reproducibility
Code, configuration, tests (19), fixed seeds, data-preparation checksums (`docs/prepare_log.json`) and all result tables are in the repository; see the README for the commands. Data are not redistributed; follow the source terms.

## References (verify before citing)
- Mushtaq, N., Farooqi, A., Khattak, J., Hussain, I., Mailloux, B., Bostick, B., Nghiem, A., van Geen, A., 2022. Well water and drill cuttings from north Punjab, Pakistan v.2, Version 1.0. IEDA. https://doi.org/10.26022/IEDA/112724
- Podgorski, J. and Berg, M. (2020). Global threat of arsenic in groundwater. Science 368(6493), 845-850. doi:10.1126/science.aba1510
- Vovk, V., Gammerman, A. and Shafer, G. (2005). Algorithmic Learning in a Random World. Springer.
- Romano, Y., Patterson, E. and Candes, E. (2019). Conformalized quantile regression. NeurIPS 32.
- Tibshirani, R. J., Barber, R. F., Candes, E. and Ramdas, A. (2019). Conformal prediction under covariate shift. NeurIPS 32.
- Roberts, D. R. et al. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. Ecography 40.
- Ploton, P. et al. (2020). Spatial validation reveals poor predictive performance of large-scale ecological mapping models. Nature Communications 11.

*Development note: this project was developed with assistance from Claude (Anthropic) for drafting code and documentation; the author is responsible for the content and should review and reproduce the results before release.*
