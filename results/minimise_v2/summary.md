# DCR-Min v2: minimisation study (dev + expansion)

10570 runs on 2050 instances; 2050 instances have valid, error-free runs of all 5 algorithms (errors: 0; evaluator build/re-check agree on 10570/10570; policy calendar agrees with the evaluator on 6470/6470 DCR runs).

Ratios are geo-means, lower is better: makespan / `t_fast` and cost / `cost_floor` (hidden calibration references, evaluation only). `search` = DCR-Min v2 before its polish. Constraint-respecting runs only; a run that breaks the constraint counts as a loss in win/tie/loss.

## Dev set (160 instances)

### Min makespan s.t. cost <= B

| Method | cost <= B | makespan / t_fast | median | p90 | v2 better / tie / worse |
|---|---:|---:|---:|---:|---:|
| **DCR-Min v2** | 160/160 | 1.466 | 1.332 | 2.511 | — |
| DCR-Min v2 search only | 160/160 | 1.479 | 1.341 | 2.537 | 121 / 39 / 0 |
| DCR-v4R, one run | 160/160 | 2.176 | 2.164 | 5.205 | 159 / 0 / 1 |
| LOSS1 (from HEFT) | 160/160 | 4.557 | 4.564 | 14.804 | 157 / 2 / 1 |

### Min cost s.t. makespan <= D

| Method | makespan <= D | cost / cost_floor | median | p90 | v2 better / tie / worse |
|---|---:|---:|---:|---:|---:|
| **DCR-Min v2** | 160/160 | 0.8058 | 0.8706 | 0.9647 | — |
| DCR-Min v2 search only | 160/160 | 0.8486 | 0.8931 | 1.0088 | 145 / 15 / 0 |
| DCR-v4R, one run | 159/160 | 3.2800 | 2.6649 | 14.9143 | 160 / 0 / 0 |
| deadline-LOSS (from HEFT) | 160/160 | 0.8745 | 0.8974 | 1.1162 | 112 / 1 / 47 |

### By size and QoS (geo-mean ratio; v2 / baseline in brackets)

| Group | n | makespan v2 | (v2/v4R) | (v2/LOSS1) | cost v2 | (v2/v4R) | (v2/dLOSS) |
|---|---:|---:|---:|---:|---:|---:|---:|
| tasks=60 | 23 | 1.369 | 0.670 | 0.353 | 0.8387 | 0.247 | 0.780 |
| tasks=100 | 24 | 1.390 | 0.633 | 0.344 | 0.8901 | 0.282 | 0.914 |
| tasks=200 | 23 | 1.478 | 0.755 | 0.319 | 0.8403 | 0.288 | 0.890 |
| tasks=400 | 24 | 1.484 | 0.652 | 0.341 | 0.8112 | 0.226 | 0.938 |
| tasks=600 | 22 | 1.606 | 0.663 | 0.283 | 0.7522 | 0.205 | 0.954 |
| tasks=800 | 22 | 1.450 | 0.685 | 0.294 | 0.7830 | 0.239 | 1.024 |
| tasks=1000 | 22 | 1.510 | 0.667 | 0.321 | 0.7264 | 0.238 | 0.978 |
| qos=moderate | 52 | 2.319 | 0.587 | 0.204 | 0.7308 | 0.270 | 0.907 |
| qos=relaxed | 54 | 1.304 | 0.576 | 0.339 | 0.7845 | 0.061 | 0.864 |
| qos=tight | 54 | 1.061 | 0.900 | 0.475 | 0.9093 | 0.925 | 0.998 |

### Hard constraints and runtime

- min-makespan cost <= B: 160/160; min-cost makespan <= D: 160/160; deadline-LOSS start (HEFT) meets D: 160/160.
- Search status (cost): {'ok': 160}.
- dcr-v4-rescue: median runtime 0.72 s, p90 4.4 s, max 52.2 s.
- dcr-min-v2-makespan: median runtime 50.19 s, p90 317.4 s, max 990.7 s.
- dcr-min-v2-cost: median runtime 38.05 s, p90 227.7 s, max 733.2 s.
- loss1-makespan: median runtime 0.99 s, p90 8.5 s, max 22.6 s.
- deadline-loss-cost: median runtime 4.00 s, p90 32.3 s, max 82.7 s.
- dcr-min-v2-makespan polish: re-timings median 1395, max 10000; moves median 2, improved 121/160.
- dcr-min-v2-cost polish: re-timings median 670, max 10000; moves median 31, improved 145/160.

## Expansion set (never used for tuning) (1890 instances)

### Min makespan s.t. cost <= B

| Method | cost <= B | makespan / t_fast | median | p90 | v2 better / tie / worse |
|---|---:|---:|---:|---:|---:|
| **DCR-Min v2** | 1890/1890 | 1.489 | 1.322 | 2.534 | — |
| DCR-Min v2 search only | 1890/1890 | 1.505 | 1.339 | 2.559 | 1433 / 457 / 0 |
| DCR-v4R, one run | 1890/1890 | 2.223 | 2.134 | 5.287 | 1869 / 4 / 17 |
| LOSS1 (from HEFT) | 1890/1890 | 4.587 | 4.158 | 15.332 | 1860 / 16 / 14 |

### Min cost s.t. makespan <= D

| Method | makespan <= D | cost / cost_floor | median | p90 | v2 better / tie / worse |
|---|---:|---:|---:|---:|---:|
| **DCR-Min v2** | 1890/1890 | 0.7872 | 0.8603 | 0.9708 | — |
| DCR-Min v2 search only | 1890/1890 | 0.8306 | 0.8900 | 1.0042 | 1696 / 194 / 0 |
| DCR-v4R, one run | 1857/1890 | 3.2581 | 2.7500 | 14.9087 | 1889 / 1 / 0 |
| deadline-LOSS (from HEFT) | 1890/1890 | 0.8525 | 0.8935 | 1.0619 | 1278 / 20 / 592 |

### By size and QoS (geo-mean ratio; v2 / baseline in brackets)

| Group | n | makespan v2 | (v2/v4R) | (v2/LOSS1) | cost v2 | (v2/v4R) | (v2/dLOSS) |
|---|---:|---:|---:|---:|---:|---:|---:|
| tasks=60 | 270 | 1.420 | 0.660 | 0.374 | 0.8517 | 0.276 | 0.813 |
| tasks=100 | 270 | 1.408 | 0.670 | 0.334 | 0.8550 | 0.268 | 0.886 |
| tasks=200 | 270 | 1.455 | 0.686 | 0.301 | 0.8055 | 0.235 | 0.914 |
| tasks=400 | 270 | 1.507 | 0.687 | 0.313 | 0.7854 | 0.228 | 0.966 |
| tasks=600 | 270 | 1.520 | 0.671 | 0.315 | 0.7701 | 0.230 | 0.962 |
| tasks=800 | 270 | 1.562 | 0.660 | 0.322 | 0.7346 | 0.228 | 0.967 |
| tasks=1000 | 270 | 1.562 | 0.656 | 0.318 | 0.7189 | 0.226 | 0.968 |
| qos=moderate | 630 | 2.368 | 0.572 | 0.203 | 0.7141 | 0.269 | 0.917 |
| qos=relaxed | 630 | 1.304 | 0.592 | 0.347 | 0.7485 | 0.060 | 0.865 |
| qos=tight | 630 | 1.070 | 0.887 | 0.487 | 0.9127 | 0.924 | 0.993 |

### Hard constraints and runtime

- min-makespan cost <= B: 1890/1890; min-cost makespan <= D: 1890/1890; deadline-LOSS start (HEFT) meets D: 1890/1890.
- Search status (cost): {'ok': 1890}.
- dcr-v4-rescue: median runtime 0.87 s, p90 4.3 s, max 70.7 s.
- dcr-min-v2-makespan: median runtime 57.65 s, p90 334.9 s, max 1113.9 s.
- dcr-min-v2-cost: median runtime 42.30 s, p90 252.8 s, max 909.0 s.
- loss1-makespan: median runtime 0.92 s, p90 6.8 s, max 23.2 s.
- deadline-loss-cost: median runtime 4.07 s, p90 34.5 s, max 91.1 s.
- dcr-min-v2-makespan polish: re-timings median 1251, max 10000; moves median 2, improved 1433/1890.
- dcr-min-v2-cost polish: re-timings median 641, max 10000; moves median 36, improved 1696/1890.

## Dev + expansion (2050 instances)

### Min makespan s.t. cost <= B

| Method | cost <= B | makespan / t_fast | median | p90 | v2 better / tie / worse |
|---|---:|---:|---:|---:|---:|
| **DCR-Min v2** | 2050/2050 | 1.488 | 1.322 | 2.530 | — |
| DCR-Min v2 search only | 2050/2050 | 1.503 | 1.339 | 2.559 | 1554 / 496 / 0 |
| DCR-v4R, one run | 2050/2050 | 2.219 | 2.134 | 5.257 | 2028 / 4 / 18 |
| LOSS1 (from HEFT) | 2050/2050 | 4.584 | 4.168 | 15.272 | 2017 / 18 / 15 |

### Min cost s.t. makespan <= D

| Method | makespan <= D | cost / cost_floor | median | p90 | v2 better / tie / worse |
|---|---:|---:|---:|---:|---:|
| **DCR-Min v2** | 2050/2050 | 0.7887 | 0.8618 | 0.9697 | — |
| DCR-Min v2 search only | 2050/2050 | 0.8320 | 0.8910 | 1.0045 | 1841 / 209 / 0 |
| DCR-v4R, one run | 2016/2050 | 3.2598 | 2.7500 | 14.9279 | 2049 / 1 / 0 |
| deadline-LOSS (from HEFT) | 2050/2050 | 0.8542 | 0.8936 | 1.0636 | 1390 / 21 / 639 |

### By size and QoS (geo-mean ratio; v2 / baseline in brackets)

| Group | n | makespan v2 | (v2/v4R) | (v2/LOSS1) | cost v2 | (v2/v4R) | (v2/dLOSS) |
|---|---:|---:|---:|---:|---:|---:|---:|
| tasks=60 | 293 | 1.416 | 0.661 | 0.373 | 0.8507 | 0.273 | 0.811 |
| tasks=100 | 294 | 1.406 | 0.667 | 0.335 | 0.8578 | 0.269 | 0.888 |
| tasks=200 | 293 | 1.456 | 0.691 | 0.302 | 0.8082 | 0.239 | 0.912 |
| tasks=400 | 294 | 1.505 | 0.684 | 0.315 | 0.7875 | 0.228 | 0.964 |
| tasks=600 | 292 | 1.526 | 0.671 | 0.313 | 0.7687 | 0.228 | 0.961 |
| tasks=800 | 292 | 1.553 | 0.662 | 0.320 | 0.7381 | 0.229 | 0.971 |
| tasks=1000 | 292 | 1.558 | 0.657 | 0.318 | 0.7194 | 0.226 | 0.969 |
| qos=moderate | 682 | 2.364 | 0.573 | 0.203 | 0.7154 | 0.269 | 0.916 |
| qos=relaxed | 684 | 1.304 | 0.591 | 0.346 | 0.7513 | 0.060 | 0.865 |
| qos=tight | 684 | 1.069 | 0.888 | 0.486 | 0.9124 | 0.924 | 0.994 |

### Hard constraints and runtime

- min-makespan cost <= B: 2050/2050; min-cost makespan <= D: 2050/2050; deadline-LOSS start (HEFT) meets D: 2050/2050.
- Search status (cost): {'ok': 2050}.
- dcr-v4-rescue: median runtime 0.86 s, p90 4.3 s, max 70.7 s.
- dcr-min-v2-makespan: median runtime 57.21 s, p90 332.9 s, max 1113.9 s.
- dcr-min-v2-cost: median runtime 42.27 s, p90 252.5 s, max 909.0 s.
- loss1-makespan: median runtime 0.93 s, p90 6.9 s, max 23.2 s.
- deadline-loss-cost: median runtime 4.06 s, p90 34.1 s, max 91.1 s.
- dcr-min-v2-makespan polish: re-timings median 1254, max 10000; moves median 2, improved 1554/2050.
- dcr-min-v2-cost polish: re-timings median 641, max 10000; moves median 35, improved 1841/2050.

## DCR-Min v2 vs v1 (dev, 160 instances)

- makespan: v2/v1 geo-mean 0.9887 (better / tie / worse 111 / 27 / 22); v2 search only / v1 0.9974 (45 / 77 / 38).
- cost: v2/v1 geo-mean 0.9485 (better / tie / worse 146 / 14 / 0); v2 search only / v1 0.9989 (23 / 137 / 0).

## Exact CP-SAT on the 60-task instances (586 rows, dev + expansion)

Optimality gap = (DCR-Min v2 - CP-SAT lower bound) / DCR-Min v2, so it bounds how far v2 can be from optimal. `best` = the best schedule CP-SAT found (warm-started from v2, so never worse), verified by the evaluator.

- **makespan**: statuses {'FEASIBLE': 184, 'OPTIMAL': 109}; verified 293/293. v2 proved optimal on 22/293. Gap to the CP-SAT bound: median 46.7%, p90 76.6%, max 87.5%. CP-SAT's best / v2: geo-mean 0.9360, improved on 270/293.
  - tight: n=97, median gap 29.2%, p90 69.4%
  - moderate: n=97, median gap 57.1%, p90 82.3%
  - relaxed: n=99, median gap 34.3%, p90 69.9%
- **cost**: statuses {'FEASIBLE': 221, 'OPTIMAL': 72}; verified 293/293. v2 proved optimal on 21/293. Gap to the CP-SAT bound: median 12.4%, p90 66.9%, max 100.0%. CP-SAT's best / v2: geo-mean 0.9450, improved on 272/293.
  - tight: n=97, median gap 2.4%, p90 62.4%
  - moderate: n=97, median gap 12.4%, p90 57.4%
  - relaxed: n=99, median gap 14.5%, p90 100.0%

