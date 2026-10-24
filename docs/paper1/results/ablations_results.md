# Component ablations of DCR-v1 Admission

## dev (160 instances)

Control schedule identical to DCR-v1 Admission's stored schedule: **160/160**.

| Variant | Joint feasible | Δ vs control (pp) | Only control | Only variant | p (Holm, 5 variants) | Deadline met | Budget met |
|---|---:|---:|---:|---:|---:|---:|---:|
| Control (= DCR-v1 Admission) | 140 (87.5%) | | | | | 140 | 160 |
| DCR-v1 Admission | 140 (87.5%) | | | | | 140 | 160 |
| BDC | 120 (75.0%) | | | | | 120 | 156 |
| No priced reserve (raw cheapest-remaining only) | 137 (85.6%) | -1.9 | 4 | 1 | 1.0e+00 | 137 | 160 |
| Zero dual prices | 140 (87.5%) | +0.0 | 0 | 0 | 1.0e+00 | 140 | 160 |
| Time-only ranking | 83 (51.9%) | -35.6 | 57 | 0 | 6.9e-17 | 83 | 160 |
| Budget-only ranking | 82 (51.2%) | -36.2 | 61 | 3 | 1.9e-14 | 82 | 160 |
| Weighted-sum ranking (0.5/0.5) | 142 (88.8%) | +1.2 | 1 | 3 | 1.0e+00 | 142 | 160 |

Where both are jointly feasible, median variant/control ratio:

| Variant | n | Makespan | Cost |
|---|---:|---:|---:|
| No priced reserve (raw cheapest-remaining only) | 136 | 1.000 | 1.000 |
| Zero dual prices | 140 | 1.000 | 1.000 |
| Time-only ranking | 83 | 1.317 | 1.074 |
| Budget-only ranking | 79 | 5.328 | 0.201 |
| Weighted-sum ranking (0.5/0.5) | 139 | 1.012 | 0.999 |

Joint feasibility under tight QoS:

| Algorithm | Tight joint feasible |
|---|---:|
| Control (= DCR-v1 Admission) | 39/54 |
| No priced reserve (raw cheapest-remaining only) | 36/54 |
| Zero dual prices | 39/54 |
| Time-only ranking | 27/54 |
| Budget-only ranking | 11/54 |
| Weighted-sum ranking (0.5/0.5) | 40/54 |
| BDC | 21/54 |

## expansion (1890 instances)

Control schedule identical to DCR-v1 Admission's stored schedule: **1890/1890**.

| Variant | Joint feasible | Δ vs control (pp) | Only control | Only variant | p (Holm, 5 variants) | Deadline met | Budget met |
|---|---:|---:|---:|---:|---:|---:|---:|
| Control (= DCR-v1 Admission) | 1629 (86.2%) | | | | | 1629 | 1890 |
| DCR-v1 Admission | 1629 (86.2%) | | | | | 1629 | 1890 |
| BDC | 1427 (75.5%) | | | | | 1435 | 1858 |
| No priced reserve (raw cheapest-remaining only) | 1579 (83.5%) | -2.6 | 53 | 3 | 2.4e-12 | 1579 | 1890 |
| Zero dual prices | 1629 (86.2%) | +0.0 | 0 | 0 | 1.0e+00 | 1629 | 1890 |
| Time-only ranking | 984 (52.1%) | -34.1 | 648 | 3 | 4.9e-188 | 984 | 1890 |
| Budget-only ranking | 961 (50.8%) | -35.3 | 727 | 59 | 1.1e-146 | 961 | 1890 |
| Weighted-sum ranking (0.5/0.5) | 1659 (87.8%) | +1.6 | 17 | 47 | 4.5e-04 | 1659 | 1890 |

Where both are jointly feasible, median variant/control ratio:

| Variant | n | Makespan | Cost |
|---|---:|---:|---:|
| No priced reserve (raw cheapest-remaining only) | 1576 | 1.000 | 1.000 |
| Zero dual prices | 1629 | 1.000 | 1.000 |
| Time-only ranking | 981 | 1.267 | 1.062 |
| Budget-only ranking | 902 | 6.519 | 0.139 |
| Weighted-sum ranking (0.5/0.5) | 1612 | 1.018 | 0.999 |

Joint feasibility under tight QoS:

| Algorithm | Tight joint feasible |
|---|---:|
| Control (= DCR-v1 Admission) | 445/630 |
| No priced reserve (raw cheapest-remaining only) | 398/630 |
| Zero dual prices | 445/630 |
| Time-only ranking | 336/630 |
| Budget-only ranking | 111/630 |
| Weighted-sum ranking (0.5/0.5) | 447/630 |
| BDC | 241/630 |
