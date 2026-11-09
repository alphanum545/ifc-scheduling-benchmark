# Report: paper2-expansion

Instance set: **expansion**. Algorithms: DCR-Cost v2 (+ deadline-split candidates), DCR-Cost v1 (portfolio + improvement), IC-PCP, CMaS, ProLiS (seed 0), ProLiS (seed 1), ProLiS (seed 2), ProLiS (seed 3), ProLiS (seed 4), ProLiS (seed 5), ProLiS (seed 6), ProLiS (seed 7), ProLiS (seed 8), ProLiS (seed 9). Highlight: DCR-Cost v2 (+ deadline-split candidates). Cases: 1890 selected, **1890 compared** (every selected algorithm valid, and deterministic where checked).

Determinism was not re-observed for 26460 one-repetition runs; the replay check against the historical results covers it.

## Validity

| Algorithm | Runs | Valid + deterministic | Errors | Invalid | Nondeterministic | Missing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DCR-Cost v2 (+ deadline-split candidates) | 1890 | 1890 | 0 | 0 | 0 | 0 |
| DCR-Cost v1 (portfolio + improvement) | 1890 | 1890 | 0 | 0 | 0 | 0 |
| IC-PCP | 1890 | 1890 | 0 | 0 | 0 | 0 |
| CMaS | 1890 | 1890 | 0 | 0 | 0 | 0 |
| ProLiS (seed 0) | 1890 | 1890 | 0 | 0 | 0 | 0 |
| ProLiS (seed 1) | 1890 | 1890 | 0 | 0 | 0 | 0 |
| ProLiS (seed 2) | 1890 | 1890 | 0 | 0 | 0 | 0 |
| ProLiS (seed 3) | 1890 | 1890 | 0 | 0 | 0 | 0 |
| ProLiS (seed 4) | 1890 | 1890 | 0 | 0 | 0 | 0 |
| ProLiS (seed 5) | 1890 | 1890 | 0 | 0 | 0 | 0 |
| ProLiS (seed 6) | 1890 | 1890 | 0 | 0 | 0 | 0 |
| ProLiS (seed 7) | 1890 | 1890 | 0 | 0 | 0 | 0 |
| ProLiS (seed 8) | 1890 | 1890 | 0 | 0 | 0 | 0 |
| ProLiS (seed 9) | 1890 | 1890 | 0 | 0 | 0 | 0 |

## Joint deadline-and-budget feasibility

| Algorithm | Joint feasible | Deadline met | Budget met | Median runtime (ms) | Runtime / - median | p95 | max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **DCR-Cost v2 (+ deadline-split candidates)** | 1848/1890 (97.8%) | 1890/1890 (100.0%) | 1848/1890 (97.8%) | 8031 | - | - | - |
| DCR-Cost v1 (portfolio + improvement) | 1790/1890 (94.7%) | 1890/1890 (100.0%) | 1790/1890 (94.7%) | 2626 | - | - | - |
| ProLiS (seed 7) | 1628/1890 (86.1%) | 1814/1890 (96.0%) | 1699/1890 (89.9%) | 490 | - | - | - |
| ProLiS (seed 0) | 1627/1890 (86.1%) | 1809/1890 (95.7%) | 1702/1890 (90.1%) | 491 | - | - | - |
| ProLiS (seed 4) | 1627/1890 (86.1%) | 1813/1890 (95.9%) | 1697/1890 (89.8%) | 491 | - | - | - |
| ProLiS (seed 1) | 1626/1890 (86.0%) | 1815/1890 (96.0%) | 1695/1890 (89.7%) | 492 | - | - | - |
| ProLiS (seed 9) | 1626/1890 (86.0%) | 1815/1890 (96.0%) | 1698/1890 (89.8%) | 492 | - | - | - |
| ProLiS (seed 6) | 1625/1890 (86.0%) | 1808/1890 (95.7%) | 1700/1890 (89.9%) | 493 | - | - | - |
| ProLiS (seed 2) | 1624/1890 (85.9%) | 1811/1890 (95.8%) | 1698/1890 (89.8%) | 490 | - | - | - |
| ProLiS (seed 3) | 1624/1890 (85.9%) | 1815/1890 (96.0%) | 1695/1890 (89.7%) | 491 | - | - | - |
| ProLiS (seed 5) | 1623/1890 (85.9%) | 1813/1890 (95.9%) | 1696/1890 (89.7%) | 490 | - | - | - |
| ProLiS (seed 8) | 1618/1890 (85.6%) | 1804/1890 (95.4%) | 1697/1890 (89.8%) | 491 | - | - | - |
| IC-PCP | 983/1890 (52.0%) | 1717/1890 (90.8%) | 1090/1890 (57.7%) | 1106 | - | - | - |
| CMaS | 278/1890 (14.7%) | 278/1890 (14.7%) | 1890/1890 (100.0%) | 3142 | - | - | - |

Runtime is policy time only (schedule construction and scoring excluded), median over repetitions; ratios are paired on the same machine and case, p95 is nearest-rank.

## Joint feasibility by workflow family

| Workflow family | cybershake | genome | ligo | montage | sipht |
| --- | ---: | ---: | ---: | ---: | ---: |
| DCR-Cost v2 (+ deadline-split candidates) | 375/378 | 373/378 | 378/378 | 348/378 | 374/378 |
| DCR-Cost v1 (portfolio + improvement) | 372/378 | 371/378 | 345/378 | 339/378 | 363/378 |
| IC-PCP | 151/378 | 139/378 | 317/378 | 69/378 | 307/378 |
| CMaS | 32/378 | 68/378 | 29/378 | 66/378 | 83/378 |
| ProLiS (seed 0) | 331/378 | 342/378 | 369/378 | 241/378 | 344/378 |
| ProLiS (seed 1) | 334/378 | 342/378 | 369/378 | 237/378 | 344/378 |
| ProLiS (seed 2) | 332/378 | 341/378 | 369/378 | 238/378 | 344/378 |
| ProLiS (seed 3) | 333/378 | 342/378 | 369/378 | 236/378 | 344/378 |
| ProLiS (seed 4) | 333/378 | 342/378 | 369/378 | 239/378 | 344/378 |
| ProLiS (seed 5) | 332/378 | 341/378 | 369/378 | 237/378 | 344/378 |
| ProLiS (seed 6) | 330/378 | 342/378 | 369/378 | 240/378 | 344/378 |
| ProLiS (seed 7) | 334/378 | 341/378 | 369/378 | 240/378 | 344/378 |
| ProLiS (seed 8) | 323/378 | 342/378 | 369/378 | 240/378 | 344/378 |
| ProLiS (seed 9) | 334/378 | 342/378 | 369/378 | 237/378 | 344/378 |

## Joint feasibility by number of tasks

| Number of tasks | 60 | 100 | 200 | 400 | 600 | 800 | 1000 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DCR-Cost v2 (+ deadline-split candidates) | 260/270 | 261/270 | 261/270 | 265/270 | 268/270 | 267/270 | 266/270 |
| DCR-Cost v1 (portfolio + improvement) | 257/270 | 257/270 | 259/270 | 254/270 | 259/270 | 251/270 | 253/270 |
| IC-PCP | 185/270 | 166/270 | 141/270 | 124/270 | 129/270 | 116/270 | 122/270 |
| CMaS | 58/270 | 63/270 | 53/270 | 32/270 | 30/270 | 22/270 | 20/270 |
| ProLiS (seed 0) | 230/270 | 238/270 | 237/270 | 232/270 | 235/270 | 224/270 | 231/270 |
| ProLiS (seed 1) | 230/270 | 241/270 | 237/270 | 233/270 | 235/270 | 220/270 | 230/270 |
| ProLiS (seed 2) | 228/270 | 239/270 | 237/270 | 231/270 | 234/270 | 224/270 | 231/270 |
| ProLiS (seed 3) | 228/270 | 240/270 | 238/270 | 231/270 | 235/270 | 221/270 | 231/270 |
| ProLiS (seed 4) | 229/270 | 240/270 | 238/270 | 232/270 | 235/270 | 224/270 | 229/270 |
| ProLiS (seed 5) | 231/270 | 236/270 | 236/270 | 232/270 | 234/270 | 224/270 | 230/270 |
| ProLiS (seed 6) | 226/270 | 238/270 | 238/270 | 231/270 | 235/270 | 225/270 | 232/270 |
| ProLiS (seed 7) | 229/270 | 239/270 | 237/270 | 232/270 | 234/270 | 225/270 | 232/270 |
| ProLiS (seed 8) | 230/270 | 235/270 | 234/270 | 232/270 | 235/270 | 221/270 | 231/270 |
| ProLiS (seed 9) | 231/270 | 240/270 | 237/270 | 231/270 | 235/270 | 223/270 | 229/270 |

## Joint feasibility by qos tightness

| QoS tightness | relaxed | moderate | tight |
| --- | ---: | ---: | ---: |
| DCR-Cost v2 (+ deadline-split candidates) | 630/630 | 630/630 | 588/630 |
| DCR-Cost v1 (portfolio + improvement) | 630/630 | 605/630 | 555/630 |
| IC-PCP | 423/630 | 306/630 | 254/630 |
| CMaS | 278/630 | 0/630 | 0/630 |
| ProLiS (seed 0) | 630/630 | 566/630 | 431/630 |
| ProLiS (seed 1) | 630/630 | 569/630 | 427/630 |
| ProLiS (seed 2) | 630/630 | 567/630 | 427/630 |
| ProLiS (seed 3) | 630/630 | 567/630 | 427/630 |
| ProLiS (seed 4) | 630/630 | 570/630 | 427/630 |
| ProLiS (seed 5) | 630/630 | 569/630 | 424/630 |
| ProLiS (seed 6) | 630/630 | 566/630 | 429/630 |
| ProLiS (seed 7) | 630/630 | 568/630 | 430/630 |
| ProLiS (seed 8) | 630/630 | 569/630 | 419/630 |
| ProLiS (seed 9) | 630/630 | 569/630 | 427/630 |

## Joint feasibility by scenario

| Scenario | balanced | compute_constrained | network_constrained |
| --- | ---: | ---: | ---: |
| DCR-Cost v2 (+ deadline-split candidates) | 622/630 | 611/630 | 615/630 |
| DCR-Cost v1 (portfolio + improvement) | 603/630 | 592/630 | 595/630 |
| IC-PCP | 343/630 | 314/630 | 326/630 |
| CMaS | 94/630 | 89/630 | 95/630 |
| ProLiS (seed 0) | 557/630 | 526/630 | 544/630 |
| ProLiS (seed 1) | 557/630 | 525/630 | 544/630 |
| ProLiS (seed 2) | 556/630 | 524/630 | 544/630 |
| ProLiS (seed 3) | 557/630 | 524/630 | 543/630 |
| ProLiS (seed 4) | 558/630 | 522/630 | 547/630 |
| ProLiS (seed 5) | 555/630 | 523/630 | 545/630 |
| ProLiS (seed 6) | 556/630 | 525/630 | 544/630 |
| ProLiS (seed 7) | 555/630 | 525/630 | 548/630 |
| ProLiS (seed 8) | 555/630 | 522/630 | 541/630 |
| ProLiS (seed 9) | 556/630 | 526/630 | 544/630 |

## Joint feasibility by resource scale

| Resource scale | S01 | S02 | S03 |
| --- | ---: | ---: | ---: |
| DCR-Cost v2 (+ deadline-split candidates) | 621/630 | 620/630 | 607/630 |
| DCR-Cost v1 (portfolio + improvement) | 617/630 | 599/630 | 574/630 |
| IC-PCP | 293/630 | 318/630 | 372/630 |
| CMaS | 124/630 | 122/630 | 32/630 |
| ProLiS (seed 0) | 554/630 | 562/630 | 511/630 |
| ProLiS (seed 1) | 554/630 | 557/630 | 515/630 |
| ProLiS (seed 2) | 553/630 | 559/630 | 512/630 |
| ProLiS (seed 3) | 554/630 | 560/630 | 510/630 |
| ProLiS (seed 4) | 554/630 | 559/630 | 514/630 |
| ProLiS (seed 5) | 551/630 | 558/630 | 514/630 |
| ProLiS (seed 6) | 556/630 | 560/630 | 509/630 |
| ProLiS (seed 7) | 554/630 | 560/630 | 514/630 |
| ProLiS (seed 8) | 546/630 | 557/630 | 515/630 |
| ProLiS (seed 9) | 554/630 | 560/630 | 512/630 |

## DCR-Cost v2 (+ deadline-split candidates) against each algorithm

| Against | Cases only DCR-Cost v2 (+ deadline-split candidates) is feasible | Cases only the other is feasible | Both feasible | Makespan ratio (median) | Cost ratio (median) | Energy ratio (median) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DCR-Cost v1 (portfolio + improvement) | 58 | 0 | 1790 | 1.000 | 0.995 | 1.000 |
| IC-PCP | 869 | 4 | 979 | 1.148 | 0.717 | 1.029 |
| CMaS | 1570 | 0 | 278 | 1.005 | 0.363 | 1.036 |
| ProLiS (seed 0) | 221 | 0 | 1627 | 1.004 | 0.988 | 1.000 |
| ProLiS (seed 1) | 223 | 1 | 1625 | 1.004 | 0.988 | 1.000 |
| ProLiS (seed 2) | 224 | 0 | 1624 | 1.004 | 0.988 | 1.000 |
| ProLiS (seed 3) | 224 | 0 | 1624 | 1.004 | 0.988 | 1.000 |
| ProLiS (seed 4) | 221 | 0 | 1627 | 1.004 | 0.988 | 1.000 |
| ProLiS (seed 5) | 225 | 0 | 1623 | 1.004 | 0.988 | 1.000 |
| ProLiS (seed 6) | 223 | 0 | 1625 | 1.004 | 0.988 | 1.000 |
| ProLiS (seed 7) | 220 | 0 | 1628 | 1.004 | 0.988 | 1.000 |
| ProLiS (seed 8) | 231 | 1 | 1617 | 1.004 | 0.988 | 1.000 |
| ProLiS (seed 9) | 222 | 0 | 1626 | 1.004 | 0.988 | 1.000 |

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

