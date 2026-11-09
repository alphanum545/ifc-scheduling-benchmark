# Report: paper2-expansion-speed

Instance set: **expansion**. Algorithms: DCR-Cost v2 (+ deadline-split candidates), DCR-Cost v1 (portfolio + improvement). Highlight: DCR-Cost v2 (+ deadline-split candidates). Cases: 1890 selected, **1890 compared** (every selected algorithm valid, and deterministic where checked).

Determinism was not re-observed for 3780 one-repetition runs; the replay check against the historical results covers it.

## Validity

| Algorithm | Runs | Valid + deterministic | Errors | Invalid | Nondeterministic | Missing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DCR-Cost v2 (+ deadline-split candidates) | 1890 | 1890 | 0 | 0 | 0 | 0 |
| DCR-Cost v1 (portfolio + improvement) | 1890 | 1890 | 0 | 0 | 0 | 0 |

## Joint deadline-and-budget feasibility

| Algorithm | Joint feasible | Deadline met | Budget met | Median runtime (ms) | Runtime / - median | p95 | max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **DCR-Cost v2 (+ deadline-split candidates)** | 1848/1890 (97.8%) | 1890/1890 (100.0%) | 1848/1890 (97.8%) | 4583 | - | - | - |
| DCR-Cost v1 (portfolio + improvement) | 1790/1890 (94.7%) | 1890/1890 (100.0%) | 1790/1890 (94.7%) | 2259 | - | - | - |

Runtime is policy time only (schedule construction and scoring excluded), median over repetitions; ratios are paired on the same machine and case, p95 is nearest-rank.

## Joint feasibility by workflow family

| Workflow family | cybershake | genome | ligo | montage | sipht |
| --- | ---: | ---: | ---: | ---: | ---: |
| DCR-Cost v2 (+ deadline-split candidates) | 375/378 | 373/378 | 378/378 | 348/378 | 374/378 |
| DCR-Cost v1 (portfolio + improvement) | 372/378 | 371/378 | 345/378 | 339/378 | 363/378 |

## Joint feasibility by number of tasks

| Number of tasks | 60 | 100 | 200 | 400 | 600 | 800 | 1000 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DCR-Cost v2 (+ deadline-split candidates) | 260/270 | 261/270 | 261/270 | 265/270 | 268/270 | 267/270 | 266/270 |
| DCR-Cost v1 (portfolio + improvement) | 257/270 | 257/270 | 259/270 | 254/270 | 259/270 | 251/270 | 253/270 |

## Joint feasibility by qos tightness

| QoS tightness | relaxed | moderate | tight |
| --- | ---: | ---: | ---: |
| DCR-Cost v2 (+ deadline-split candidates) | 630/630 | 630/630 | 588/630 |
| DCR-Cost v1 (portfolio + improvement) | 630/630 | 605/630 | 555/630 |

## Joint feasibility by scenario

| Scenario | balanced | compute_constrained | network_constrained |
| --- | ---: | ---: | ---: |
| DCR-Cost v2 (+ deadline-split candidates) | 622/630 | 611/630 | 615/630 |
| DCR-Cost v1 (portfolio + improvement) | 603/630 | 592/630 | 595/630 |

## Joint feasibility by resource scale

| Resource scale | S01 | S02 | S03 |
| --- | ---: | ---: | ---: |
| DCR-Cost v2 (+ deadline-split candidates) | 621/630 | 620/630 | 607/630 |
| DCR-Cost v1 (portfolio + improvement) | 617/630 | 599/630 | 574/630 |

## DCR-Cost v2 (+ deadline-split candidates) against each algorithm

| Against | Cases only DCR-Cost v2 (+ deadline-split candidates) is feasible | Cases only the other is feasible | Both feasible | Makespan ratio (median) | Cost ratio (median) | Energy ratio (median) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DCR-Cost v1 (portfolio + improvement) | 58 | 0 | 1790 | 1.000 | 0.995 | 1.000 |

Ratios are DCR-Cost v2 (+ deadline-split candidates) / other on cases where both are jointly feasible; below 1 favours DCR-Cost v2 (+ deadline-split candidates). Energy = compute + network energy.

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

