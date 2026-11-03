# DCR-Min: DCR for the two minimisation variants

160 dev instances with valid runs of all three DCR variants. Every schedule was built and independently re-checked by the pinned Dataset evaluator (all agree: True). Comparator rows are the stored runs in `results/store/` on the same instances (same D and B; they solve the joint problem, not the minimisation problem, so they are a reference, not a tuned rival).

References (evaluation only, from the hidden QoS calibration; no scheduler sees them): `t_fast` = makespan of the fastest calibrated reference schedule (budget-agnostic); `cost_floor` = the calibrated deadline-conditioned cost floor at the instance deadline; `witness` = the instance's jointly-feasible witness schedule. All ratios: lower is better.

## 1. Minimise makespan subject to cost <= B (instance deadline ignored)

Ratio = makespan / t_fast. Only runs with cost <= B count.

| Algorithm | cost <= B | geo-mean ratio | median | p90 | DCR-Min better / tie / worse |
|---|---:|---:|---:|---:|---:|
| **DCR-Min (dcr-min-makespan)** | 160/160 | 1.483 | 1.339 | 2.565 | — |
| DCR-v4R, one run (instance D and B) | 160/160 | 2.176 | 2.143 | 5.205 | 157 / 3 / 0 |
| bdc | 156/160 | 2.527 | 2.467 | 5.739 | 159 / 0 / 1 |
| bdheft | 149/160 | 3.591 | 3.084 | 12.865 | 158 / 0 / 2 |
| bdsd | 160/160 | 3.862 | 3.013 | 14.182 | 159 / 0 / 1 |
| dbcs | 160/160 | 4.020 | 3.805 | 12.402 | 156 / 3 / 1 |
| bddc | 61/160 | 2.108 | 2.113 | 3.579 | 159 / 0 / 1 |
| heft-ifc | 8/160 | 1.000 | 1.000 | 1.000 | 156 / 2 / 2 |
| peft-ifc | 4/160 | 1.260 | 1.285 | 1.493 | 160 / 0 / 0 |
| dcr-v1-admission | 160/160 | 2.222 | 2.089 | 6.162 | 148 / 0 / 12 |

DCR-Min makespan beats the calibration witness (a budget-feasible schedule) on 147/160 instances.

## 2. Minimise compute cost subject to makespan <= D (instance budget ignored)

Ratio = cost / cost_floor. Only runs with makespan <= D count.

| Algorithm | makespan <= D | geo-mean ratio | median | p90 | DCR-Min better / tie / worse |
|---|---:|---:|---:|---:|---:|
| **DCR-Min (dcr-min-cost)** | 160/160 | 0.8495 | 0.8930 | 1.0088 | — |
| DCR-v4R, one run (instance D and B) | 159/160 | 3.2800 | 2.6649 | 14.9143 | 158 / 1 / 1 |
| bdc | 120/160 | 4.6949 | 3.6814 | 15.5400 | 160 / 0 / 0 |
| bdheft | 79/160 | 7.1379 | 14.2442 | 20.2782 | 160 / 0 / 0 |
| bdsd | 94/160 | 4.5391 | 4.5932 | 15.0197 | 160 / 0 / 0 |
| dbcs | 76/160 | 7.5790 | 14.7791 | 22.0868 | 160 / 0 / 0 |
| bddc | 133/160 | 5.1825 | 5.0525 | 17.8143 | 160 / 0 / 0 |
| heft-ifc | 160/160 | 4.5038 | 4.8732 | 20.9964 | 160 / 0 / 0 |
| peft-ifc | 151/160 | 4.9681 | 5.1860 | 21.5427 | 160 / 0 / 0 |
| dcr-v1-admission | 140/160 | 3.7658 | 3.0389 | 15.0230 | 160 / 0 / 0 |

DCR-Min cost is below the calibrated cost floor on 141/160 instances and below the witness cost on 141/160.

## 3. By QoS level (geo-mean ratio; constraint-respecting runs only)

| QoS | n | makespan/t_fast DCR-Min | DCR-v4R | cost/floor DCR-Min | DCR-v4R |
|---|---:|---:|---:|---:|---:|
| relaxed | 54 | 1.317 | 2.263 | 0.7982 | 12.9094 |
| moderate | 52 | 2.363 | 3.950 | 0.8176 | 2.7034 |
| tight | 54 | 1.066 | 1.179 | 0.9382 | 0.9818 |

## 4. Tuning instances vs untouched instances (geo-mean ratio; constraint-respecting runs only)

The defaults were chosen on the tuning subset, so that subset is in-sample. `/LB` columns use the certified lower bounds LB_T and LB_C(D), so they are upper bounds on the true optimality gap.

| Subset | n | makespan/t_fast DCR-Min | DCR-v4R | makespan/LB_T DCR-Min | cost/floor DCR-Min | DCR-v4R | cost/LB_C(D) DCR-Min |
|---|---:|---:|---:|---:|---:|---:|---:|
| tuning | 35 | 1.402 | 1.928 | 3.121 | 0.9071 | 2.6662 | 6.982 |
| untouched | 125 | 1.507 | 2.251 | 4.136 | 0.8341 | 3.4776 | 5.239 |

## 5. Search effort and runtime (2-core cloud VM, 2 processes, so indicative only)

| Algorithm | median probes | max probes | median runtime (s) | max runtime (s) | runtime / DCR-v4R (median) |
|---|---:|---:|---:|---:|---:|
| dcr-v4-rescue | 1.0 | 1 | 0.55 | 28.44 | 1.00 |
| dcr-min-makespan | 12.0 | 12 | 28.87 | 512.45 | 78.92 |
| dcr-min-cost | 12.0 | 12 | 24.64 | 434.85 | 55.63 |

Search outcomes: dcr-min-makespan: {'ok': 160}; dcr-min-cost: {'ok': 160}

