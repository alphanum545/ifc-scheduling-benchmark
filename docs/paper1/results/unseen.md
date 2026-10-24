# Unseen-workflow test (ifc-unseen-v1)

2241/2241 instances with valid results for all 12 algorithms.

| Algorithm | Joint feasible | 95% CI | Deadline met | Budget met |
|---|---:|---|---:|---:|
| dcr-v3-rescue | 2208 (98.5%) | 97.9–98.9% | 2208 | 2241 |
| dcr-v1-admission | 1905 (85.0%) | 83.5–86.4% | 1905 | 2241 |
| dcr-v0 | 1902 (84.9%) | 83.3–86.3% | 1902 | 2241 |
| dcr-v0-opt | 1902 (84.9%) | 83.3–86.3% | 1902 | 2241 |
| dcr-v1 | 1900 (84.8%) | 83.2–86.2% | 1900 | 2241 |
| bdc | 1610 (71.8%) | 69.9–73.7% | 1653 | 2131 |
| bdsd | 1293 (57.7%) | 55.6–59.7% | 1293 | 2241 |
| dbcs | 1162 (51.9%) | 49.8–53.9% | 1162 | 2241 |
| bdheft | 1049 (46.8%) | 44.8–48.9% | 1129 | 2064 |
| bddc | 402 (17.9%) | 16.4–19.6% | 1962 | 631 |
| heft-ifc | 134 (6.0%) | 5.1–7.0% | 2241 | 134 |
| peft-ifc | 8 (0.4%) | 0.2–0.7% | 2140 | 27 |

## DCR-v1 Admission vs each comparator (exact McNemar, Holm over 7)

| Against | Only DCR-v1 | Only other | p (Holm) |
|---|---:|---:|---:|
| bdc | 343 | 48 | 4.9e-56 |
| bdsd | 727 | 115 | 4.1e-109 |
| dbcs | 745 | 2 | 2.3e-219 |
| bdheft | 862 | 6 | 2.4e-246 |
| bddc | 1504 | 1 | 0.0e+00 |
| heft-ifc | 1772 | 1 | 0.0e+00 |
| peft-ifc | 1897 | 0 | 0.0e+00 |

DCR-v3 Rescue vs DCR-v1 Admission: only v3 303, only v1 0, p = 1.2e-91.

## By family

| family | n | dcr-v3-rescue | dcr-v1-admission | bdc | bdsd | DCR-v1 vs BDC (only/only) |
|---|---:|---:|---:|---:|---:|---:|
| 1000genome | 378 | 98.4% | 76.2% | 73.0% | 65.9% | 41/29 |
| blast | 378 | 100.0% | 84.4% | 77.2% | 68.8% | 28/1 |
| cybershake | 189 | 98.4% | 92.6% | 77.8% | 50.3% | 33/5 |
| genome | 189 | 97.9% | 89.4% | 72.5% | 65.1% | 34/2 |
| ligo | 189 | 100.0% | 98.9% | 75.1% | 65.1% | 46/1 |
| montage | 189 | 97.4% | 71.4% | 59.3% | 66.7% | 27/4 |
| sipht | 189 | 94.7% | 86.2% | 64.6% | 29.1% | 47/6 |
| soykb | 162 | 100.0% | 82.7% | 54.3% | 66.7% | 46/0 |
| srasearch | 378 | 98.7% | 88.6% | 77.8% | 40.7% | 41/0 |

## By source kind

| source kind | n | dcr-v3-rescue | dcr-v1-admission | bdc | bdsd | DCR-v1 vs BDC (only/only) |
|---|---:|---:|---:|---:|---:|---:|
| new_family | 1296 | 99.2% | 83.0% | 73.3% | 59.5% | 156/30 |
| new_replicate | 945 | 97.7% | 87.7% | 69.8% | 55.2% | 187/18 |

## By QoS

| QoS | n | dcr-v3-rescue | dcr-v1-admission | bdc | bdsd | DCR-v1 vs BDC (only/only) |
|---|---:|---:|---:|---:|---:|---:|
| moderate | 747 | 100.0% | 81.8% | 76.4% | 73.2% | 78/38 |
| relaxed | 747 | 100.0% | 100.0% | 100.0% | 98.8% | 0/0 |
| tight | 747 | 95.6% | 73.2% | 39.1% | 1.1% | 265/10 |

## By tasks

| tasks | n | dcr-v3-rescue | dcr-v1-admission | bdc | bdsd | DCR-v1 vs BDC (only/only) |
|---|---:|---:|---:|---:|---:|---:|
| 100 | 297 | 99.3% | 86.5% | 67.0% | 53.9% | 59/1 |
| 1000 | 297 | 98.3% | 80.1% | 74.7% | 59.6% | 26/10 |
| 200 | 351 | 99.1% | 92.0% | 71.8% | 57.5% | 73/2 |
| 400 | 351 | 98.9% | 86.6% | 74.9% | 59.5% | 52/11 |
| 60 | 297 | 98.3% | 84.8% | 60.9% | 53.2% | 71/0 |
| 600 | 297 | 97.3% | 82.8% | 78.5% | 59.3% | 27/14 |
| 800 | 351 | 98.3% | 81.2% | 74.1% | 60.1% | 35/10 |

Where both feasible (n=1562): DCR-v1/BDC median makespan 0.814, cost 1.015.
