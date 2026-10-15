#### Synthetic benchmark (known truth)

##### Accuracy under different validation schemes (weighted mean over folds and repeats)

| model | R2 random | R2 block | R2 region | RMSE (log1p scale) random | RMSE (log1p scale) block | RMSE (log1p scale) region |
|---|---|---|---|---|---|---|
| gp | 0.82 | 0.75 | 0.23 | 0.58 | 0.62 | 0.81 |
| idw | 0.74 | 0.54 | -1.81 | 0.7 | 0.83 | 1.55 |
| naive | -0.0 | -0.38 | -1.75 | 1.4 | 1.46 | 1.57 |
| qgbm | 0.86 | 0.77 | 0.16 | 0.52 | 0.6 | 0.89 |

##### Interval coverage by scheme (nominal 80%); width in parentheses

Model: **qgbm**

| method | random | block | region |
|---|---|---|---|
| none | 0.65 (0.96) | 0.59 (1.03) | 0.47 (1.44) |
| split | 0.81 (1.28) | 0.73 (1.26) | 0.52 (1.27) |
| cqr | 0.80 (1.34) | 0.75 (1.41) | 0.59 (1.82) |
| split+local | 0.83 (1.37) | 0.76 (1.43) | 0.72 (2.23) |
| cqr+local | 0.82 (1.43) | 0.78 (1.55) | 0.75 (2.63) |
| split+iw | 0.82 (1.29) | 0.74 (1.31) | 0.81 (3.00) |
| cqr+iw | 0.81 (1.35) | 0.74 (1.39) | 0.83 (3.35) |

Model: **gp**

| method | random | block | region |
|---|---|---|---|
| none | 0.81 (1.47) | 0.79 (1.52) | 0.69 (1.68) |
| split | 0.80 (1.46) | 0.77 (1.47) | 0.61 (1.44) |
| cqr | 0.80 (1.48) | 0.79 (1.54) | 0.68 (1.67) |
| split+local | 0.82 (1.58) | 0.81 (1.64) | 0.80 (2.38) |
| cqr+local | 0.83 (1.59) | 0.83 (1.71) | 0.84 (2.62) |
| split+iw | 0.80 (1.46) | 0.77 (1.48) | 0.87 (3.05) |
| cqr+iw | 0.80 (1.47) | 0.78 (1.52) | 0.90 (3.27) |

##### Leave-one-region-out coverage by held-out region (model qgbm)

| method | test region 0 | test region 1 | test region 2 | test region 3 |
|---|---|---|---|---|
| none | 0.47 | 0.65 | 0.4 | 0.37 |
| split | 0.52 | 0.61 | 0.59 | 0.35 |
| cqr | 0.61 | 0.76 | 0.55 | 0.45 |
| split+local | 0.75 | 0.87 | 0.77 | 0.45 |
| cqr+local | 0.78 | 0.91 | 0.76 | 0.55 |
| split+iw | 0.86 | 0.95 | 0.83 | 0.58 |
| cqr+iw | 0.82 | 0.94 | 0.89 | 0.67 |

##### Exceedance probability: Brier score / expected calibration error

| model | random | block | region |
|---|---|---|---|
| gp | 0.056 / 0.040 | 0.059 / 0.046 | 0.093 / 0.104 |
| idw | 0.069 / 0.047 | 0.087 / 0.075 | 0.249 / 0.270 |
| naive | 0.160 / 0.020 | 0.169 / 0.116 | 0.209 / 0.264 |
| qgbm | 0.061 / 0.055 | 0.071 / 0.063 | 0.165 / 0.173 |

##### Data scarcity under leave-region-out: coverage (RMSE) by training fraction

Model: **gp**

| method | 0.1 | 0.25 | 0.5 | 1.0 |
|---|---|---|---|---|
| cqr | 0.81 (0.73) | 0.80 (0.67) | 0.80 (0.66) | 0.80 (0.67) |
| cqr+iw | 0.93 (0.73) | 0.93 (0.67) | 0.90 (0.66) | 0.91 (0.67) |
| cqr+local | 0.93 (0.73) | 0.91 (0.67) | 0.90 (0.66) | 0.88 (0.67) |
| none | 0.71 (0.73) | 0.78 (0.67) | 0.81 (0.66) | 0.80 (0.67) |
| split | 0.79 (0.73) | 0.75 (0.67) | 0.73 (0.66) | 0.72 (0.67) |

Model: **qgbm**

| method | 0.1 | 0.25 | 0.5 | 1.0 |
|---|---|---|---|---|
| cqr | 0.70 (1.23) | 0.69 (0.98) | 0.76 (0.89) | 0.73 (0.88) |
| cqr+iw | 0.85 (1.23) | 0.85 (0.98) | 0.87 (0.89) | 0.85 (0.88) |
| cqr+local | 0.89 (1.23) | 0.84 (0.98) | 0.85 (0.89) | 0.82 (0.88) |
| none | 0.54 (1.23) | 0.53 (0.98) | 0.63 (0.89) | 0.63 (0.88) |
| split | 0.71 (1.23) | 0.64 (0.98) | 0.63 (0.89) | 0.61 (0.88) |


##### Spatiotemporal forecasting (synthetic): coverage by scheme and lead time, model qgbm

| method | site / all | time / lead 1 | time / lead 2 | time / lead 3 |
|---|---|---|---|---|
| cqr | 0.73 | 0.71 | 0.74 | 0.69 |
| cqr+iw | 0.73 | 0.87 | 0.99 | 0.99 |
| none | 0.65 | 0.61 | 0.63 | 0.61 |
| split | 0.71 | 0.73 | 0.79 | 0.71 |
