# Report: expansion-all

Instance set: **expansion**. Algorithms: HEFT-IFC, PEFT-IFC, BDHEFT (a=0.5), DBCS, BDSD, BDDC (w=0.5), BDC (w=0.5), DCR-v0, DCR-v0 (optimized), DCR-v1 (full ranking), DCR-v1 Admission, DCR-v3 Rescue. Highlight: DCR-v1 Admission. Cases: 1890 selected, **1890 compared** (every selected algorithm valid, and deterministic where checked).

Determinism was not re-observed for 22680 one-repetition runs; the replay check against the historical results covers it.

## Validity

| Algorithm | Runs | Valid + deterministic | Errors | Invalid | Nondeterministic | Missing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| HEFT-IFC | 1890 | 1890 | 0 | 0 | 0 | 0 |
| PEFT-IFC | 1890 | 1890 | 0 | 0 | 0 | 0 |
| BDHEFT (a=0.5) | 1890 | 1890 | 0 | 0 | 0 | 0 |
| DBCS | 1890 | 1890 | 0 | 0 | 0 | 0 |
| BDSD | 1890 | 1890 | 0 | 0 | 0 | 0 |
| BDDC (w=0.5) | 1890 | 1890 | 0 | 0 | 0 | 0 |
| BDC (w=0.5) | 1890 | 1890 | 0 | 0 | 0 | 0 |
| DCR-v0 | 1890 | 1890 | 0 | 0 | 0 | 0 |
| DCR-v0 (optimized) | 1890 | 1890 | 0 | 0 | 0 | 0 |
| DCR-v1 (full ranking) | 1890 | 1890 | 0 | 0 | 0 | 0 |
| DCR-v1 Admission | 1890 | 1890 | 0 | 0 | 0 | 0 |
| DCR-v3 Rescue | 1890 | 1890 | 0 | 0 | 0 | 0 |

## Joint deadline-and-budget feasibility

| Algorithm | Joint feasible | Deadline met | Budget met | Median runtime (ms) | Runtime / BDC (w=0.5) median | p95 | max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DCR-v3 Rescue | 1844/1890 (97.6%) | 1844/1890 (97.6%) | 1890/1890 (100.0%) | 931 | 0.627x | 3.155x | 10.535x |
| **DCR-v1 Admission** | 1629/1890 (86.2%) | 1629/1890 (86.2%) | 1890/1890 (100.0%) | 766 | 0.515x | 1.110x | 1.337x |
| DCR-v1 (full ranking) | 1627/1890 (86.1%) | 1627/1890 (86.1%) | 1890/1890 (100.0%) | 763 | 0.515x | 1.110x | 1.337x |
| DCR-v0 | 1619/1890 (85.7%) | 1619/1890 (85.7%) | 1890/1890 (100.0%) | 1772 | 1.079x | 3.399x | 4.562x |
| DCR-v0 (optimized) | 1619/1890 (85.7%) | 1619/1890 (85.7%) | 1890/1890 (100.0%) | 627 | 0.440x | 0.998x | 1.257x |
| BDC (w=0.5) | 1427/1890 (75.5%) | 1435/1890 (75.9%) | 1858/1890 (98.3%) | 1368 | - | - | - |
| BDSD | 1109/1890 (58.7%) | 1109/1890 (58.7%) | 1890/1890 (100.0%) | 944 | 0.806x | 0.952x | 1.937x |
| DBCS | 904/1890 (47.8%) | 904/1890 (47.8%) | 1890/1890 (100.0%) | 1071 | 0.862x | 0.988x | 2.053x |
| BDHEFT (a=0.5) | 852/1890 (45.1%) | 934/1890 (49.4%) | 1710/1890 (90.5%) | 971 | 0.801x | 0.954x | 1.993x |
| BDDC (w=0.5) | 446/1890 (23.6%) | 1609/1890 (85.1%) | 679/1890 (35.9%) | 1386 | 1.007x | 1.083x | 1.889x |
| HEFT-IFC | 106/1890 (5.6%) | 1890/1890 (100.0%) | 106/1890 (5.6%) | 991 | 0.779x | 0.960x | 1.992x |
| PEFT-IFC | 18/1890 (1.0%) | 1826/1890 (96.6%) | 35/1890 (1.9%) | 613 | 0.491x | 0.572x | 1.192x |

Runtime is policy time only (schedule construction and scoring excluded), median over repetitions; ratios are paired on the same machine and case, p95 is nearest-rank.

## Joint feasibility by workflow family

| Workflow family | cybershake | genome | ligo | montage | sipht |
| --- | ---: | ---: | ---: | ---: | ---: |
| HEFT-IFC | 6/378 | 17/378 | 68/378 | 0/378 | 15/378 |
| PEFT-IFC | 4/378 | 2/378 | 6/378 | 4/378 | 2/378 |
| BDHEFT (a=0.5) | 158/378 | 149/378 | 199/378 | 184/378 | 162/378 |
| DBCS | 185/378 | 167/378 | 217/378 | 169/378 | 166/378 |
| BDSD | 228/378 | 253/378 | 252/378 | 258/378 | 118/378 |
| BDDC (w=0.5) | 60/378 | 47/378 | 83/378 | 90/378 | 166/378 |
| BDC (w=0.5) | 309/378 | 276/378 | 314/378 | 262/378 | 266/378 |
| DCR-v0 | 326/378 | 322/378 | 367/378 | 274/378 | 330/378 |
| DCR-v0 (optimized) | 326/378 | 322/378 | 367/378 | 274/378 | 330/378 |
| DCR-v1 (full ranking) | 325/378 | 322/378 | 367/378 | 276/378 | 337/378 |
| DCR-v1 Admission | 326/378 | 322/378 | 367/378 | 277/378 | 337/378 |
| DCR-v3 Rescue | 372/378 | 372/378 | 377/378 | 363/378 | 360/378 |

## Joint feasibility by number of tasks

| Number of tasks | 60 | 100 | 200 | 400 | 600 | 800 | 1000 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| HEFT-IFC | 15/270 | 8/270 | 12/270 | 14/270 | 19/270 | 18/270 | 20/270 |
| PEFT-IFC | 0/270 | 3/270 | 4/270 | 4/270 | 1/270 | 2/270 | 4/270 |
| BDHEFT (a=0.5) | 118/270 | 107/270 | 121/270 | 124/270 | 123/270 | 132/270 | 127/270 |
| DBCS | 120/270 | 108/270 | 126/270 | 129/270 | 136/270 | 141/270 | 144/270 |
| BDSD | 146/270 | 158/270 | 156/270 | 161/270 | 163/270 | 163/270 | 162/270 |
| BDDC (w=0.5) | 103/270 | 89/270 | 79/270 | 58/270 | 45/270 | 32/270 | 40/270 |
| BDC (w=0.5) | 169/270 | 175/270 | 196/270 | 216/270 | 228/270 | 223/270 | 220/270 |
| DCR-v0 | 231/270 | 235/270 | 235/270 | 237/270 | 242/270 | 222/270 | 217/270 |
| DCR-v0 (optimized) | 231/270 | 235/270 | 235/270 | 237/270 | 242/270 | 222/270 | 217/270 |
| DCR-v1 (full ranking) | 231/270 | 235/270 | 236/270 | 239/270 | 243/270 | 224/270 | 219/270 |
| DCR-v1 Admission | 232/270 | 238/270 | 236/270 | 239/270 | 242/270 | 223/270 | 219/270 |
| DCR-v3 Rescue | 260/270 | 264/270 | 259/270 | 263/270 | 267/270 | 264/270 | 267/270 |

## Joint feasibility by qos tightness

| QoS tightness | relaxed | moderate | tight |
| --- | ---: | ---: | ---: |
| HEFT-IFC | 0/630 | 0/630 | 106/630 |
| PEFT-IFC | 0/630 | 0/630 | 18/630 |
| BDHEFT (a=0.5) | 597/630 | 63/630 | 192/630 |
| DBCS | 630/630 | 7/630 | 267/630 |
| BDSD | 622/630 | 477/630 | 10/630 |
| BDDC (w=0.5) | 356/630 | 44/630 | 46/630 |
| BDC (w=0.5) | 630/630 | 556/630 | 241/630 |
| DCR-v0 | 630/630 | 553/630 | 436/630 |
| DCR-v0 (optimized) | 630/630 | 553/630 | 436/630 |
| DCR-v1 (full ranking) | 630/630 | 554/630 | 443/630 |
| DCR-v1 Admission | 630/630 | 554/630 | 445/630 |
| DCR-v3 Rescue | 630/630 | 629/630 | 585/630 |

## Joint feasibility by scenario

| Scenario | balanced | compute_constrained | network_constrained |
| --- | ---: | ---: | ---: |
| HEFT-IFC | 35/630 | 35/630 | 36/630 |
| PEFT-IFC | 4/630 | 9/630 | 5/630 |
| BDHEFT (a=0.5) | 302/630 | 261/630 | 289/630 |
| DBCS | 300/630 | 302/630 | 302/630 |
| BDSD | 370/630 | 369/630 | 370/630 |
| BDDC (w=0.5) | 143/630 | 158/630 | 145/630 |
| BDC (w=0.5) | 478/630 | 471/630 | 478/630 |
| DCR-v0 | 546/630 | 537/630 | 536/630 |
| DCR-v0 (optimized) | 546/630 | 537/630 | 536/630 |
| DCR-v1 (full ranking) | 550/630 | 539/630 | 538/630 |
| DCR-v1 Admission | 550/630 | 539/630 | 540/630 |
| DCR-v3 Rescue | 620/630 | 614/630 | 610/630 |

## Joint feasibility by resource scale

| Resource scale | S01 | S02 | S03 |
| --- | ---: | ---: | ---: |
| HEFT-IFC | 35/630 | 23/630 | 48/630 |
| PEFT-IFC | 9/630 | 1/630 | 8/630 |
| BDHEFT (a=0.5) | 306/630 | 268/630 | 278/630 |
| DBCS | 323/630 | 268/630 | 313/630 |
| BDSD | 376/630 | 384/630 | 349/630 |
| BDDC (w=0.5) | 165/630 | 183/630 | 98/630 |
| BDC (w=0.5) | 525/630 | 490/630 | 412/630 |
| DCR-v0 | 563/630 | 524/630 | 532/630 |
| DCR-v0 (optimized) | 563/630 | 524/630 | 532/630 |
| DCR-v1 (full ranking) | 566/630 | 529/630 | 532/630 |
| DCR-v1 Admission | 566/630 | 528/630 | 535/630 |
| DCR-v3 Rescue | 618/630 | 611/630 | 615/630 |

## DCR-v1 Admission against each algorithm

| Against | Cases only DCR-v1 Admission is feasible | Cases only the other is feasible | Both feasible | Makespan ratio (median) | Cost ratio (median) | Energy ratio (median) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| HEFT-IFC | 1523 | 0 | 106 | 1.026 | 0.991 | 1.007 |
| PEFT-IFC | 1611 | 0 | 18 | 1.009 | 0.995 | 0.999 |
| BDHEFT (a=0.5) | 790 | 13 | 839 | 1.000 | 0.959 | 1.008 |
| DBCS | 726 | 1 | 903 | 0.729 | 0.931 | 1.030 |
| BDSD | 584 | 64 | 1045 | 0.864 | 1.161 | 0.922 |
| BDDC (w=0.5) | 1183 | 0 | 446 | 0.890 | 0.947 | 0.990 |
| BDC (w=0.5) | 255 | 53 | 1374 | 0.844 | 1.010 | 0.959 |
| DCR-v0 | 10 | 0 | 1619 | 1.000 | 1.000 | 1.000 |
| DCR-v0 (optimized) | 10 | 0 | 1619 | 1.000 | 1.000 | 1.000 |
| DCR-v1 (full ranking) | 5 | 3 | 1624 | 1.000 | 1.000 | 1.000 |
| DCR-v3 Rescue | 0 | 215 | 1629 | 1.000 | 1.000 | 1.000 |

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

