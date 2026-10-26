# Report: unseen-all-bdcws

Instance set: **unseen**. Algorithms: HEFT-IFC, PEFT-IFC, BDHEFT (a=0.5), DBCS, BDSD, BDDC (w=0.5), BDC (w=0.5), BDCWS, DCR-v0, DCR-v0 (optimized), DCR-v1 (full ranking), DCR-v1 Admission, DCR-v3 Rescue. Highlight: DCR-v1 Admission. Cases: 2241 selected, **2241 compared** (every selected algorithm valid, and deterministic where checked).

Determinism was not re-observed for 29133 one-repetition runs; the replay check against the historical results covers it.

## Validity

| Algorithm | Runs | Valid + deterministic | Errors | Invalid | Nondeterministic | Missing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| HEFT-IFC | 2241 | 2241 | 0 | 0 | 0 | 0 |
| PEFT-IFC | 2241 | 2241 | 0 | 0 | 0 | 0 |
| BDHEFT (a=0.5) | 2241 | 2241 | 0 | 0 | 0 | 0 |
| DBCS | 2241 | 2241 | 0 | 0 | 0 | 0 |
| BDSD | 2241 | 2241 | 0 | 0 | 0 | 0 |
| BDDC (w=0.5) | 2241 | 2241 | 0 | 0 | 0 | 0 |
| BDC (w=0.5) | 2241 | 2241 | 0 | 0 | 0 | 0 |
| BDCWS | 2241 | 2241 | 0 | 0 | 0 | 0 |
| DCR-v0 | 2241 | 2241 | 0 | 0 | 0 | 0 |
| DCR-v0 (optimized) | 2241 | 2241 | 0 | 0 | 0 | 0 |
| DCR-v1 (full ranking) | 2241 | 2241 | 0 | 0 | 0 | 0 |
| DCR-v1 Admission | 2241 | 2241 | 0 | 0 | 0 | 0 |
| DCR-v3 Rescue | 2241 | 2241 | 0 | 0 | 0 | 0 |

## Joint deadline-and-budget feasibility

| Algorithm | Joint feasible | Deadline met | Budget met | Median runtime (ms) | Runtime / BDC (w=0.5) median | p95 | max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DCR-v3 Rescue | 2208/2241 (98.5%) | 2208/2241 (98.5%) | 2241/2241 (100.0%) | 890 | 0.601x | 3.001x | 10.492x |
| **DCR-v1 Admission** | 1905/2241 (85.0%) | 1905/2241 (85.0%) | 2241/2241 (100.0%) | 731 | 0.476x | 1.027x | 1.307x |
| DCR-v0 | 1902/2241 (84.9%) | 1902/2241 (84.9%) | 2241/2241 (100.0%) | 1589 | 0.970x | 3.098x | 4.557x |
| DCR-v0 (optimized) | 1902/2241 (84.9%) | 1902/2241 (84.9%) | 2241/2241 (100.0%) | 613 | 0.396x | 0.926x | 1.211x |
| DCR-v1 (full ranking) | 1900/2241 (84.8%) | 1900/2241 (84.8%) | 2241/2241 (100.0%) | 732 | 0.474x | 1.032x | 1.352x |
| BDCWS | 1638/2241 (73.1%) | 1638/2241 (73.1%) | 2241/2241 (100.0%) | 1211 | 0.915x | 1.838x | 3.367x |
| BDC (w=0.5) | 1610/2241 (71.8%) | 1653/2241 (73.8%) | 2131/2241 (95.1%) | 1475 | - | - | - |
| BDSD | 1293/2241 (57.7%) | 1293/2241 (57.7%) | 2241/2241 (100.0%) | 1067 | 0.828x | 0.954x | 2.076x |
| DBCS | 1162/2241 (51.9%) | 1162/2241 (51.9%) | 2241/2241 (100.0%) | 1160 | 0.875x | 0.982x | 2.102x |
| BDHEFT (a=0.5) | 1049/2241 (46.8%) | 1129/2241 (50.4%) | 2064/2241 (92.1%) | 1070 | 0.825x | 0.961x | 2.058x |
| BDDC (w=0.5) | 402/2241 (17.9%) | 1962/2241 (87.6%) | 631/2241 (28.2%) | 1502 | 1.007x | 1.067x | 1.864x |
| HEFT-IFC | 134/2241 (6.0%) | 2241/2241 (100.0%) | 134/2241 (6.0%) | 1074 | 0.805x | 0.964x | 2.059x |
| PEFT-IFC | 8/2241 (0.4%) | 2140/2241 (95.5%) | 27/2241 (1.2%) | 677 | 0.504x | 0.581x | 1.243x |

Runtime is policy time only (schedule construction and scoring excluded), median over repetitions; ratios are paired on the same machine and case, p95 is nearest-rank.

## Joint feasibility by workflow family

| Workflow family | 1000genome | blast | cybershake | genome | ligo | montage | sipht | soykb | srasearch |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| HEFT-IFC | 14/378 | 17/378 | 1/189 | 14/189 | 40/189 | 4/189 | 11/189 | 3/162 | 30/378 |
| PEFT-IFC | 0/378 | 0/378 | 1/189 | 3/189 | 3/189 | 1/189 | 0/189 | 0/162 | 0/378 |
| BDHEFT (a=0.5) | 170/378 | 185/378 | 72/189 | 85/189 | 113/189 | 84/189 | 79/189 | 75/162 | 186/378 |
| DBCS | 183/378 | 209/378 | 102/189 | 93/189 | 122/189 | 83/189 | 99/189 | 65/162 | 206/378 |
| BDSD | 249/378 | 260/378 | 95/189 | 123/189 | 123/189 | 126/189 | 55/189 | 108/162 | 154/378 |
| BDDC (w=0.5) | 103/378 | 15/378 | 17/189 | 21/189 | 36/189 | 32/189 | 69/189 | 53/162 | 56/378 |
| BDC (w=0.5) | 276/378 | 292/378 | 147/189 | 137/189 | 142/189 | 112/189 | 122/189 | 88/162 | 294/378 |
| BDCWS | 255/378 | 375/378 | 110/189 | 141/189 | 120/189 | 139/189 | 110/189 | 113/162 | 275/378 |
| DCR-v0 | 288/378 | 319/378 | 175/189 | 169/189 | 187/189 | 132/189 | 163/189 | 134/162 | 335/378 |
| DCR-v0 (optimized) | 288/378 | 319/378 | 175/189 | 169/189 | 187/189 | 132/189 | 163/189 | 134/162 | 335/378 |
| DCR-v1 (full ranking) | 288/378 | 319/378 | 174/189 | 169/189 | 186/189 | 134/189 | 161/189 | 134/162 | 335/378 |
| DCR-v1 Admission | 288/378 | 319/378 | 175/189 | 169/189 | 187/189 | 135/189 | 163/189 | 134/162 | 335/378 |
| DCR-v3 Rescue | 372/378 | 378/378 | 186/189 | 185/189 | 189/189 | 184/189 | 179/189 | 162/162 | 373/378 |

## Joint feasibility by number of tasks

| Number of tasks | 60 | 100 | 200 | 400 | 600 | 800 | 1000 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| HEFT-IFC | 10/297 | 18/297 | 25/351 | 23/351 | 17/297 | 19/351 | 22/297 |
| PEFT-IFC | 0/297 | 0/297 | 1/351 | 2/351 | 1/297 | 1/351 | 3/297 |
| BDHEFT (a=0.5) | 120/297 | 122/297 | 159/351 | 163/351 | 151/297 | 181/351 | 153/297 |
| DBCS | 133/297 | 139/297 | 183/351 | 181/351 | 162/297 | 191/351 | 173/297 |
| BDSD | 158/297 | 160/297 | 202/351 | 209/351 | 176/297 | 211/351 | 177/297 |
| BDDC (w=0.5) | 89/297 | 73/297 | 73/351 | 61/351 | 35/297 | 43/351 | 28/297 |
| BDC (w=0.5) | 181/297 | 199/297 | 252/351 | 263/351 | 233/297 | 260/351 | 222/297 |
| BDCWS | 221/297 | 222/297 | 255/351 | 252/351 | 217/297 | 255/351 | 216/297 |
| DCR-v0 | 252/297 | 257/297 | 323/351 | 304/351 | 246/297 | 283/351 | 237/297 |
| DCR-v0 (optimized) | 252/297 | 257/297 | 323/351 | 304/351 | 246/297 | 283/351 | 237/297 |
| DCR-v1 (full ranking) | 249/297 | 257/297 | 322/351 | 302/351 | 246/297 | 286/351 | 238/297 |
| DCR-v1 Admission | 252/297 | 257/297 | 323/351 | 304/351 | 246/297 | 285/351 | 238/297 |
| DCR-v3 Rescue | 292/297 | 295/297 | 348/351 | 347/351 | 289/297 | 345/351 | 292/297 |

## Joint feasibility by qos tightness

| QoS tightness | relaxed | moderate | tight |
| --- | ---: | ---: | ---: |
| HEFT-IFC | 0/747 | 0/747 | 134/747 |
| PEFT-IFC | 0/747 | 0/747 | 8/747 |
| BDHEFT (a=0.5) | 706/747 | 29/747 | 314/747 |
| DBCS | 747/747 | 7/747 | 408/747 |
| BDSD | 738/747 | 547/747 | 8/747 |
| BDDC (w=0.5) | 324/747 | 20/747 | 58/747 |
| BDC (w=0.5) | 747/747 | 571/747 | 292/747 |
| BDCWS | 747/747 | 697/747 | 194/747 |
| DCR-v0 | 747/747 | 611/747 | 544/747 |
| DCR-v0 (optimized) | 747/747 | 611/747 | 544/747 |
| DCR-v1 (full ranking) | 747/747 | 610/747 | 543/747 |
| DCR-v1 Admission | 747/747 | 611/747 | 547/747 |
| DCR-v3 Rescue | 747/747 | 747/747 | 714/747 |

## Joint feasibility by scenario

| Scenario | balanced | compute_constrained | network_constrained |
| --- | ---: | ---: | ---: |
| HEFT-IFC | 50/747 | 47/747 | 37/747 |
| PEFT-IFC | 1/747 | 6/747 | 1/747 |
| BDHEFT (a=0.5) | 365/747 | 328/747 | 356/747 |
| DBCS | 389/747 | 390/747 | 383/747 |
| BDSD | 422/747 | 450/747 | 421/747 |
| BDDC (w=0.5) | 121/747 | 144/747 | 137/747 |
| BDC (w=0.5) | 543/747 | 538/747 | 529/747 |
| BDCWS | 549/747 | 543/747 | 546/747 |
| DCR-v0 | 636/747 | 628/747 | 638/747 |
| DCR-v0 (optimized) | 636/747 | 628/747 | 638/747 |
| DCR-v1 (full ranking) | 634/747 | 628/747 | 638/747 |
| DCR-v1 Admission | 637/747 | 629/747 | 639/747 |
| DCR-v3 Rescue | 735/747 | 740/747 | 733/747 |

## Joint feasibility by resource scale

| Resource scale | S01 | S02 | S03 |
| --- | ---: | ---: | ---: |
| HEFT-IFC | 46/747 | 35/747 | 53/747 |
| PEFT-IFC | 3/747 | 2/747 | 3/747 |
| BDHEFT (a=0.5) | 404/747 | 331/747 | 314/747 |
| DBCS | 422/747 | 350/747 | 390/747 |
| BDSD | 446/747 | 442/747 | 405/747 |
| BDDC (w=0.5) | 162/747 | 165/747 | 75/747 |
| BDC (w=0.5) | 603/747 | 539/747 | 468/747 |
| BDCWS | 550/747 | 547/747 | 541/747 |
| DCR-v0 | 683/747 | 610/747 | 609/747 |
| DCR-v0 (optimized) | 683/747 | 610/747 | 609/747 |
| DCR-v1 (full ranking) | 682/747 | 609/747 | 609/747 |
| DCR-v1 Admission | 683/747 | 613/747 | 609/747 |
| DCR-v3 Rescue | 736/747 | 736/747 | 736/747 |

## DCR-v1 Admission against each algorithm

| Against | Cases only DCR-v1 Admission is feasible | Cases only the other is feasible | Both feasible | Makespan ratio (median) | Cost ratio (median) | Energy ratio (median) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| HEFT-IFC | 1772 | 1 | 133 | 1.010 | 0.994 | 1.002 |
| PEFT-IFC | 1897 | 0 | 8 | 1.016 | 0.993 | 1.003 |
| BDHEFT (a=0.5) | 862 | 6 | 1043 | 0.956 | 0.991 | 1.004 |
| DBCS | 745 | 2 | 1160 | 0.716 | 0.984 | 1.000 |
| BDSD | 727 | 115 | 1178 | 0.748 | 1.190 | 0.872 |
| BDDC (w=0.5) | 1504 | 1 | 401 | 0.830 | 0.999 | 0.972 |
| BDC (w=0.5) | 343 | 48 | 1562 | 0.814 | 1.015 | 0.949 |
| BDCWS | 458 | 191 | 1447 | 0.412 | 1.354 | 0.817 |
| DCR-v0 | 3 | 0 | 1902 | 1.000 | 1.000 | 1.000 |
| DCR-v0 (optimized) | 3 | 0 | 1902 | 1.000 | 1.000 | 1.000 |
| DCR-v1 (full ranking) | 6 | 1 | 1899 | 1.000 | 1.000 | 1.000 |
| DCR-v3 Rescue | 0 | 303 | 1905 | 1.000 | 1.000 | 1.000 |

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

