#### Real data: North Punjab (Pakistan) individual wells, field-kit arsenic

##### Accuracy under different validation schemes (weighted mean over folds and repeats)

| model | R2 random | R2 block | R2 region | RMSE (log1p scale) random | RMSE (log1p scale) block | RMSE (log1p scale) region |
|---|---|---|---|---|---|---|
| gp | -2.32 | -1.52 | -0.8 | 2.56 | 2.49 | 1.9 |
| idw | 0.52 | -0.17 | -0.22 | 1.26 | 1.92 | 1.66 |
| naive | -0.0 | -0.02 | -0.79 | 1.82 | 1.82 | 1.89 |
| qgbm | -0.39 | -0.39 | -0.47 | 2.14 | 2.13 | 1.97 |

##### Interval coverage by scheme (nominal 80%); width in parentheses

Model: **qgbm**

| method | random | block | region |
|---|---|---|---|
| none | 0.91 (2.65) | 0.84 (2.65) | 0.83 (2.37) |
| split | 0.83 (6.37) | 0.83 (6.23) | 0.81 (6.09) |
| cqr | 0.91 (2.65) | 0.84 (2.65) | 0.83 (2.37) |
| cqr+local | 0.91 (2.65) | 0.84 (2.68) | 0.85 (3.46) |
| cqr+iw | 0.91 (2.65) | 0.84 (2.65) | 0.83 (2.37) |

Model: **gp**

| method | random | block | region |
|---|---|---|---|
| none | 0.81 (3.56) | 0.82 (4.26) | 0.79 (4.48) |
| split | 0.80 (3.43) | 0.72 (3.36) | 0.68 (3.41) |
| cqr | 0.80 (3.42) | 0.82 (4.17) | 0.79 (4.38) |
| cqr+local | 0.81 (3.21) | 0.81 (3.97) | 0.76 (17.66) |
| cqr+iw | 0.80 (3.42) | 0.81 (4.11) | 0.70 (4.07) |

##### Leave-one-region-out coverage by held-out region (model qgbm)

| method | test region 0 | test region 1 | test region 2 | test region 3 | test region 4 |
|---|---|---|---|---|---|
| none | 0.82 | 0.78 | 0.67 | 0.82 | 0.92 |
| split | 0.74 | 0.8 | 0.52 | 0.87 | 1.0 |
| cqr | 0.82 | 0.78 | 0.67 | 0.82 | 0.92 |
| cqr+local | 0.82 | 0.89 | 0.68 | 0.93 | 0.92 |
| cqr+iw | 0.82 | 0.78 | 0.67 | 0.82 | 0.92 |

##### Exceedance probability: Brier score / expected calibration error

| model | random | block | region |
|---|---|---|---|
| gp | 0.107 / 0.034 | 0.143 / 0.086 | 0.181 / 0.158 |
| idw | 0.097 / 0.064 | 0.191 / 0.192 | 0.160 / 0.161 |
| naive | 0.169 / 0.029 | 0.171 / 0.058 | 0.190 / 0.163 |
| qgbm | 0.087 / 0.020 | 0.136 / 0.087 | 0.132 / 0.069 |

##### Data scarcity under leave-region-out: coverage (RMSE) by training fraction

Model: **gp**

| method | 0.1 | 0.25 | 0.5 | 1.0 |
|---|---|---|---|---|
| cqr | 0.78 (2.14) | 0.79 (1.86) | 0.78 (1.93) | 0.78 (1.87) |
| cqr+iw | 0.86 (2.14) | 0.75 (1.86) | 0.67 (1.93) | 0.69 (1.87) |
| none | 0.79 (2.14) | 0.80 (1.86) | 0.78 (1.93) | 0.80 (1.87) |
| split | 0.68 (2.14) | 0.72 (1.86) | 0.66 (1.93) | 0.70 (1.87) |

Model: **qgbm**

| method | 0.1 | 0.25 | 0.5 | 1.0 |
|---|---|---|---|---|
| cqr | 0.78 (1.97) | 0.79 (1.97) | 0.82 (1.97) | 0.82 (1.97) |
| cqr+iw | 0.88 (1.97) | 0.80 (1.97) | 0.82 (1.97) | 0.82 (1.97) |
| none | 0.78 (1.97) | 0.79 (1.97) | 0.82 (1.97) | 0.82 (1.97) |
| split | 0.81 (1.97) | 0.82 (1.97) | 0.81 (1.97) | 0.81 (1.97) |

