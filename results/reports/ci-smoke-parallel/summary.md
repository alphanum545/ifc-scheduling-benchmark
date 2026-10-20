# Report: ci-smoke-parallel

Instance set: **dev**. Algorithms: BDC (w=0.5), DCR-v1 Admission. Highlight: DCR-v1 Admission. Cases: 5 selected, **5 compared** (every selected algorithm valid, and deterministic where checked).

Determinism was not re-observed for 10 one-repetition runs; the replay check against the historical results covers it.

## Validity

| Algorithm | Runs | Valid + deterministic | Errors | Invalid | Nondeterministic | Missing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BDC (w=0.5) | 5 | 5 | 0 | 0 | 0 | 0 |
| DCR-v1 Admission | 5 | 5 | 0 | 0 | 0 | 0 |

## Joint deadline-and-budget feasibility

| Algorithm | Joint feasible | Deadline met | Budget met | Median runtime (ms) | Runtime / BDC (w=0.5) median | p95 | max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| BDC (w=0.5) | 5/5 (100.0%) | 5/5 (100.0%) | 5/5 (100.0%) | 1340 | - | - | - |
| **DCR-v1 Admission** | 4/5 (80.0%) | 4/5 (80.0%) | 5/5 (100.0%) | 566 | 0.422x | 0.820x | 0.820x |

Runtime is policy time only (schedule construction and scoring excluded), median over repetitions; ratios are paired on the same machine and case, p95 is nearest-rank.

## Joint feasibility by workflow family

| Workflow family | cybershake | genome | ligo | montage | sipht |
| --- | ---: | ---: | ---: | ---: | ---: |
| BDC (w=0.5) | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 |
| DCR-v1 Admission | 1/1 | 1/1 | 1/1 | 1/1 | 0/1 |

## Joint feasibility by number of tasks

| Number of tasks | 60 | 100 | 400 | 600 | 1000 |
| --- | ---: | ---: | ---: | ---: | ---: |
| BDC (w=0.5) | 1/1 | 1/1 | 1/1 | 1/1 | 1/1 |
| DCR-v1 Admission | 1/1 | 1/1 | 1/1 | 0/1 | 1/1 |

## Joint feasibility by qos tightness

| QoS tightness | relaxed | moderate | tight |
| --- | ---: | ---: | ---: |
| BDC (w=0.5) | 2/2 | 1/1 | 2/2 |
| DCR-v1 Admission | 2/2 | 1/1 | 1/2 |

## Joint feasibility by scenario

| Scenario | balanced | compute_constrained | network_constrained |
| --- | ---: | ---: | ---: |
| BDC (w=0.5) | 1/1 | 2/2 | 2/2 |
| DCR-v1 Admission | 0/1 | 2/2 | 2/2 |

## Joint feasibility by resource scale

| Resource scale | S01 | S02 | S03 |
| --- | ---: | ---: | ---: |
| BDC (w=0.5) | 1/1 | 2/2 | 2/2 |
| DCR-v1 Admission | 1/1 | 1/2 | 2/2 |

## DCR-v1 Admission against each algorithm

| Against | Cases only DCR-v1 Admission is feasible | Cases only the other is feasible | Both feasible | Makespan ratio (median) | Cost ratio (median) | Energy ratio (median) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BDC (w=0.5) | 0 | 1 | 4 | 0.854 | 1.020 | 0.942 |

Ratios are DCR-v1 Admission / other on cases where both are jointly feasible; below 1 favours DCR-v1 Admission. Energy = compute + network energy.

## Replay against the historical results

| Algorithm | Reference set | Instances compared | Exact matches | Mismatches |
| --- | --- | ---: | ---: | ---: |
| HEFT-IFC | `primary:deterministic_heft_ifc` | 160 | 160 | 0 |
| PEFT-IFC | `primary:deterministic_peft_ifc` | 160 | 160 | 0 |
| BDHEFT (a=0.5) | `primary:bdheft_ifc_a05` | 160 | 160 | 0 |
| DBCS | `primary:dbcs_ifc` | 160 | 160 | 0 |
| BDSD | `primary:bdsd_ifc` | 160 | 160 | 0 |
| BDDC (w=0.5) | `primary:bddc_ifc_w05` | 160 | 160 | 0 |
| BDC (w=0.5) | `primary:bdc_ifc_w05` | 160 | 160 | 0 |
| BDC (w=0.5) | `dcr:bdc_ifc_w05` | 160 | 160 | 0 |
| DCR-v0 | `dcr:dcr_ifc_v0` | 160 | 160 | 0 |
| DCR-v0 | `dcr:dcr_ifc_v0@dev-run` | 160 | 160 | 0 |
| DCR-v0 (optimized) | `dcr:dcr_ifc_v0_optimized` | 160 | 160 | 0 |
| DCR-v1 (full ranking) | `dcr:dcr_ifc_v1_arrival` | 160 | 160 | 0 |
| DCR-v1 Admission | `dcr:dcr_ifc_v1_arrival_admission` | 160 | 160 | 0 |
| DCR-v1 Admission | `core24:dcr-v1-admission` | 24 | 24 | 0 |
| DCR-v3 Rescue | `core24:dcr-v3-rescue` | 24 | 24 | 0 |
**Total mismatches: 0.** Every compared run reproduces its historical result exactly.

