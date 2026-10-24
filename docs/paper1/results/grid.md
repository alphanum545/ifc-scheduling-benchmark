# Deadline x budget tightness grid (ifc-grid-v1)

3975/3975 instances have valid results for all 12 algorithms.


## dcr-v1-admission: joint feasible % (rows deadline fraction, columns budget fraction)

| α \ β | 1/10 | 3/10 | 1/2 | 7/10 | 9/10 |
|---|---:|---:|---:|---:|---:|
| 1/100 | 74 | 77 | 82 | 93 | 99 |
| 1/20 | 15 | 28 | 54 | 88 | 100 |
| 1/4 | 26 | 53 | 89 | 100 | 100 |
| 1/2 | 84 | 97 | 100 | 100 | 100 |
| 3/4 | 100 | 100 | 100 | 100 | 100 |

## bdc: joint feasible % (rows deadline fraction, columns budget fraction)

| α \ β | 1/10 | 3/10 | 1/2 | 7/10 | 9/10 |
|---|---:|---:|---:|---:|---:|
| 1/100 | 36 | 38 | 43 | 48 | 54 |
| 1/20 | 5 | 18 | 43 | 79 | 90 |
| 1/4 | 10 | 40 | 87 | 99 | 100 |
| 1/2 | 51 | 92 | 99 | 100 | 100 |
| 3/4 | 89 | 100 | 100 | 100 | 100 |

## dcr-v3-rescue: joint feasible % (rows deadline fraction, columns budget fraction)

| α \ β | 1/10 | 3/10 | 1/2 | 7/10 | 9/10 |
|---|---:|---:|---:|---:|---:|
| 1/100 | 91 | 97 | 97 | 99 | 99 |
| 1/20 | 84 | 91 | 99 | 100 | 100 |
| 1/4 | 92 | 99 | 100 | 100 | 100 |
| 1/2 | 100 | 100 | 100 | 100 | 100 |
| 3/4 | 100 | 100 | 100 | 100 | 100 |

## bdsd: joint feasible % (rows deadline fraction, columns budget fraction)

| α \ β | 1/10 | 3/10 | 1/2 | 7/10 | 9/10 |
|---|---:|---:|---:|---:|---:|
| 1/100 | 1 | 2 | 2 | 4 | 4 |
| 1/20 | 25 | 34 | 42 | 47 | 49 |
| 1/4 | 51 | 69 | 74 | 76 | 75 |
| 1/2 | 57 | 79 | 80 | 80 | 81 |
| 3/4 | 60 | 85 | 94 | 97 | 97 |

## DCR-v1 Admission minus BDC (percentage points); * = exact McNemar p < 0.05 (uncorrected)

| α \ β | 1/10 | 3/10 | 1/2 | 7/10 | 9/10 |
|---|---:|---:|---:|---:|---:|
| 1/100 | +37* | +39* | +39* | +45* | +45* |
| 1/20 | +10* | +9* | +11* | +9* | +10* |
| 1/4 | +16* | +14* | +2 | +1 | +0 |
| 1/2 | +33* | +5* | +1 | +0 | +0 |
| 3/4 | +11* | +0 | +0 | +0 | +0 |

Cells where DCR-v1 Admission is significantly better: 15; significantly worse: 0 (of 25).

## Whole grid

| Algorithm | Joint feasible | 95% CI |
|---|---:|---|
| dcr-v3-rescue | 3893 (97.9%) | 97.4–98.3% |
| dcr-v1-admission | 3274 (82.4%) | 81.1–83.5% |
| dcr-v1 | 3274 (82.4%) | 81.1–83.5% |
| dcr-v0 | 3261 (82.0%) | 80.8–83.2% |
| dcr-v0-opt | 3261 (82.0%) | 80.8–83.2% |
| bdc | 2739 (68.9%) | 67.4–70.3% |
| bdsd | 2174 (54.7%) | 53.1–56.2% |
| dbcs | 2042 (51.4%) | 49.8–52.9% |
| bdheft | 1785 (44.9%) | 43.4–46.5% |
| bddc | 572 (14.4%) | 13.3–15.5% |
| heft-ifc | 171 (4.3%) | 3.7–5.0% |
| peft-ifc | 33 (0.8%) | 0.6–1.2% |
