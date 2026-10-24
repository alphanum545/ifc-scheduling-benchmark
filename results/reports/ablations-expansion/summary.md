# Report: ablations-expansion

Instance set: **expansion**. Algorithms: Ablation: control (= DCR-v1 Admission), Ablation: no priced reserve, Ablation: zero prices, Ablation: time-only ranking, Ablation: budget-only ranking, Ablation: weighted-sum ranking, DCR-v1 Admission, BDC (w=0.5). Highlight: Ablation: control (= DCR-v1 Admission). Cases: 1890 selected, **1890 compared** (every selected algorithm valid, and deterministic where checked).

Determinism was not re-observed for 15120 one-repetition runs; the replay check against the historical results covers it.

## Validity

| Algorithm | Runs | Valid + deterministic | Errors | Invalid | Nondeterministic | Missing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Ablation: control (= DCR-v1 Admission) | 1890 | 1890 | 0 | 0 | 0 | 0 |
| Ablation: no priced reserve | 1890 | 1890 | 0 | 0 | 0 | 0 |
| Ablation: zero prices | 1890 | 1890 | 0 | 0 | 0 | 0 |
| Ablation: time-only ranking | 1890 | 1890 | 0 | 0 | 0 | 0 |
| Ablation: budget-only ranking | 1890 | 1890 | 0 | 0 | 0 | 0 |
| Ablation: weighted-sum ranking | 1890 | 1890 | 0 | 0 | 0 | 0 |
| DCR-v1 Admission | 1890 | 1890 | 0 | 0 | 0 | 0 |
| BDC (w=0.5) | 1890 | 1890 | 0 | 0 | 0 | 0 |

## Joint deadline-and-budget feasibility

| Algorithm | Joint feasible | Deadline met | Budget met | Median runtime (ms) | Runtime / BDC (w=0.5) median | p95 | max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Ablation: weighted-sum ranking | 1659/1890 (87.8%) | 1659/1890 (87.8%) | 1890/1890 (100.0%) | 767 | 0.518x | 1.260x | 2.702x |
| **Ablation: control (= DCR-v1 Admission)** | 1629/1890 (86.2%) | 1629/1890 (86.2%) | 1890/1890 (100.0%) | 757 | 0.508x | 1.218x | 2.606x |
| Ablation: zero prices | 1629/1890 (86.2%) | 1629/1890 (86.2%) | 1890/1890 (100.0%) | 759 | 0.514x | 1.239x | 2.618x |
| DCR-v1 Admission | 1629/1890 (86.2%) | 1629/1890 (86.2%) | 1890/1890 (100.0%) | 766 | 0.515x | 1.110x | 1.337x |
| Ablation: no priced reserve | 1579/1890 (83.5%) | 1579/1890 (83.5%) | 1890/1890 (100.0%) | 407 | 0.260x | 0.811x | 1.963x |
| BDC (w=0.5) | 1427/1890 (75.5%) | 1435/1890 (75.9%) | 1858/1890 (98.3%) | 1368 | - | - | - |
| Ablation: time-only ranking | 984/1890 (52.1%) | 984/1890 (52.1%) | 1890/1890 (100.0%) | 623 | 0.411x | 1.112x | 2.233x |
| Ablation: budget-only ranking | 961/1890 (50.8%) | 961/1890 (50.8%) | 1890/1890 (100.0%) | 606 | 0.406x | 1.126x | 2.757x |

Runtime is policy time only (schedule construction and scoring excluded), median over repetitions; ratios are paired on the same machine and case, p95 is nearest-rank.

## Joint feasibility by workflow family

| Workflow family | cybershake | genome | ligo | montage | sipht |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ablation: control (= DCR-v1 Admission) | 326/378 | 322/378 | 367/378 | 277/378 | 337/378 |
| Ablation: no priced reserve | 326/378 | 313/378 | 367/378 | 272/378 | 301/378 |
| Ablation: zero prices | 326/378 | 322/378 | 367/378 | 277/378 | 337/378 |
| Ablation: time-only ranking | 188/378 | 182/378 | 220/378 | 179/378 | 215/378 |
| Ablation: budget-only ranking | 265/378 | 275/378 | 119/378 | 91/378 | 211/378 |
| Ablation: weighted-sum ranking | 340/378 | 325/378 | 367/378 | 292/378 | 335/378 |
| DCR-v1 Admission | 326/378 | 322/378 | 367/378 | 277/378 | 337/378 |
| BDC (w=0.5) | 309/378 | 276/378 | 314/378 | 262/378 | 266/378 |

## Joint feasibility by number of tasks

| Number of tasks | 60 | 100 | 200 | 400 | 600 | 800 | 1000 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Ablation: control (= DCR-v1 Admission) | 232/270 | 238/270 | 236/270 | 239/270 | 242/270 | 223/270 | 219/270 |
| Ablation: no priced reserve | 211/270 | 221/270 | 233/270 | 240/270 | 236/270 | 220/270 | 218/270 |
| Ablation: zero prices | 232/270 | 238/270 | 236/270 | 239/270 | 242/270 | 223/270 | 219/270 |
| Ablation: time-only ranking | 147/270 | 131/270 | 133/270 | 134/270 | 144/270 | 147/270 | 148/270 |
| Ablation: budget-only ranking | 180/270 | 165/270 | 147/270 | 130/270 | 123/270 | 116/270 | 100/270 |
| Ablation: weighted-sum ranking | 235/270 | 235/270 | 237/270 | 244/270 | 247/270 | 230/270 | 231/270 |
| DCR-v1 Admission | 232/270 | 238/270 | 236/270 | 239/270 | 242/270 | 223/270 | 219/270 |
| BDC (w=0.5) | 169/270 | 175/270 | 196/270 | 216/270 | 228/270 | 223/270 | 220/270 |

## Joint feasibility by qos tightness

| QoS tightness | relaxed | moderate | tight |
| --- | ---: | ---: | ---: |
| Ablation: control (= DCR-v1 Admission) | 630/630 | 554/630 | 445/630 |
| Ablation: no priced reserve | 630/630 | 551/630 | 398/630 |
| Ablation: zero prices | 630/630 | 554/630 | 445/630 |
| Ablation: time-only ranking | 630/630 | 18/630 | 336/630 |
| Ablation: budget-only ranking | 552/630 | 298/630 | 111/630 |
| Ablation: weighted-sum ranking | 630/630 | 582/630 | 447/630 |
| DCR-v1 Admission | 630/630 | 554/630 | 445/630 |
| BDC (w=0.5) | 630/630 | 556/630 | 241/630 |

## Joint feasibility by scenario

| Scenario | balanced | compute_constrained | network_constrained |
| --- | ---: | ---: | ---: |
| Ablation: control (= DCR-v1 Admission) | 550/630 | 539/630 | 540/630 |
| Ablation: no priced reserve | 531/630 | 522/630 | 526/630 |
| Ablation: zero prices | 550/630 | 539/630 | 540/630 |
| Ablation: time-only ranking | 329/630 | 329/630 | 326/630 |
| Ablation: budget-only ranking | 332/630 | 305/630 | 324/630 |
| Ablation: weighted-sum ranking | 554/630 | 556/630 | 549/630 |
| DCR-v1 Admission | 550/630 | 539/630 | 540/630 |
| BDC (w=0.5) | 478/630 | 471/630 | 478/630 |

## Joint feasibility by resource scale

| Resource scale | S01 | S02 | S03 |
| --- | ---: | ---: | ---: |
| Ablation: control (= DCR-v1 Admission) | 566/630 | 528/630 | 535/630 |
| Ablation: no priced reserve | 561/630 | 514/630 | 504/630 |
| Ablation: zero prices | 566/630 | 528/630 | 535/630 |
| Ablation: time-only ranking | 334/630 | 286/630 | 364/630 |
| Ablation: budget-only ranking | 310/630 | 345/630 | 306/630 |
| Ablation: weighted-sum ranking | 569/630 | 541/630 | 549/630 |
| DCR-v1 Admission | 566/630 | 528/630 | 535/630 |
| BDC (w=0.5) | 525/630 | 490/630 | 412/630 |

## Ablation: control (= DCR-v1 Admission) against each algorithm

| Against | Cases only Ablation: control (= DCR-v1 Admission) is feasible | Cases only the other is feasible | Both feasible | Makespan ratio (median) | Cost ratio (median) | Energy ratio (median) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Ablation: no priced reserve | 53 | 3 | 1576 | 1.000 | 1.000 | 1.000 |
| Ablation: zero prices | 0 | 0 | 1629 | 1.000 | 1.000 | 1.000 |
| Ablation: time-only ranking | 648 | 3 | 981 | 0.789 | 0.941 | 1.025 |
| Ablation: budget-only ranking | 727 | 59 | 902 | 0.153 | 7.184 | 0.678 |
| Ablation: weighted-sum ranking | 17 | 47 | 1612 | 0.982 | 1.001 | 0.970 |
| DCR-v1 Admission | 0 | 0 | 1629 | 1.000 | 1.000 | 1.000 |
| BDC (w=0.5) | 255 | 53 | 1374 | 0.844 | 1.010 | 0.959 |

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

