# Report: ablation-scoring-expansion

Instance set: **expansion**. Algorithms: Ablation: scoring control (= DCR-v1 Admission), Ablation: BDC-style quality ranking. Highlight: Ablation: scoring control (= DCR-v1 Admission). Cases: 1890 selected, **1890 compared** (every selected algorithm valid, and deterministic where checked).

Determinism was not re-observed for 3780 one-repetition runs; the replay check against the historical results covers it.

## Validity

| Algorithm | Runs | Valid + deterministic | Errors | Invalid | Nondeterministic | Missing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Ablation: scoring control (= DCR-v1 Admission) | 1890 | 1890 | 0 | 0 | 0 | 0 |
| Ablation: BDC-style quality ranking | 1890 | 1890 | 0 | 0 | 0 | 0 |

## Joint deadline-and-budget feasibility

| Algorithm | Joint feasible | Deadline met | Budget met | Median runtime (ms) | Runtime / - median | p95 | max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Ablation: BDC-style quality ranking | 1732/1890 (91.6%) | 1732/1890 (91.6%) | 1890/1890 (100.0%) | 734 | - | - | - |
| **Ablation: scoring control (= DCR-v1 Admission)** | 1629/1890 (86.2%) | 1629/1890 (86.2%) | 1890/1890 (100.0%) | 707 | - | - | - |

Runtime is policy time only (schedule construction and scoring excluded), median over repetitions; ratios are paired on the same machine and case, p95 is nearest-rank.

## Joint feasibility by workflow family

| Workflow family | cybershake | genome | ligo | montage | sipht |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ablation: scoring control (= DCR-v1 Admission) | 326/378 | 322/378 | 367/378 | 277/378 | 337/378 |
| Ablation: BDC-style quality ranking | 355/378 | 340/378 | 375/378 | 319/378 | 343/378 |

## Joint feasibility by number of tasks

| Number of tasks | 60 | 100 | 200 | 400 | 600 | 800 | 1000 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Ablation: scoring control (= DCR-v1 Admission) | 232/270 | 238/270 | 236/270 | 239/270 | 242/270 | 223/270 | 219/270 |
| Ablation: BDC-style quality ranking | 240/270 | 248/270 | 244/270 | 251/270 | 258/270 | 250/270 | 241/270 |

## Joint feasibility by qos tightness

| QoS tightness | relaxed | moderate | tight |
| --- | ---: | ---: | ---: |
| Ablation: scoring control (= DCR-v1 Admission) | 630/630 | 554/630 | 445/630 |
| Ablation: BDC-style quality ranking | 630/630 | 590/630 | 512/630 |

## Joint feasibility by scenario

| Scenario | balanced | compute_constrained | network_constrained |
| --- | ---: | ---: | ---: |
| Ablation: scoring control (= DCR-v1 Admission) | 550/630 | 539/630 | 540/630 |
| Ablation: BDC-style quality ranking | 580/630 | 579/630 | 573/630 |

## Joint feasibility by resource scale

| Resource scale | S01 | S02 | S03 |
| --- | ---: | ---: | ---: |
| Ablation: scoring control (= DCR-v1 Admission) | 566/630 | 528/630 | 535/630 |
| Ablation: BDC-style quality ranking | 600/630 | 558/630 | 574/630 |

## Ablation: scoring control (= DCR-v1 Admission) against each algorithm

| Against | Cases only Ablation: scoring control (= DCR-v1 Admission) is feasible | Cases only the other is feasible | Both feasible | Makespan ratio (median) | Cost ratio (median) | Energy ratio (median) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Ablation: BDC-style quality ranking | 10 | 113 | 1619 | 0.945 | 1.008 | 0.964 |

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

