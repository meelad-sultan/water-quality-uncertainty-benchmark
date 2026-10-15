#### Real data: North Punjab wells, coordinates only (ablation)

##### Accuracy under different validation schemes (weighted mean over folds and repeats)

| model | R2 random | R2 block | R2 region | RMSE (log1p scale) random | RMSE (log1p scale) block | RMSE (log1p scale) region |
|---|---|---|---|---|---|---|
| gp | 0.4 | 0.08 | -0.66 | 1.4 | 1.72 | 1.84 |
| idw | 0.52 | -0.17 | -0.22 | 1.26 | 1.92 | 1.66 |
| naive | -0.0 | -0.02 | -0.79 | 1.82 | 1.82 | 1.89 |
| qgbm | -0.39 | -0.39 | -0.47 | 2.14 | 2.13 | 1.97 |

##### Interval coverage by scheme (nominal 80%); width in parentheses

Model: **qgbm**

| method | random | block | region |
|---|---|---|---|
| none | 0.91 (2.73) | 0.84 (2.77) | 0.81 (2.24) |
| split | 0.83 (6.37) | 0.83 (6.23) | 0.81 (6.09) |
| cqr | 0.91 (2.73) | 0.84 (2.77) | 0.81 (2.24) |
| cqr+local | 0.91 (2.73) | 0.84 (2.80) | 0.83 (3.38) |
| cqr+iw | 0.91 (2.73) | 0.84 (2.77) | 0.81 (2.24) |

Model: **gp**

| method | random | block | region |
|---|---|---|---|
| none | 0.81 (3.59) | 0.82 (4.45) | 0.81 (4.62) |
| split | 0.80 (3.49) | 0.75 (3.53) | 0.77 (3.41) |
| cqr | 0.80 (3.52) | 0.82 (4.45) | 0.81 (4.50) |
| cqr+local | 0.82 (3.09) | 0.79 (3.93) | 0.71 (5.09) |
| cqr+iw | 0.80 (3.53) | 0.81 (4.39) | 0.57 (4.26) |

##### Leave-one-region-out coverage by held-out region (model qgbm)

| method | test region 0 | test region 1 | test region 2 | test region 3 | test region 4 |
|---|---|---|---|---|---|
| none | 0.82 | 0.75 | 0.59 | 0.81 | 0.91 |
| split | 0.74 | 0.8 | 0.52 | 0.87 | 1.0 |
| cqr | 0.82 | 0.75 | 0.59 | 0.81 | 0.91 |
| cqr+local | 0.82 | 0.88 | 0.6 | 0.94 | 0.91 |
| cqr+iw | 0.82 | 0.75 | 0.59 | 0.81 | 0.91 |

##### Exceedance probability: Brier score / expected calibration error

| model | random | block | region |
|---|---|---|---|
| gp | 0.112 / 0.039 | 0.155 / 0.108 | 0.181 / 0.164 |
| idw | 0.097 / 0.064 | 0.191 / 0.192 | 0.160 / 0.161 |
| naive | 0.169 / 0.029 | 0.171 / 0.058 | 0.190 / 0.163 |
| qgbm | 0.091 / 0.021 | 0.153 / 0.114 | 0.153 / 0.101 |

##### Data scarcity under leave-region-out: coverage (RMSE) by training fraction

Model: **qgbm**

| method | 0.25 | 1.0 |
|---|---|---|
| cqr | 0.75 (1.98) | 0.79 (1.97) |
| cqr+iw | 0.78 (1.98) | 0.79 (1.97) |
| none | 0.75 (1.98) | 0.79 (1.97) |

