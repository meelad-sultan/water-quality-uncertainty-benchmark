# Method details

## Target and threshold
The target is transformed as `y = log1p(value)`; the exceedance event is `value > limit` (equivalently `y > log1p(limit)`). Non-detects are kept as 0 (`nonpositive: zero`),
replaced by half the smallest positive value (`half_min`) or dropped (`drop`), as set in the configuration.

## Models
* `naive`: mean and standard deviation of the training target; Gaussian interval; exceedance probability from the normal tail.
* `idw`: 8 nearest neighbours in projected coordinates, weights `1/(d + 1e-3)^2`; spread of the neighbour values gives the standard deviation (floor 0.05).
* `gp` (universal kriging): ridge regression on covariates (and time when present); a Gaussian process with kernel `C * Matern(nu = 3/2) + White` on the
  residuals, fitted on at most `gp.max_n` randomly chosen points; Gaussian interval including observation noise.
* `qgbm`: histogram gradient boosting with quantile loss at `alpha/2`, `0.5` and `1 - alpha/2` on covariates, coordinates (and time); the three outputs are sorted to avoid crossing;
  a separate classifier on the exceedance indicator gives the probability.

## Conformal methods
Let calibration scores be `s_i` and let `q` be the conformal quantile.
* `split`: `s_i = |y_i - mu(x_i)|`, interval `mu(x) +/- q`.
* `cqr`: `s_i = max(l(x_i) - y_i, y_i - u(x_i))`, interval `[l(x) - q, u(x) + q]` (Romano et al. 2019).
* Weighting: `q` is the `(1 - alpha)` quantile of the weighted distribution `sum_i p_i delta(s_i) + p_test delta(+infinity)` with `p_i` proportional to `w_i` and `p_test` to the test weight.
  * none: all weights 1 (the standard split-conformal quantile index `ceil((n + 1)(1 - alpha))`);
  * `local`: `w_i = exp(-d_i^2 / (2 h^2))` for the distance `d_i` between test point and calibration point, test weight 1, bandwidth `h = cv.local_bandwidth_km`;
  * `iw`: `w(x) = P(test | x) / P(calibration | x) * n_cal / n_test`, estimated by logistic regression on standardised inputs (covariates, coordinates, time), clipped to `cv.iw_clip`.
  If the quantile falls beyond the largest score, the largest score is used (conservative).
The finite-sample coverage guarantee needs calibration and test points to be exchangeable; spatial validation deliberately breaks this, which is what the study measures.

## Validation schemes
`random`: K random folds. `block`: points are binned into square blocks of side `cv.block_km` and whole blocks are assigned to folds, balanced by size.
`region`: each spatial cluster (or the region column) is held out in turn. `box`: all points inside a latitude/longitude box are held out; the rest train.
`time`: train on the first 70 % of the time range and test on the rest, reported by lead-time tercile. `site`: whole sites are held out.
In every fold a fraction `cv.calib_frac` of the training points is set aside, at random, for conformal calibration.

## Metrics
Coverage and mean width of the `1 - alpha` interval; Winkler interval score `(u - l) + (2/alpha)(l - y) 1{y < l} + (2/alpha)(y - u) 1{y > u}`;
Brier score and expected calibration error (ten equal-width bins) for the exceedance probability; RMSE, MAE and R2 for the point prediction.
Aggregates are means over folds weighted by test-set size, then over repeats.
