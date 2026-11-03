# DCR-Min v2: minimisation study (dev + expansion)

28 runs on 4 instances; 4 instances have valid, error-free runs of all 5 algorithms (errors: 0; evaluator build/re-check agree on 28/28; policy calendar agrees with the evaluator on 20/20 DCR runs).

Ratios are geo-means, lower is better: makespan / `t_fast` and cost / `cost_floor` (hidden calibration references, evaluation only). `search` = DCR-Min v2 before its polish. Constraint-respecting runs only; a run that breaks the constraint counts as a loss in win/tie/loss.

## Dev set (4 instances)

### Min makespan s.t. cost <= B

| Method | cost <= B | makespan / t_fast | median | p90 | v2 better / tie / worse |
|---|---:|---:|---:|---:|---:|
| **DCR-Min v2** | 4/4 | 1.709 | 1.744 | 2.993 | — |
| DCR-Min v2 search only | 4/4 | 1.716 | 1.754 | 2.994 | 3 / 1 / 0 |
| DCR-v4R, one run | 4/4 | 3.012 | 3.163 | 3.205 | 4 / 0 / 0 |
| LOSS1 (from HEFT) | 4/4 | 5.244 | 7.900 | 9.660 | 4 / 0 / 0 |

### Min cost s.t. makespan <= D

| Method | makespan <= D | cost / cost_floor | median | p90 | v2 better / tie / worse |
|---|---:|---:|---:|---:|---:|
| **DCR-Min v2** | 4/4 | 0.9090 | 0.9452 | 0.9477 | — |
| DCR-Min v2 search only | 4/4 | 0.9101 | 0.9467 | 0.9477 | 3 / 1 / 0 |
| DCR-v4R, one run | 4/4 | 6.2622 | 12.2742 | 12.9794 | 4 / 0 / 0 |
| deadline-LOSS (from HEFT) | 4/4 | 0.9167 | 0.9482 | 1.0150 | 2 / 0 / 2 |

### By size and QoS (geo-mean ratio; v2 / baseline in brackets)

| Group | n | makespan v2 | (v2/v4R) | (v2/LOSS1) | cost v2 | (v2/v4R) | (v2/dLOSS) |
|---|---:|---:|---:|---:|---:|---:|---:|
| tasks=60 | 4 | 1.709 | 0.567 | 0.326 | 0.9090 | 0.145 | 0.992 |
| qos=moderate | 2 | 2.285 | 0.788 | 0.262 | 0.8730 | 0.281 | 1.019 |
| qos=relaxed | 2 | 1.278 | 0.408 | 0.406 | 0.9464 | 0.075 | 0.965 |

### Hard constraints and runtime

- min-makespan cost <= B: 4/4; min-cost makespan <= D: 4/4; deadline-LOSS start (HEFT) meets D: 4/4.
- Search status (cost): {'ok': 4}.
- dcr-v4-rescue: median runtime 0.03 s, p90 0.0 s, max 0.0 s.
- dcr-min-v2-makespan: median runtime 2.01 s, p90 2.5 s, max 2.5 s.
- dcr-min-v2-cost: median runtime 1.76 s, p90 2.6 s, max 2.6 s.
- loss1-makespan: median runtime 0.08 s, p90 0.1 s, max 0.1 s.
- deadline-loss-cost: median runtime 0.09 s, p90 0.1 s, max 0.1 s.
- dcr-min-v2-makespan polish: re-timings median 334, max 381; moves median 3, improved 3/4.
- dcr-min-v2-cost polish: re-timings median 81, max 125; moves median 1, improved 3/4.

## Dev + expansion (4 instances)

### Min makespan s.t. cost <= B

| Method | cost <= B | makespan / t_fast | median | p90 | v2 better / tie / worse |
|---|---:|---:|---:|---:|---:|
| **DCR-Min v2** | 4/4 | 1.709 | 1.744 | 2.993 | — |
| DCR-Min v2 search only | 4/4 | 1.716 | 1.754 | 2.994 | 3 / 1 / 0 |
| DCR-v4R, one run | 4/4 | 3.012 | 3.163 | 3.205 | 4 / 0 / 0 |
| LOSS1 (from HEFT) | 4/4 | 5.244 | 7.900 | 9.660 | 4 / 0 / 0 |

### Min cost s.t. makespan <= D

| Method | makespan <= D | cost / cost_floor | median | p90 | v2 better / tie / worse |
|---|---:|---:|---:|---:|---:|
| **DCR-Min v2** | 4/4 | 0.9090 | 0.9452 | 0.9477 | — |
| DCR-Min v2 search only | 4/4 | 0.9101 | 0.9467 | 0.9477 | 3 / 1 / 0 |
| DCR-v4R, one run | 4/4 | 6.2622 | 12.2742 | 12.9794 | 4 / 0 / 0 |
| deadline-LOSS (from HEFT) | 4/4 | 0.9167 | 0.9482 | 1.0150 | 2 / 0 / 2 |

### By size and QoS (geo-mean ratio; v2 / baseline in brackets)

| Group | n | makespan v2 | (v2/v4R) | (v2/LOSS1) | cost v2 | (v2/v4R) | (v2/dLOSS) |
|---|---:|---:|---:|---:|---:|---:|---:|
| tasks=60 | 4 | 1.709 | 0.567 | 0.326 | 0.9090 | 0.145 | 0.992 |
| qos=moderate | 2 | 2.285 | 0.788 | 0.262 | 0.8730 | 0.281 | 1.019 |
| qos=relaxed | 2 | 1.278 | 0.408 | 0.406 | 0.9464 | 0.075 | 0.965 |

### Hard constraints and runtime

- min-makespan cost <= B: 4/4; min-cost makespan <= D: 4/4; deadline-LOSS start (HEFT) meets D: 4/4.
- Search status (cost): {'ok': 4}.
- dcr-v4-rescue: median runtime 0.03 s, p90 0.0 s, max 0.0 s.
- dcr-min-v2-makespan: median runtime 2.01 s, p90 2.5 s, max 2.5 s.
- dcr-min-v2-cost: median runtime 1.76 s, p90 2.6 s, max 2.6 s.
- loss1-makespan: median runtime 0.08 s, p90 0.1 s, max 0.1 s.
- deadline-loss-cost: median runtime 0.09 s, p90 0.1 s, max 0.1 s.
- dcr-min-v2-makespan polish: re-timings median 334, max 381; moves median 3, improved 3/4.
- dcr-min-v2-cost polish: re-timings median 81, max 125; moves median 1, improved 3/4.

## DCR-Min v2 vs v1 (dev, 4 instances)

- makespan: v2/v1 geo-mean 1.0125 (better / tie / worse 1 / 1 / 2); v2 search only / v1 1.0169 (0 / 0 / 4).
- cost: v2/v1 geo-mean 0.9974 (better / tie / worse 3 / 1 / 0); v2 search only / v1 0.9986 (1 / 3 / 0).

## Exact CP-SAT on the 60-task instances (4 rows, dev + expansion)

Optimality gap = (DCR-Min v2 - CP-SAT lower bound) / DCR-Min v2, so it bounds how far v2 can be from optimal. `best` = the best schedule CP-SAT found (warm-started from v2, so never worse), verified by the evaluator.

- **makespan**: statuses {'FEASIBLE': 2}; verified 2/2. v2 proved optimal on 0/2. Gap to the CP-SAT bound: median 80.4%, p90 80.4%, max 80.4%. CP-SAT's best / v2: geo-mean 0.8375, improved on 2/2.
  - moderate: n=2, median gap 80.4%, p90 80.4%
- **cost**: statuses {'FEASIBLE': 2}; verified 2/2. v2 proved optimal on 0/2. Gap to the CP-SAT bound: median 26.7%, p90 26.7%, max 26.7%. CP-SAT's best / v2: geo-mean 0.8619, improved on 2/2.
  - moderate: n=2, median gap 26.7%, p90 26.7%

