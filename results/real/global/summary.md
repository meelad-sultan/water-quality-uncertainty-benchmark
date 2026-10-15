#### Real data: Global groundwater arsenic (1 km pixels, 51 predictors)

##### Accuracy under different validation schemes (weighted mean over folds and repeats)

| model | R2 random | R2 block | R2 region | R2 box | RMSE (log1p scale) random | RMSE (log1p scale) block | RMSE (log1p scale) region | RMSE (log1p scale) box |
|---|---|---|---|---|---|---|---|---|
| naive | -0.0 | -0.02 | -0.22 | -0.26 | 1.42 | 1.41 | 1.4 | 2.4 |
| qgbm | 0.27 | 0.04 | -0.17 | 0.02 | 1.21 | 1.37 | 1.4 | 2.12 |

##### Interval coverage by scheme (nominal 80%); width in parentheses

Model: **qgbm**

| method | random | block | region | box |
|---|---|---|---|---|
| none | 0.87 (2.77) | 0.86 (3.03) | 0.80 (2.92) | 0.31 (3.10) |
| split | 0.80 (2.83) | 0.69 (2.74) | 0.63 (2.65) | 0.39 (2.73) |
| cqr | 0.87 (2.77) | 0.86 (3.03) | 0.80 (2.92) | 0.31 (3.10) |
| cqr+iw | 0.87 (2.77) | 0.86 (3.03) | 0.80 (2.92) | 0.31 (3.10) |

##### Leave-one-region-out coverage by held-out region (model qgbm)

| method | test region 0 | test region 1 | test region 2 | test region 3 | test region 4 | test region 5 | test region 6 | test region 7 |
|---|---|---|---|---|---|---|---|---|
| none | 0.65 | 0.94 | 0.97 | 0.75 | 0.87 | 0.26 | 0.92 | 0.65 |
| split | 0.33 | 0.94 | 0.96 | 0.79 | 0.86 | 0.25 | 0.34 | 0.6 |
| cqr | 0.65 | 0.94 | 0.97 | 0.75 | 0.87 | 0.26 | 0.92 | 0.65 |
| cqr+iw | 0.65 | 0.94 | 0.97 | 0.76 | 0.87 | 0.26 | 0.92 | 0.65 |

##### Exceedance probability: Brier score / expected calibration error

| model | random | block | region | box |
|---|---|---|---|---|
| naive | 0.155 / 0.028 | 0.158 / 0.066 | 0.164 / 0.138 | 0.305 / 0.240 |
| qgbm | 0.112 / 0.018 | 0.150 / 0.080 | 0.161 / 0.123 | 0.216 / 0.192 |
