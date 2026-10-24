# Report: ablations-dev

Instance set: **dev**. Algorithms: Ablation: control (= DCR-v1 Admission), Ablation: no priced reserve, Ablation: zero prices, Ablation: time-only ranking, Ablation: budget-only ranking, Ablation: weighted-sum ranking, DCR-v1 Admission, BDC (w=0.5). Highlight: Ablation: control (= DCR-v1 Admission). Cases: 160 selected, **160 compared** (every selected algorithm valid, and deterministic where checked).

Determinism was not re-observed for 970 one-repetition runs; the replay check against the historical results covers it.

## Validity

| Algorithm | Runs | Valid + deterministic | Errors | Invalid | Nondeterministic | Missing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Ablation: control (= DCR-v1 Admission) | 160 | 160 | 0 | 0 | 0 | 0 |
| Ablation: no priced reserve | 160 | 160 | 0 | 0 | 0 | 0 |
| Ablation: zero prices | 160 | 160 | 0 | 0 | 0 | 0 |
| Ablation: time-only ranking | 160 | 160 | 0 | 0 | 0 | 0 |
| Ablation: budget-only ranking | 160 | 160 | 0 | 0 | 0 | 0 |
| Ablation: weighted-sum ranking | 160 | 160 | 0 | 0 | 0 | 0 |
| DCR-v1 Admission | 160 | 160 | 0 | 0 | 0 | 0 |
| BDC (w=0.5) | 160 | 160 | 0 | 0 | 0 | 0 |

## Joint deadline-and-budget feasibility

| Algorithm | Joint feasible | Deadline met | Budget met | Median runtime (ms) | Runtime / BDC (w=0.5) median | p95 | max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Ablation: weighted-sum ranking | 142/160 (88.8%) | 142/160 (88.8%) | 160/160 (100.0%) | 720 | 0.853x | 2.998x | 4.318x |
| **Ablation: control (= DCR-v1 Admission)** | 140/160 (87.5%) | 140/160 (87.5%) | 160/160 (100.0%) | 707 | 0.949x | 3.163x | 4.653x |
| Ablation: zero prices | 140/160 (87.5%) | 140/160 (87.5%) | 160/160 (100.0%) | 723 | 0.913x | 3.027x | 4.873x |
| DCR-v1 Admission | 140/160 (87.5%) | 140/160 (87.5%) | 160/160 (100.0%) | 370 | 0.594x | 1.162x | 1.419x |
| Ablation: no priced reserve | 137/160 (85.6%) | 137/160 (85.6%) | 160/160 (100.0%) | 387 | 0.469x | 1.846x | 3.485x |
| BDC (w=0.5) | 120/160 (75.0%) | 120/160 (75.0%) | 156/160 (97.5%) | 706 | - | - | - |
| Ablation: time-only ranking | 83/160 (51.9%) | 83/160 (51.9%) | 160/160 (100.0%) | 618 | 0.680x | 2.677x | 4.189x |
| Ablation: budget-only ranking | 82/160 (51.2%) | 82/160 (51.2%) | 160/160 (100.0%) | 567 | 0.676x | 2.754x | 3.996x |

Runtime is policy time only (schedule construction and scoring excluded), median over repetitions; ratios are paired on the same machine and case, p95 is nearest-rank.

## Joint feasibility by workflow family

| Workflow family | cybershake | genome | ligo | montage | sipht |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ablation: control (= DCR-v1 Admission) | 27/32 | 29/32 | 31/32 | 25/32 | 28/32 |
| Ablation: no priced reserve | 27/32 | 29/32 | 31/32 | 24/32 | 26/32 |
| Ablation: zero prices | 27/32 | 29/32 | 31/32 | 25/32 | 28/32 |
| Ablation: time-only ranking | 13/32 | 18/32 | 17/32 | 15/32 | 20/32 |
| Ablation: budget-only ranking | 23/32 | 23/32 | 10/32 | 7/32 | 19/32 |
| Ablation: weighted-sum ranking | 29/32 | 29/32 | 31/32 | 25/32 | 28/32 |
| DCR-v1 Admission | 27/32 | 29/32 | 31/32 | 25/32 | 28/32 |
| BDC (w=0.5) | 25/32 | 22/32 | 28/32 | 22/32 | 23/32 |

## Joint feasibility by number of tasks

| Number of tasks | 60 | 100 | 200 | 400 | 600 | 800 | 1000 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Ablation: control (= DCR-v1 Admission) | 22/23 | 23/24 | 18/23 | 21/24 | 19/22 | 18/22 | 19/22 |
| Ablation: no priced reserve | 19/23 | 22/24 | 19/23 | 21/24 | 19/22 | 18/22 | 19/22 |
| Ablation: zero prices | 22/23 | 23/24 | 18/23 | 21/24 | 19/22 | 18/22 | 19/22 |
| Ablation: time-only ranking | 14/23 | 13/24 | 10/23 | 13/24 | 10/22 | 11/22 | 12/22 |
| Ablation: budget-only ranking | 18/23 | 16/24 | 10/23 | 13/24 | 12/22 | 7/22 | 6/22 |
| Ablation: weighted-sum ranking | 21/23 | 24/24 | 18/23 | 21/24 | 20/22 | 18/22 | 20/22 |
| DCR-v1 Admission | 22/23 | 23/24 | 18/23 | 21/24 | 19/22 | 18/22 | 19/22 |
| BDC (w=0.5) | 16/23 | 17/24 | 14/23 | 18/24 | 21/22 | 16/22 | 18/22 |

## Joint feasibility by qos tightness

| QoS tightness | relaxed | moderate | tight |
| --- | ---: | ---: | ---: |
| Ablation: control (= DCR-v1 Admission) | 54/54 | 47/52 | 39/54 |
| Ablation: no priced reserve | 54/54 | 47/52 | 36/54 |
| Ablation: zero prices | 54/54 | 47/52 | 39/54 |
| Ablation: time-only ranking | 54/54 | 2/52 | 27/54 |
| Ablation: budget-only ranking | 45/54 | 26/52 | 11/54 |
| Ablation: weighted-sum ranking | 54/54 | 48/52 | 40/54 |
| DCR-v1 Admission | 54/54 | 47/52 | 39/54 |
| BDC (w=0.5) | 54/54 | 45/52 | 21/54 |

## Joint feasibility by scenario

| Scenario | balanced | compute_constrained | network_constrained |
| --- | ---: | ---: | ---: |
| Ablation: control (= DCR-v1 Admission) | 46/53 | 46/54 | 48/53 |
| Ablation: no priced reserve | 45/53 | 45/54 | 47/53 |
| Ablation: zero prices | 46/53 | 46/54 | 48/53 |
| Ablation: time-only ranking | 29/53 | 25/54 | 29/53 |
| Ablation: budget-only ranking | 30/53 | 27/54 | 25/53 |
| Ablation: weighted-sum ranking | 47/53 | 47/54 | 48/53 |
| DCR-v1 Admission | 46/53 | 46/54 | 48/53 |
| BDC (w=0.5) | 38/53 | 41/54 | 41/53 |

## Joint feasibility by resource scale

| Resource scale | S01 | S02 | S03 |
| --- | ---: | ---: | ---: |
| Ablation: control (= DCR-v1 Admission) | 49/54 | 44/52 | 47/54 |
| Ablation: no priced reserve | 47/54 | 44/52 | 46/54 |
| Ablation: zero prices | 49/54 | 44/52 | 47/54 |
| Ablation: time-only ranking | 28/54 | 23/52 | 32/54 |
| Ablation: budget-only ranking | 25/54 | 29/52 | 28/54 |
| Ablation: weighted-sum ranking | 50/54 | 44/52 | 48/54 |
| DCR-v1 Admission | 49/54 | 44/52 | 47/54 |
| BDC (w=0.5) | 47/54 | 42/52 | 31/54 |

## Ablation: control (= DCR-v1 Admission) against each algorithm

| Against | Cases only Ablation: control (= DCR-v1 Admission) is feasible | Cases only the other is feasible | Both feasible | Makespan ratio (median) | Cost ratio (median) | Energy ratio (median) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Ablation: no priced reserve | 4 | 1 | 136 | 1.000 | 1.000 | 1.000 |
| Ablation: zero prices | 0 | 0 | 140 | 1.000 | 1.000 | 1.000 |
| Ablation: time-only ranking | 57 | 0 | 83 | 0.759 | 0.931 | 1.023 |
| Ablation: budget-only ranking | 61 | 3 | 79 | 0.188 | 4.978 | 0.696 |
| Ablation: weighted-sum ranking | 1 | 3 | 139 | 0.988 | 1.001 | 0.967 |
| DCR-v1 Admission | 0 | 0 | 140 | 1.000 | 1.000 | 1.000 |
| BDC (w=0.5) | 24 | 4 | 116 | 0.851 | 1.006 | 0.952 |

Ratios are Ablation: control (= DCR-v1 Admission) / other on cases where both are jointly feasible; below 1 favours Ablation: control (= DCR-v1 Admission). Energy = compute + network energy.

## Replay against the historical results

| Algorithm | Reference set | Instances compared | Exact matches | Mismatches |
| --- | --- | ---: | ---: | ---: |
| HEFT-IFC | `primary:deterministic_heft_ifc` | 160 | 160 | 0 |
| HEFT-IFC | `expansion:deterministic_heft_ifc` | 1890 | 1890 | 0 |
| PEFT-IFC | `primary:deterministic_peft_ifc` | 160 | 160 | 0 |
| PEFT-IFC | `expansion:deterministic_peft_ifc` | 1890 | 1890 | 0 |
| BDHEFT (a=0.5) | `primary:bdheft_ifc_a05` | 160 | 160 | 0 |
| BDHEFT (a=0.5) | `expansion:bdheft_ifc_a05` | 1890 | 1890 | 0 |
| DBCS | `primary:dbcs_ifc` | 160 | 160 | 0 |
| DBCS | `expansion:dbcs_ifc` | 1890 | 1890 | 0 |
| BDSD | `primary:bdsd_ifc` | 160 | 160 | 0 |
| BDSD | `expansion:bdsd_ifc` | 1890 | 1890 | 0 |
| BDDC (w=0.5) | `primary:bddc_ifc_w05` | 160 | 160 | 0 |
| BDDC (w=0.5) | `expansion:bddc_ifc_w05` | 1890 | 1890 | 0 |
| BDC (w=0.5) | `primary:bdc_ifc_w05` | 160 | 160 | 0 |
| BDC (w=0.5) | `dcr:bdc_ifc_w05` | 160 | 160 | 0 |
| BDC (w=0.5) | `expansion:bdc_ifc_w05` | 1890 | 1890 | 0 |
| DCR-v0 | `dcr:dcr_ifc_v0` | 160 | 160 | 0 |
| DCR-v0 | `dcr:dcr_ifc_v0@dev-run` | 160 | 160 | 0 |
| DCR-v0 (optimized) | `dcr:dcr_ifc_v0_optimized` | 160 | 160 | 0 |
| DCR-v1 (full ranking) | `dcr:dcr_ifc_v1_arrival` | 160 | 160 | 0 |
| DCR-v1 Admission | `dcr:dcr_ifc_v1_arrival_admission` | 160 | 160 | 0 |
| DCR-v1 Admission | `core24:dcr-v1-admission` | 24 | 24 | 0 |
| DCR-v1 Admission | `expansion:dcr-v1-admission` | 1890 | 1890 | 0 |
| DCR-v3 Rescue | `core24:dcr-v3-rescue` | 24 | 24 | 0 |
**Total mismatches: 0.** Every compared run reproduces its historical result exactly.

