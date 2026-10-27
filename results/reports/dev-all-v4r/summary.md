# Report: dev-all-v4r

Instance set: **dev**. Algorithms: HEFT-IFC, PEFT-IFC, BDHEFT (a=0.5), DBCS, BDSD, BDDC (w=0.5), BDC (w=0.5), BDCWS, DCR-v0, DCR-v0 (optimized), DCR-v1 (full ranking), DCR-v1 Admission, DCR-v3 Rescue, DCR-v4 (reserve + quality ranking), DCR-v4R (v4 + v3 rescue). Highlight: DCR-v4R (v4 + v3 rescue). Cases: 160 selected, **160 compared** (every selected algorithm valid, and deterministic where checked).

Determinism was not re-observed for 160 one-repetition runs; the replay check against the historical results covers it.

## Validity

| Algorithm | Runs | Valid + deterministic | Errors | Invalid | Nondeterministic | Missing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| HEFT-IFC | 160 | 160 | 0 | 0 | 0 | 0 |
| PEFT-IFC | 160 | 160 | 0 | 0 | 0 | 0 |
| BDHEFT (a=0.5) | 160 | 160 | 0 | 0 | 0 | 0 |
| DBCS | 160 | 160 | 0 | 0 | 0 | 0 |
| BDSD | 160 | 160 | 0 | 0 | 0 | 0 |
| BDDC (w=0.5) | 160 | 160 | 0 | 0 | 0 | 0 |
| BDC (w=0.5) | 160 | 160 | 0 | 0 | 0 | 0 |
| BDCWS | 160 | 160 | 0 | 0 | 0 | 0 |
| DCR-v0 | 160 | 160 | 0 | 0 | 0 | 0 |
| DCR-v0 (optimized) | 160 | 160 | 0 | 0 | 0 | 0 |
| DCR-v1 (full ranking) | 160 | 160 | 0 | 0 | 0 | 0 |
| DCR-v1 Admission | 160 | 160 | 0 | 0 | 0 | 0 |
| DCR-v3 Rescue | 160 | 160 | 0 | 0 | 0 | 0 |
| DCR-v4 (reserve + quality ranking) | 160 | 160 | 0 | 0 | 0 | 0 |
| DCR-v4R (v4 + v3 rescue) | 160 | 160 | 0 | 0 | 0 | 0 |

## Joint deadline-and-budget feasibility

| Algorithm | Joint feasible | Deadline met | Budget met | Median runtime (ms) | Runtime / BDC (w=0.5) median | p95 | max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **DCR-v4R (v4 + v3 rescue)** | 159/160 (99.4%) | 159/160 (99.4%) | 160/160 (100.0%) | 827 | 1.031x | 3.321x | 9.030x |
| DCR-v3 Rescue | 157/160 (98.1%) | 157/160 (98.1%) | 160/160 (100.0%) | 537 | 0.686x | 2.950x | 8.554x |
| DCR-v4 (reserve + quality ranking) | 148/160 (92.5%) | 148/160 (92.5%) | 160/160 (100.0%) | 422 | 0.588x | 1.211x | 1.407x |
| DCR-v1 Admission | 140/160 (87.5%) | 140/160 (87.5%) | 160/160 (100.0%) | 399 | 0.568x | 1.209x | 1.371x |
| DCR-v0 | 139/160 (86.9%) | 139/160 (86.9%) | 160/160 (100.0%) | 751 | 1.009x | 3.232x | 4.178x |
| DCR-v0 (optimized) | 139/160 (86.9%) | 139/160 (86.9%) | 160/160 (100.0%) | 337 | 0.480x | 1.071x | 1.269x |
| DCR-v1 (full ranking) | 139/160 (86.9%) | 139/160 (86.9%) | 160/160 (100.0%) | 400 | 0.573x | 1.203x | 1.373x |
| BDC (w=0.5) | 120/160 (75.0%) | 120/160 (75.0%) | 156/160 (97.5%) | 697 | - | - | - |
| BDCWS | 119/160 (74.4%) | 119/160 (74.4%) | 160/160 (100.0%) | 559 | 0.880x | 0.965x | 0.991x |
| BDSD | 94/160 (58.8%) | 94/160 (58.8%) | 160/160 (100.0%) | 501 | 0.794x | 0.931x | 0.960x |
| DBCS | 76/160 (47.5%) | 76/160 (47.5%) | 160/160 (100.0%) | 570 | 0.858x | 0.956x | 0.982x |
| BDHEFT (a=0.5) | 72/160 (45.0%) | 79/160 (49.4%) | 149/160 (93.1%) | 500 | 0.791x | 0.925x | 0.955x |
| BDDC (w=0.5) | 38/160 (23.8%) | 133/160 (83.1%) | 61/160 (38.1%) | 712 | 1.009x | 1.058x | 1.207x |
| HEFT-IFC | 8/160 (5.0%) | 160/160 (100.0%) | 8/160 (5.0%) | 487 | 0.766x | 0.917x | 0.963x |
| PEFT-IFC | 1/160 (0.6%) | 151/160 (94.4%) | 4/160 (2.5%) | 327 | 0.496x | 0.560x | 0.588x |

Runtime is policy time only (schedule construction and scoring excluded), median over repetitions; ratios are paired on the same machine and case, p95 is nearest-rank.

## Joint feasibility by workflow family

| Workflow family | cybershake | genome | ligo | montage | sipht |
| --- | ---: | ---: | ---: | ---: | ---: |
| HEFT-IFC | 0/32 | 1/32 | 5/32 | 1/32 | 1/32 |
| PEFT-IFC | 0/32 | 0/32 | 1/32 | 0/32 | 0/32 |
| BDHEFT (a=0.5) | 11/32 | 14/32 | 16/32 | 16/32 | 15/32 |
| DBCS | 13/32 | 16/32 | 17/32 | 14/32 | 16/32 |
| BDSD | 21/32 | 21/32 | 20/32 | 21/32 | 11/32 |
| BDDC (w=0.5) | 6/32 | 3/32 | 9/32 | 7/32 | 13/32 |
| BDC (w=0.5) | 25/32 | 22/32 | 28/32 | 22/32 | 23/32 |
| BDCWS | 23/32 | 26/32 | 21/32 | 26/32 | 23/32 |
| DCR-v0 | 27/32 | 29/32 | 31/32 | 24/32 | 28/32 |
| DCR-v0 (optimized) | 27/32 | 29/32 | 31/32 | 24/32 | 28/32 |
| DCR-v1 (full ranking) | 27/32 | 29/32 | 31/32 | 24/32 | 28/32 |
| DCR-v1 Admission | 27/32 | 29/32 | 31/32 | 25/32 | 28/32 |
| DCR-v3 Rescue | 31/32 | 32/32 | 32/32 | 32/32 | 30/32 |
| DCR-v4 (reserve + quality ranking) | 31/32 | 31/32 | 31/32 | 26/32 | 29/32 |
| DCR-v4R (v4 + v3 rescue) | 32/32 | 32/32 | 32/32 | 32/32 | 31/32 |

## Joint feasibility by number of tasks

| Number of tasks | 60 | 100 | 200 | 400 | 600 | 800 | 1000 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| HEFT-IFC | 0/23 | 1/24 | 1/23 | 3/24 | 0/22 | 1/22 | 2/22 |
| PEFT-IFC | 0/23 | 0/24 | 0/23 | 0/24 | 0/22 | 1/22 | 0/22 |
| BDHEFT (a=0.5) | 11/23 | 12/24 | 9/23 | 9/24 | 9/22 | 11/22 | 11/22 |
| DBCS | 10/23 | 12/24 | 9/23 | 13/24 | 10/22 | 11/22 | 11/22 |
| BDSD | 14/23 | 14/24 | 12/23 | 14/24 | 14/22 | 13/22 | 13/22 |
| BDDC (w=0.5) | 10/23 | 9/24 | 3/23 | 5/24 | 4/22 | 3/22 | 4/22 |
| BDC (w=0.5) | 16/23 | 17/24 | 14/23 | 18/24 | 21/22 | 16/22 | 18/22 |
| BDCWS | 19/23 | 19/24 | 17/23 | 19/24 | 16/22 | 14/22 | 15/22 |
| DCR-v0 | 22/23 | 22/24 | 18/23 | 21/24 | 19/22 | 18/22 | 19/22 |
| DCR-v0 (optimized) | 22/23 | 22/24 | 18/23 | 21/24 | 19/22 | 18/22 | 19/22 |
| DCR-v1 (full ranking) | 22/23 | 22/24 | 18/23 | 21/24 | 19/22 | 18/22 | 19/22 |
| DCR-v1 Admission | 22/23 | 23/24 | 18/23 | 21/24 | 19/22 | 18/22 | 19/22 |
| DCR-v3 Rescue | 23/23 | 23/24 | 23/23 | 23/24 | 21/22 | 22/22 | 22/22 |
| DCR-v4 (reserve + quality ranking) | 23/23 | 24/24 | 20/23 | 22/24 | 21/22 | 18/22 | 20/22 |
| DCR-v4R (v4 + v3 rescue) | 23/23 | 24/24 | 23/23 | 23/24 | 22/22 | 22/22 | 22/22 |

## Joint feasibility by qos tightness

| QoS tightness | relaxed | moderate | tight |
| --- | ---: | ---: | ---: |
| HEFT-IFC | 0/54 | 0/52 | 8/54 |
| PEFT-IFC | 0/54 | 0/52 | 1/54 |
| BDHEFT (a=0.5) | 51/54 | 4/52 | 17/54 |
| DBCS | 54/54 | 1/52 | 21/54 |
| BDSD | 53/54 | 40/52 | 1/54 |
| BDDC (w=0.5) | 30/54 | 3/52 | 5/54 |
| BDC (w=0.5) | 54/54 | 45/52 | 21/54 |
| BDCWS | 54/54 | 52/52 | 13/54 |
| DCR-v0 | 54/54 | 47/52 | 38/54 |
| DCR-v0 (optimized) | 54/54 | 47/52 | 38/54 |
| DCR-v1 (full ranking) | 54/54 | 47/52 | 38/54 |
| DCR-v1 Admission | 54/54 | 47/52 | 39/54 |
| DCR-v3 Rescue | 54/54 | 52/52 | 51/54 |
| DCR-v4 (reserve + quality ranking) | 54/54 | 48/52 | 46/54 |
| DCR-v4R (v4 + v3 rescue) | 54/54 | 52/52 | 53/54 |

## Joint feasibility by scenario

| Scenario | balanced | compute_constrained | network_constrained |
| --- | ---: | ---: | ---: |
| HEFT-IFC | 1/53 | 3/54 | 4/53 |
| PEFT-IFC | 0/53 | 0/54 | 1/53 |
| BDHEFT (a=0.5) | 26/53 | 22/54 | 24/53 |
| DBCS | 26/53 | 25/54 | 25/53 |
| BDSD | 31/53 | 30/54 | 33/53 |
| BDDC (w=0.5) | 14/53 | 10/54 | 14/53 |
| BDC (w=0.5) | 38/53 | 41/54 | 41/53 |
| BDCWS | 40/53 | 39/54 | 40/53 |
| DCR-v0 | 46/53 | 45/54 | 48/53 |
| DCR-v0 (optimized) | 46/53 | 45/54 | 48/53 |
| DCR-v1 (full ranking) | 46/53 | 45/54 | 48/53 |
| DCR-v1 Admission | 46/53 | 46/54 | 48/53 |
| DCR-v3 Rescue | 52/53 | 52/54 | 53/53 |
| DCR-v4 (reserve + quality ranking) | 49/53 | 48/54 | 51/53 |
| DCR-v4R (v4 + v3 rescue) | 53/53 | 53/54 | 53/53 |

## Joint feasibility by resource scale

| Resource scale | S01 | S02 | S03 |
| --- | ---: | ---: | ---: |
| HEFT-IFC | 2/54 | 2/52 | 4/54 |
| PEFT-IFC | 0/54 | 0/52 | 1/54 |
| BDHEFT (a=0.5) | 28/54 | 22/52 | 22/54 |
| DBCS | 27/54 | 21/52 | 28/54 |
| BDSD | 32/54 | 33/52 | 29/54 |
| BDDC (w=0.5) | 15/54 | 18/52 | 5/54 |
| BDC (w=0.5) | 47/54 | 42/52 | 31/54 |
| BDCWS | 39/54 | 41/52 | 39/54 |
| DCR-v0 | 48/54 | 44/52 | 47/54 |
| DCR-v0 (optimized) | 48/54 | 44/52 | 47/54 |
| DCR-v1 (full ranking) | 48/54 | 44/52 | 47/54 |
| DCR-v1 Admission | 49/54 | 44/52 | 47/54 |
| DCR-v3 Rescue | 53/54 | 51/52 | 53/54 |
| DCR-v4 (reserve + quality ranking) | 53/54 | 47/52 | 48/54 |
| DCR-v4R (v4 + v3 rescue) | 54/54 | 52/52 | 53/54 |

## DCR-v4R (v4 + v3 rescue) against each algorithm

| Against | Cases only DCR-v4R (v4 + v3 rescue) is feasible | Cases only the other is feasible | Both feasible | Makespan ratio (median) | Cost ratio (median) | Energy ratio (median) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| HEFT-IFC | 151 | 0 | 8 | 1.081 | 0.975 | 1.024 |
| PEFT-IFC | 158 | 0 | 1 | 1.026 | 0.980 | 1.021 |
| BDHEFT (a=0.5) | 87 | 0 | 72 | 1.074 | 0.919 | 1.077 |
| DBCS | 83 | 0 | 76 | 0.787 | 0.902 | 1.100 |
| BDSD | 65 | 0 | 94 | 1.025 | 1.163 | 0.952 |
| BDDC (w=0.5) | 121 | 0 | 38 | 0.947 | 0.927 | 1.031 |
| BDC (w=0.5) | 39 | 0 | 120 | 0.927 | 1.001 | 0.997 |
| BDCWS | 40 | 0 | 119 | 0.496 | 1.423 | 0.878 |
| DCR-v0 | 20 | 0 | 139 | 1.058 | 0.993 | 1.041 |
| DCR-v0 (optimized) | 20 | 0 | 139 | 1.058 | 0.993 | 1.041 |
| DCR-v1 (full ranking) | 20 | 0 | 139 | 1.054 | 0.992 | 1.040 |
| DCR-v1 Admission | 19 | 0 | 140 | 1.056 | 0.993 | 1.041 |
| DCR-v3 Rescue | 2 | 0 | 157 | 1.049 | 0.995 | 1.036 |
| DCR-v4 (reserve + quality ranking) | 11 | 0 | 148 | 1.000 | 1.000 | 1.000 |

Ratios are DCR-v4R (v4 + v3 rescue) / other on cases where both are jointly feasible; below 1 favours DCR-v4R (v4 + v3 rescue). Energy = compute + network energy.

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

