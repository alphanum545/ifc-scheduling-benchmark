# Report: ablation-scoring-dev

Instance set: **dev**. Algorithms: Ablation: scoring control (= DCR-v1 Admission), Ablation: BDC-style quality ranking. Highlight: Ablation: scoring control (= DCR-v1 Admission). Cases: 160 selected, **160 compared** (every selected algorithm valid, and deterministic where checked).

Determinism was not re-observed for 320 one-repetition runs; the replay check against the historical results covers it.

## Validity

| Algorithm | Runs | Valid + deterministic | Errors | Invalid | Nondeterministic | Missing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Ablation: scoring control (= DCR-v1 Admission) | 160 | 160 | 0 | 0 | 0 | 0 |
| Ablation: BDC-style quality ranking | 160 | 160 | 0 | 0 | 0 | 0 |

## Joint deadline-and-budget feasibility

| Algorithm | Joint feasible | Deadline met | Budget met | Median runtime (ms) | Runtime / - median | p95 | max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Ablation: BDC-style quality ranking | 148/160 (92.5%) | 148/160 (92.5%) | 160/160 (100.0%) | 652 | - | - | - |
| **Ablation: scoring control (= DCR-v1 Admission)** | 140/160 (87.5%) | 140/160 (87.5%) | 160/160 (100.0%) | 627 | - | - | - |

Runtime is policy time only (schedule construction and scoring excluded), median over repetitions; ratios are paired on the same machine and case, p95 is nearest-rank.

## Joint feasibility by workflow family

| Workflow family | cybershake | genome | ligo | montage | sipht |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ablation: scoring control (= DCR-v1 Admission) | 27/32 | 29/32 | 31/32 | 25/32 | 28/32 |
| Ablation: BDC-style quality ranking | 31/32 | 31/32 | 31/32 | 26/32 | 29/32 |

## Joint feasibility by number of tasks

| Number of tasks | 60 | 100 | 200 | 400 | 600 | 800 | 1000 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Ablation: scoring control (= DCR-v1 Admission) | 22/23 | 23/24 | 18/23 | 21/24 | 19/22 | 18/22 | 19/22 |
| Ablation: BDC-style quality ranking | 23/23 | 24/24 | 20/23 | 22/24 | 21/22 | 18/22 | 20/22 |

## Joint feasibility by qos tightness

| QoS tightness | relaxed | moderate | tight |
| --- | ---: | ---: | ---: |
| Ablation: scoring control (= DCR-v1 Admission) | 54/54 | 47/52 | 39/54 |
| Ablation: BDC-style quality ranking | 54/54 | 48/52 | 46/54 |

## Joint feasibility by scenario

| Scenario | balanced | compute_constrained | network_constrained |
| --- | ---: | ---: | ---: |
| Ablation: scoring control (= DCR-v1 Admission) | 46/53 | 46/54 | 48/53 |
| Ablation: BDC-style quality ranking | 49/53 | 48/54 | 51/53 |

## Joint feasibility by resource scale

| Resource scale | S01 | S02 | S03 |
| --- | ---: | ---: | ---: |
| Ablation: scoring control (= DCR-v1 Admission) | 49/54 | 44/52 | 47/54 |
| Ablation: BDC-style quality ranking | 53/54 | 47/52 | 48/54 |

## Ablation: scoring control (= DCR-v1 Admission) against each algorithm

| Against | Cases only Ablation: scoring control (= DCR-v1 Admission) is feasible | Cases only the other is feasible | Both feasible | Makespan ratio (median) | Cost ratio (median) | Energy ratio (median) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Ablation: BDC-style quality ranking | 0 | 8 | 140 | 0.947 | 1.007 | 0.961 |

Ratios are Ablation: scoring control (= DCR-v1 Admission) / other on cases where both are jointly feasible; below 1 favours Ablation: scoring control (= DCR-v1 Admission). Energy = compute + network energy.

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

