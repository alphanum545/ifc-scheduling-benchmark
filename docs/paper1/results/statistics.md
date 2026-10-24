
# dev set (160 instances, every algorithm valid on every case)

## Feasibility with 95% Wilson intervals

| Algorithm | Joint | 95% CI | Deadline only | Budget only |
|---|---:|---|---:|---:|
| DCR-v3 Rescue | 157 (98.1%) | 94.6–99.4% | 157 | 160 |
| DCR-v1 Admission | 140 (87.5%) | 81.5–91.8% | 140 | 160 |
| DCR-v0 | 139 (86.9%) | 80.8–91.3% | 139 | 160 |
| DCR-v0 (optimized) | 139 (86.9%) | 80.8–91.3% | 139 | 160 |
| DCR-v1 (full ranking) | 139 (86.9%) | 80.8–91.3% | 139 | 160 |
| BDC (w=0.5) | 120 (75.0%) | 67.8–81.1% | 120 | 156 |
| BDSD | 94 (58.8%) | 51.0–66.1% | 94 | 160 |
| DBCS | 76 (47.5%) | 39.9–55.2% | 76 | 160 |
| BDHEFT (a=0.5) | 72 (45.0%) | 37.5–52.7% | 79 | 149 |
| BDDC (w=0.5) | 38 (23.8%) | 17.8–30.9% | 133 | 61 |
| HEFT-IFC | 8 (5.0%) | 2.6–9.6% | 160 | 8 |
| PEFT-IFC | 1 (0.6%) | 0.1–3.5% | 151 | 4 |

## Exact McNemar: DCR-v1 Admission vs each comparator (Holm-adjusted)

| Against | Only DCR-v1 | Only other | Both | Neither | Δ (pp) | p (exact) | p (Holm) |
|---|---:|---:|---:|---:|---:|---:|---:|
| BDC (w=0.5) | 24 | 4 | 116 | 16 | +12.5 | 1.80e-04 | 1.80e-04 |
| BDSD | 50 | 4 | 90 | 16 | +28.8 | 3.80e-11 | 7.61e-11 |
| DBCS | 64 | 0 | 76 | 20 | +40.0 | 1.08e-19 | 3.25e-19 |
| BDHEFT (a=0.5) | 68 | 0 | 72 | 20 | +42.5 | 6.78e-21 | 2.71e-20 |
| BDDC (w=0.5) | 103 | 1 | 37 | 19 | +63.8 | 1.04e-29 | 5.18e-29 |
| HEFT-IFC | 132 | 0 | 8 | 20 | +82.5 | 3.67e-40 | 2.20e-39 |
| PEFT-IFC | 139 | 0 | 1 | 20 | +86.9 | 2.87e-42 | 2.01e-41 |

## DCR-v3 Rescue (extension)

| Comparison | Only first | Only second | Both | p (exact) |
|---|---:|---:|---:|---:|
| DCR-v3 Rescue vs DCR-v1 Admission | 17 | 0 | 140 | 1.53e-05 |
| DCR-v3 Rescue vs BDC (w=0.5) | 38 | 1 | 119 | 1.46e-10 |

## Mechanism ablation predeclared in the DCR-v1 spec

A = capacity-only reserve (DCR-v0 optimized), B = child-arrival reserve in admission only (DCR-v1 Admission), C = in admission and ranking (DCR-v1 full).

| Pair | Only first | Only second | Both | p (exact) |
|---|---:|---:|---:|---:|
| DCR-v1 Admission vs DCR-v0 (optimized) | 1 | 0 | 139 | 1.00e+00 |
| DCR-v1 (full ranking) vs DCR-v0 (optimized) | 1 | 1 | 138 | 1.00e+00 |
| DCR-v1 Admission vs DCR-v1 (full ranking) | 1 | 0 | 139 | 1.00e+00 |
| DCR-v0 (optimized) vs DCR-v0 | 0 | 0 | 139 | 1.00e+00 |
| DCR-v0 vs BDC (w=0.5) | 24 | 5 | 115 | 5.46e-04 |

## DCR-v1 Admission vs BDC by QoS level

| QoS | n | DCR-v1 | BDC | Only DCR-v1 | Only BDC | p (exact) |
|---|---:|---:|---:|---:|---:|---:|
| relaxed | 54 | 54 | 54 | 0 | 0 | 1.00e+00 |
| moderate | 52 | 47 | 45 | 4 | 2 | 6.88e-01 |
| tight | 54 | 39 | 21 | 20 | 2 | 1.21e-04 |

## Quality when both are jointly feasible: DCR-v1 Admission / other (median, 95% bootstrap CI)

| Against | Metric | n | Median ratio | 95% CI | DCR better / tie / worse | Wilcoxon p |
|---|---|---:|---:|---|---|---:|
| BDC (w=0.5) | makespan | 116 | 0.851 | 0.816–0.903 | 96 / 0 / 20 | 1.8e-12 |
| BDC (w=0.5) | compute | 116 | 1.006 | 1.004–1.013 | 25 / 0 / 91 | 8.0e-04 |
| BDSD | makespan | 90 | 0.861 | 0.762–0.966 | 57 / 0 / 33 | 1.6e-02 |
| BDSD | compute | 90 | 1.195 | 1.103–1.293 | 15 / 0 / 75 | 2.0e-10 |
| DBCS | makespan | 76 | 0.661 | 0.550–0.878 | 56 / 0 / 20 | 2.4e-08 |
| DBCS | compute | 76 | 0.921 | 0.878–0.950 | 76 / 0 / 0 | 3.6e-14 |
| BDHEFT (a=0.5) | makespan | 72 | 1.004 | 0.936–1.072 | 36 / 0 / 36 | 5.7e-01 |
| BDHEFT (a=0.5) | compute | 72 | 0.935 | 0.887–0.985 | 57 / 0 / 15 | 3.0e-09 |

# expansion set (1890 instances, every algorithm valid on every case)

## Feasibility with 95% Wilson intervals

| Algorithm | Joint | 95% CI | Deadline only | Budget only |
|---|---:|---|---:|---:|
| DCR-v3 Rescue | 1844 (97.6%) | 96.8–98.2% | 1844 | 1890 |
| DCR-v1 Admission | 1629 (86.2%) | 84.6–87.7% | 1629 | 1890 |
| DCR-v0 | 1619 (85.7%) | 84.0–87.2% | 1619 | 1890 |
| DCR-v0 (optimized) | 1619 (85.7%) | 84.0–87.2% | 1619 | 1890 |
| DCR-v1 (full ranking) | 1627 (86.1%) | 84.5–87.6% | 1627 | 1890 |
| BDC (w=0.5) | 1427 (75.5%) | 73.5–77.4% | 1435 | 1858 |
| BDSD | 1109 (58.7%) | 56.4–60.9% | 1109 | 1890 |
| DBCS | 904 (47.8%) | 45.6–50.1% | 904 | 1890 |
| BDHEFT (a=0.5) | 852 (45.1%) | 42.8–47.3% | 934 | 1710 |
| BDDC (w=0.5) | 446 (23.6%) | 21.7–25.6% | 1609 | 679 |
| HEFT-IFC | 106 (5.6%) | 4.7–6.7% | 1890 | 106 |
| PEFT-IFC | 18 (1.0%) | 0.6–1.5% | 1826 | 35 |

## Exact McNemar: DCR-v1 Admission vs each comparator (Holm-adjusted)

| Against | Only DCR-v1 | Only other | Both | Neither | Δ (pp) | p (exact) | p (Holm) |
|---|---:|---:|---:|---:|---:|---:|---:|
| BDC (w=0.5) | 255 | 53 | 1374 | 208 | +10.7 | 7.62e-33 | 7.62e-33 |
| BDSD | 584 | 64 | 1045 | 197 | +27.5 | 5.29e-106 | 1.06e-105 |
| DBCS | 726 | 1 | 903 | 260 | +38.4 | 2.06e-216 | 8.25e-216 |
| BDHEFT (a=0.5) | 790 | 13 | 839 | 248 | +41.1 | 3.20e-214 | 9.61e-214 |
| BDDC (w=0.5) | 1183 | 0 | 446 | 261 | +62.6 | 0.00e+00 | 0.00e+00 |
| HEFT-IFC | 1523 | 0 | 106 | 261 | +80.6 | 0.00e+00 | 0.00e+00 |
| PEFT-IFC | 1611 | 0 | 18 | 261 | +85.2 | 0.00e+00 | 0.00e+00 |

## DCR-v3 Rescue (extension)

| Comparison | Only first | Only second | Both | p (exact) |
|---|---:|---:|---:|---:|
| DCR-v3 Rescue vs DCR-v1 Admission | 215 | 0 | 1629 | 3.80e-65 |
| DCR-v3 Rescue vs BDC (w=0.5) | 420 | 3 | 1424 | 1.16e-120 |

## Mechanism ablation predeclared in the DCR-v1 spec

A = capacity-only reserve (DCR-v0 optimized), B = child-arrival reserve in admission only (DCR-v1 Admission), C = in admission and ranking (DCR-v1 full).

| Pair | Only first | Only second | Both | p (exact) |
|---|---:|---:|---:|---:|
| DCR-v1 Admission vs DCR-v0 (optimized) | 10 | 0 | 1619 | 1.95e-03 |
| DCR-v1 (full ranking) vs DCR-v0 (optimized) | 13 | 5 | 1614 | 9.63e-02 |
| DCR-v1 Admission vs DCR-v1 (full ranking) | 5 | 3 | 1624 | 7.27e-01 |
| DCR-v0 (optimized) vs DCR-v0 | 0 | 0 | 1619 | 1.00e+00 |
| DCR-v0 vs BDC (w=0.5) | 247 | 55 | 1372 | 3.29e-30 |

## DCR-v1 Admission vs BDC by QoS level

| QoS | n | DCR-v1 | BDC | Only DCR-v1 | Only BDC | p (exact) |
|---|---:|---:|---:|---:|---:|---:|
| relaxed | 630 | 630 | 630 | 0 | 0 | 1.00e+00 |
| moderate | 630 | 554 | 556 | 27 | 29 | 8.94e-01 |
| tight | 630 | 445 | 241 | 228 | 24 | 6.90e-43 |

## Quality when both are jointly feasible: DCR-v1 Admission / other (median, 95% bootstrap CI)

| Against | Metric | n | Median ratio | 95% CI | DCR better / tie / worse | Wilcoxon p |
|---|---|---:|---:|---|---|---:|
| BDC (w=0.5) | makespan | 1374 | 0.844 | 0.834–0.854 | 1133 / 0 / 241 | 3.0e-144 |
| BDC (w=0.5) | compute | 1374 | 1.010 | 1.008–1.012 | 314 / 0 / 1060 | 6.3e-41 |
| BDSD | makespan | 1045 | 0.864 | 0.835–0.894 | 610 / 0 / 435 | 2.9e-11 |
| BDSD | compute | 1045 | 1.161 | 1.146–1.193 | 213 / 0 / 832 | 3.4e-96 |
| DBCS | makespan | 903 | 0.729 | 0.683–0.773 | 649 / 4 / 250 | 3.0e-79 |
| DBCS | compute | 903 | 0.931 | 0.921–0.940 | 898 / 0 / 5 | 4.4e-149 |
| BDHEFT (a=0.5) | makespan | 839 | 1.000 | 0.991–1.013 | 421 / 2 / 416 | 7.7e-03 |
| BDHEFT (a=0.5) | compute | 839 | 0.959 | 0.947–0.969 | 687 / 0 / 152 | 1.6e-84 |

# Runtime (155 dev cases) (dev set, GitHub runners, one instance at a time, median of 2 repetitions)

Paired ratio = algorithm runtime / BDC runtime on the same case and machine. The expansion run used 4 parallel processes per machine and is excluded from runtime claims.

| Algorithm | Median ratio | 95% CI | p95 (nearest rank) | 95% CI | max |
|---|---:|---|---:|---|---:|
| DCR-v3 Rescue | 0.689 | 0.584–0.797 | 3.128 | 1.759–4.323 | 8.18 |
| DCR-v1 Admission | 0.594 | 0.519–0.688 | 1.195 | 1.086–1.260 | 1.42 |
| DCR-v0 | 1.004 | 0.922–1.398 | 3.205 | 2.845–3.662 | 4.27 |
| DCR-v0 (optimized) | 0.486 | 0.428–0.557 | 1.046 | 0.948–1.149 | 1.34 |
| DCR-v1 (full ranking) | 0.593 | 0.517–0.679 | 1.182 | 1.089–1.258 | 1.42 |
| BDSD | 0.791 | 0.765–0.823 | 0.935 | 0.918–0.947 | 0.96 |
| DBCS | 0.869 | 0.844–0.891 | 0.959 | 0.952–0.964 | 0.98 |
| BDHEFT (a=0.5) | 0.791 | 0.756–0.815 | 0.926 | 0.911–0.933 | 0.95 |
| BDDC (w=0.5) | 1.007 | 1.005–1.010 | 1.062 | 1.037–1.073 | 1.20 |
| HEFT-IFC | 0.761 | 0.735–0.784 | 0.920 | 0.907–0.923 | 0.94 |
| PEFT-IFC | 0.492 | 0.473–0.507 | 0.555 | 0.553–0.566 | 0.60 |

Rows whose CPU model differs from the BDC row of the same case: 0.
