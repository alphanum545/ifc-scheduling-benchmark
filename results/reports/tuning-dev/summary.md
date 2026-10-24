# Report: tuning-dev

Instance set: **dev**. Algorithms: BDC (w=0.1), BDC (w=0.3), BDC (w=0.5), BDC (w=0.7), BDC (w=0.9), BDDC (w=0.1), BDDC (w=0.3), BDDC (w=0.5), BDDC (w=0.7), BDDC (w=0.9), BDHEFT (a=0.1), BDHEFT (a=0.3), BDHEFT (a=0.5), BDHEFT (a=0.7), BDHEFT (a=0.9), DCR-v1 Admission. Highlight: DCR-v1 Admission. Cases: 160 selected, **160 compared** (every selected algorithm valid, and deterministic where checked).

Determinism was not re-observed for 1930 one-repetition runs; the replay check against the historical results covers it.

## Validity

| Algorithm | Runs | Valid + deterministic | Errors | Invalid | Nondeterministic | Missing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BDC (w=0.1) | 160 | 160 | 0 | 0 | 0 | 0 |
| BDC (w=0.3) | 160 | 160 | 0 | 0 | 0 | 0 |
| BDC (w=0.5) | 160 | 160 | 0 | 0 | 0 | 0 |
| BDC (w=0.7) | 160 | 160 | 0 | 0 | 0 | 0 |
| BDC (w=0.9) | 160 | 160 | 0 | 0 | 0 | 0 |
| BDDC (w=0.1) | 160 | 160 | 0 | 0 | 0 | 0 |
| BDDC (w=0.3) | 160 | 160 | 0 | 0 | 0 | 0 |
| BDDC (w=0.5) | 160 | 160 | 0 | 0 | 0 | 0 |
| BDDC (w=0.7) | 160 | 160 | 0 | 0 | 0 | 0 |
| BDDC (w=0.9) | 160 | 160 | 0 | 0 | 0 | 0 |
| BDHEFT (a=0.1) | 160 | 160 | 0 | 0 | 0 | 0 |
| BDHEFT (a=0.3) | 160 | 160 | 0 | 0 | 0 | 0 |
| BDHEFT (a=0.5) | 160 | 160 | 0 | 0 | 0 | 0 |
| BDHEFT (a=0.7) | 160 | 160 | 0 | 0 | 0 | 0 |
| BDHEFT (a=0.9) | 160 | 160 | 0 | 0 | 0 | 0 |
| DCR-v1 Admission | 160 | 160 | 0 | 0 | 0 | 0 |

## Joint deadline-and-budget feasibility

| Algorithm | Joint feasible | Deadline met | Budget met | Median runtime (ms) | Runtime / BDC (w=0.5) median | p95 | max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **DCR-v1 Admission** | 140/160 (87.5%) | 140/160 (87.5%) | 160/160 (100.0%) | 370 | 0.594x | 1.162x | 1.419x |
| BDC (w=0.5) | 120/160 (75.0%) | 120/160 (75.0%) | 156/160 (97.5%) | 706 | - | - | - |
| BDC (w=0.3) | 113/160 (70.6%) | 113/160 (70.6%) | 160/160 (100.0%) | 1351 | 1.902x | 3.486x | 3.644x |
| BDC (w=0.1) | 102/160 (63.8%) | 102/160 (63.8%) | 160/160 (100.0%) | 1351 | 1.925x | 3.509x | 4.212x |
| BDC (w=0.7) | 97/160 (60.6%) | 117/160 (73.1%) | 126/160 (78.8%) | 1456 | 1.931x | 3.571x | 4.281x |
| BDHEFT (a=0.1) | 92/160 (57.5%) | 93/160 (58.1%) | 157/160 (98.1%) | 885 | 1.303x | 2.675x | 3.097x |
| BDDC (w=0.1) | 84/160 (52.5%) | 114/160 (71.2%) | 126/160 (78.8%) | 1361 | 1.877x | 3.514x | 4.488x |
| BDHEFT (a=0.3) | 80/160 (50.0%) | 87/160 (54.4%) | 146/160 (91.2%) | 886 | 1.309x | 2.681x | 3.111x |
| BDHEFT (a=0.5) | 72/160 (45.0%) | 79/160 (49.4%) | 149/160 (93.1%) | 496 | 0.788x | 0.923x | 0.952x |
| BDHEFT (a=0.7) | 68/160 (42.5%) | 77/160 (48.1%) | 144/160 (90.0%) | 886 | 1.308x | 2.694x | 3.191x |
| BDHEFT (a=0.9) | 68/160 (42.5%) | 75/160 (46.9%) | 150/160 (93.8%) | 885 | 1.240x | 2.622x | 3.162x |
| BDC (w=0.9) | 64/160 (40.0%) | 135/160 (84.4%) | 73/160 (45.6%) | 1452 | 1.916x | 3.542x | 4.933x |
| BDDC (w=0.3) | 60/160 (37.5%) | 131/160 (81.9%) | 78/160 (48.8%) | 1382 | 1.874x | 3.501x | 3.667x |
| BDDC (w=0.5) | 38/160 (23.8%) | 133/160 (83.1%) | 61/160 (38.1%) | 716 | 1.007x | 1.062x | 1.202x |
| BDDC (w=0.7) | 36/160 (22.5%) | 135/160 (84.4%) | 57/160 (35.6%) | 1381 | 1.888x | 3.538x | 5.096x |
| BDDC (w=0.9) | 20/160 (12.5%) | 142/160 (88.8%) | 29/160 (18.1%) | 1373 | 1.881x | 3.583x | 6.405x |

Runtime is policy time only (schedule construction and scoring excluded), median over repetitions; ratios are paired on the same machine and case, p95 is nearest-rank.

## Joint feasibility by workflow family

| Workflow family | cybershake | genome | ligo | montage | sipht |
| --- | ---: | ---: | ---: | ---: | ---: |
| BDC (w=0.1) | 23/32 | 20/32 | 21/32 | 18/32 | 20/32 |
| BDC (w=0.3) | 26/32 | 21/32 | 26/32 | 18/32 | 22/32 |
| BDC (w=0.5) | 25/32 | 22/32 | 28/32 | 22/32 | 23/32 |
| BDC (w=0.7) | 20/32 | 19/32 | 23/32 | 15/32 | 20/32 |
| BDC (w=0.9) | 13/32 | 12/32 | 15/32 | 11/32 | 13/32 |
| BDDC (w=0.1) | 20/32 | 14/32 | 20/32 | 13/32 | 17/32 |
| BDDC (w=0.3) | 10/32 | 7/32 | 13/32 | 11/32 | 19/32 |
| BDDC (w=0.5) | 6/32 | 3/32 | 9/32 | 7/32 | 13/32 |
| BDDC (w=0.7) | 4/32 | 5/32 | 7/32 | 9/32 | 11/32 |
| BDDC (w=0.9) | 2/32 | 2/32 | 5/32 | 8/32 | 3/32 |
| BDHEFT (a=0.1) | 15/32 | 17/32 | 21/32 | 17/32 | 22/32 |
| BDHEFT (a=0.3) | 12/32 | 15/32 | 17/32 | 20/32 | 16/32 |
| BDHEFT (a=0.5) | 11/32 | 14/32 | 16/32 | 16/32 | 15/32 |
| BDHEFT (a=0.7) | 12/32 | 14/32 | 15/32 | 13/32 | 14/32 |
| BDHEFT (a=0.9) | 11/32 | 12/32 | 17/32 | 14/32 | 14/32 |
| DCR-v1 Admission | 27/32 | 29/32 | 31/32 | 25/32 | 28/32 |

## Joint feasibility by number of tasks

| Number of tasks | 60 | 100 | 200 | 400 | 600 | 800 | 1000 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| BDC (w=0.1) | 13/23 | 15/24 | 14/23 | 15/24 | 17/22 | 13/22 | 15/22 |
| BDC (w=0.3) | 16/23 | 15/24 | 14/23 | 18/24 | 18/22 | 14/22 | 18/22 |
| BDC (w=0.5) | 16/23 | 17/24 | 14/23 | 18/24 | 21/22 | 16/22 | 18/22 |
| BDC (w=0.7) | 14/23 | 15/24 | 13/23 | 15/24 | 13/22 | 14/22 | 13/22 |
| BDC (w=0.9) | 8/23 | 9/24 | 7/23 | 9/24 | 10/22 | 10/22 | 11/22 |
| BDDC (w=0.1) | 11/23 | 13/24 | 11/23 | 16/24 | 11/22 | 11/22 | 11/22 |
| BDDC (w=0.3) | 13/23 | 9/24 | 9/23 | 10/24 | 6/22 | 4/22 | 9/22 |
| BDDC (w=0.5) | 10/23 | 9/24 | 3/23 | 5/24 | 4/22 | 3/22 | 4/22 |
| BDDC (w=0.7) | 6/23 | 7/24 | 2/23 | 4/24 | 6/22 | 6/22 | 5/22 |
| BDDC (w=0.9) | 3/23 | 4/24 | 1/23 | 1/24 | 3/22 | 3/22 | 5/22 |
| BDHEFT (a=0.1) | 17/23 | 14/24 | 11/23 | 13/24 | 12/22 | 13/22 | 12/22 |
| BDHEFT (a=0.3) | 13/23 | 13/24 | 10/23 | 10/24 | 10/22 | 12/22 | 12/22 |
| BDHEFT (a=0.5) | 11/23 | 12/24 | 9/23 | 9/24 | 9/22 | 11/22 | 11/22 |
| BDHEFT (a=0.7) | 11/23 | 12/24 | 9/23 | 9/24 | 8/22 | 11/22 | 8/22 |
| BDHEFT (a=0.9) | 11/23 | 11/24 | 8/23 | 10/24 | 8/22 | 11/22 | 9/22 |
| DCR-v1 Admission | 22/23 | 23/24 | 18/23 | 21/24 | 19/22 | 18/22 | 19/22 |

## Joint feasibility by qos tightness

| QoS tightness | relaxed | moderate | tight |
| --- | ---: | ---: | ---: |
| BDC (w=0.1) | 53/54 | 47/52 | 2/54 |
| BDC (w=0.3) | 54/54 | 48/52 | 11/54 |
| BDC (w=0.5) | 54/54 | 45/52 | 21/54 |
| BDC (w=0.7) | 54/54 | 23/52 | 20/54 |
| BDC (w=0.9) | 53/54 | 0/52 | 11/54 |
| BDDC (w=0.1) | 53/54 | 21/52 | 10/54 |
| BDDC (w=0.3) | 45/54 | 10/52 | 5/54 |
| BDDC (w=0.5) | 30/54 | 3/52 | 5/54 |
| BDDC (w=0.7) | 15/54 | 0/52 | 21/54 |
| BDDC (w=0.9) | 4/54 | 0/52 | 16/54 |
| BDHEFT (a=0.1) | 53/54 | 18/52 | 21/54 |
| BDHEFT (a=0.3) | 51/54 | 5/52 | 24/54 |
| BDHEFT (a=0.5) | 51/54 | 4/52 | 17/54 |
| BDHEFT (a=0.7) | 50/54 | 4/52 | 14/54 |
| BDHEFT (a=0.9) | 50/54 | 5/52 | 13/54 |
| DCR-v1 Admission | 54/54 | 47/52 | 39/54 |

## Joint feasibility by scenario

| Scenario | balanced | compute_constrained | network_constrained |
| --- | ---: | ---: | ---: |
| BDC (w=0.1) | 32/53 | 35/54 | 35/53 |
| BDC (w=0.3) | 36/53 | 39/54 | 38/53 |
| BDC (w=0.5) | 38/53 | 41/54 | 41/53 |
| BDC (w=0.7) | 31/53 | 31/54 | 35/53 |
| BDC (w=0.9) | 22/53 | 21/54 | 21/53 |
| BDDC (w=0.1) | 22/53 | 33/54 | 29/53 |
| BDDC (w=0.3) | 19/53 | 21/54 | 20/53 |
| BDDC (w=0.5) | 14/53 | 10/54 | 14/53 |
| BDDC (w=0.7) | 13/53 | 7/54 | 16/53 |
| BDDC (w=0.9) | 6/53 | 6/54 | 8/53 |
| BDHEFT (a=0.1) | 30/53 | 28/54 | 34/53 |
| BDHEFT (a=0.3) | 28/53 | 24/54 | 28/53 |
| BDHEFT (a=0.5) | 26/53 | 22/54 | 24/53 |
| BDHEFT (a=0.7) | 25/53 | 21/54 | 22/53 |
| BDHEFT (a=0.9) | 25/53 | 21/54 | 22/53 |
| DCR-v1 Admission | 46/53 | 46/54 | 48/53 |

## Joint feasibility by resource scale

| Resource scale | S01 | S02 | S03 |
| --- | ---: | ---: | ---: |
| BDC (w=0.1) | 36/54 | 37/52 | 29/54 |
| BDC (w=0.3) | 40/54 | 41/52 | 32/54 |
| BDC (w=0.5) | 47/54 | 42/52 | 31/54 |
| BDC (w=0.7) | 38/54 | 36/52 | 23/54 |
| BDC (w=0.9) | 25/54 | 21/52 | 18/54 |
| BDDC (w=0.1) | 29/54 | 33/52 | 22/54 |
| BDDC (w=0.3) | 22/54 | 26/52 | 12/54 |
| BDDC (w=0.5) | 15/54 | 18/52 | 5/54 |
| BDDC (w=0.7) | 18/54 | 12/52 | 6/54 |
| BDDC (w=0.9) | 13/54 | 6/52 | 1/54 |
| BDHEFT (a=0.1) | 32/54 | 33/52 | 27/54 |
| BDHEFT (a=0.3) | 29/54 | 24/52 | 27/54 |
| BDHEFT (a=0.5) | 28/54 | 22/52 | 22/54 |
| BDHEFT (a=0.7) | 25/54 | 22/52 | 21/54 |
| BDHEFT (a=0.9) | 24/54 | 24/52 | 20/54 |
| DCR-v1 Admission | 49/54 | 44/52 | 47/54 |

## DCR-v1 Admission against each algorithm

| Against | Cases only DCR-v1 Admission is feasible | Cases only the other is feasible | Both feasible | Makespan ratio (median) | Cost ratio (median) | Energy ratio (median) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BDC (w=0.1) | 42 | 4 | 98 | 0.527 | 1.762 | 0.772 |
| BDC (w=0.3) | 30 | 3 | 110 | 0.733 | 1.119 | 0.910 |
| BDC (w=0.5) | 24 | 4 | 116 | 0.851 | 1.006 | 0.952 |
| BDC (w=0.7) | 45 | 2 | 95 | 0.903 | 0.974 | 0.991 |
| BDC (w=0.9) | 77 | 1 | 63 | 0.988 | 0.913 | 1.038 |
| BDDC (w=0.1) | 59 | 3 | 81 | 0.459 | 1.946 | 0.765 |
| BDDC (w=0.3) | 80 | 0 | 60 | 0.642 | 1.217 | 0.863 |
| BDDC (w=0.5) | 103 | 1 | 37 | 0.925 | 0.934 | 0.992 |
| BDDC (w=0.7) | 105 | 1 | 35 | 0.977 | 1.000 | 0.996 |
| BDDC (w=0.9) | 121 | 1 | 19 | 0.997 | 0.999 | 1.000 |
| BDHEFT (a=0.1) | 50 | 2 | 90 | 0.957 | 0.969 | 0.998 |
| BDHEFT (a=0.3) | 62 | 2 | 78 | 1.012 | 0.937 | 1.010 |
| BDHEFT (a=0.5) | 68 | 0 | 72 | 1.004 | 0.935 | 1.009 |
| BDHEFT (a=0.7) | 72 | 0 | 68 | 0.994 | 0.933 | 1.014 |
| BDHEFT (a=0.9) | 72 | 0 | 68 | 0.980 | 0.933 | 1.018 |

Ratios are DCR-v1 Admission / other on cases where both are jointly feasible; below 1 favours DCR-v1 Admission. Energy = compute + network energy.

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

