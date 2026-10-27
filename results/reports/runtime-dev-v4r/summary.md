# Report: runtime-dev-v4r

Instance set: **dev**. Algorithms: BDC (w=0.5), DCR-v4 (reserve + quality ranking), DCR-v4R (v4 + v3 rescue), DCR-v3 Rescue. Highlight: DCR-v4R (v4 + v3 rescue). Cases: 160 selected, **160 compared** (every selected algorithm valid, and deterministic where checked).

## Validity

| Algorithm | Runs | Valid + deterministic | Errors | Invalid | Nondeterministic | Missing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BDC (w=0.5) | 160 | 160 | 0 | 0 | 0 | 0 |
| DCR-v4 (reserve + quality ranking) | 160 | 160 | 0 | 0 | 0 | 0 |
| DCR-v4R (v4 + v3 rescue) | 160 | 160 | 0 | 0 | 0 | 0 |
| DCR-v3 Rescue | 160 | 160 | 0 | 0 | 0 | 0 |

## Joint deadline-and-budget feasibility

| Algorithm | Joint feasible | Deadline met | Budget met | Median runtime (ms) | Runtime / BDC (w=0.5) median | p95 | max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **DCR-v4R (v4 + v3 rescue)** | 159/160 (99.4%) | 159/160 (99.4%) | 160/160 (100.0%) | 449 | 0.692x | 2.079x | 7.688x |
| DCR-v3 Rescue | 157/160 (98.1%) | 157/160 (98.1%) | 160/160 (100.0%) | 467 | 0.693x | 2.926x | 8.236x |
| DCR-v4 (reserve + quality ranking) | 148/160 (92.5%) | 148/160 (92.5%) | 160/160 (100.0%) | 421 | 0.620x | 1.192x | 1.389x |
| BDC (w=0.5) | 120/160 (75.0%) | 120/160 (75.0%) | 156/160 (97.5%) | 750 | - | - | - |

Runtime is policy time only (schedule construction and scoring excluded), median over repetitions; ratios are paired on the same machine and case, p95 is nearest-rank.

## Joint feasibility by workflow family

| Workflow family | cybershake | genome | ligo | montage | sipht |
| --- | ---: | ---: | ---: | ---: | ---: |
| BDC (w=0.5) | 25/32 | 22/32 | 28/32 | 22/32 | 23/32 |
| DCR-v4 (reserve + quality ranking) | 31/32 | 31/32 | 31/32 | 26/32 | 29/32 |
| DCR-v4R (v4 + v3 rescue) | 32/32 | 32/32 | 32/32 | 32/32 | 31/32 |
| DCR-v3 Rescue | 31/32 | 32/32 | 32/32 | 32/32 | 30/32 |

## Joint feasibility by number of tasks

| Number of tasks | 60 | 100 | 200 | 400 | 600 | 800 | 1000 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| BDC (w=0.5) | 16/23 | 17/24 | 14/23 | 18/24 | 21/22 | 16/22 | 18/22 |
| DCR-v4 (reserve + quality ranking) | 23/23 | 24/24 | 20/23 | 22/24 | 21/22 | 18/22 | 20/22 |
| DCR-v4R (v4 + v3 rescue) | 23/23 | 24/24 | 23/23 | 23/24 | 22/22 | 22/22 | 22/22 |
| DCR-v3 Rescue | 23/23 | 23/24 | 23/23 | 23/24 | 21/22 | 22/22 | 22/22 |

## Joint feasibility by qos tightness

| QoS tightness | relaxed | moderate | tight |
| --- | ---: | ---: | ---: |
| BDC (w=0.5) | 54/54 | 45/52 | 21/54 |
| DCR-v4 (reserve + quality ranking) | 54/54 | 48/52 | 46/54 |
| DCR-v4R (v4 + v3 rescue) | 54/54 | 52/52 | 53/54 |
| DCR-v3 Rescue | 54/54 | 52/52 | 51/54 |

## Joint feasibility by scenario

| Scenario | balanced | compute_constrained | network_constrained |
| --- | ---: | ---: | ---: |
| BDC (w=0.5) | 38/53 | 41/54 | 41/53 |
| DCR-v4 (reserve + quality ranking) | 49/53 | 48/54 | 51/53 |
| DCR-v4R (v4 + v3 rescue) | 53/53 | 53/54 | 53/53 |
| DCR-v3 Rescue | 52/53 | 52/54 | 53/53 |

## Joint feasibility by resource scale

| Resource scale | S01 | S02 | S03 |
| --- | ---: | ---: | ---: |
| BDC (w=0.5) | 47/54 | 42/52 | 31/54 |
| DCR-v4 (reserve + quality ranking) | 53/54 | 47/52 | 48/54 |
| DCR-v4R (v4 + v3 rescue) | 54/54 | 52/52 | 53/54 |
| DCR-v3 Rescue | 53/54 | 51/52 | 53/54 |

## DCR-v4R (v4 + v3 rescue) against each algorithm

| Against | Cases only DCR-v4R (v4 + v3 rescue) is feasible | Cases only the other is feasible | Both feasible | Makespan ratio (median) | Cost ratio (median) | Energy ratio (median) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BDC (w=0.5) | 39 | 0 | 120 | 0.927 | 1.001 | 0.997 |
| DCR-v4 (reserve + quality ranking) | 11 | 0 | 148 | 1.000 | 1.000 | 1.000 |
| DCR-v3 Rescue | 2 | 0 | 157 | 1.049 | 0.995 | 1.036 |

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

