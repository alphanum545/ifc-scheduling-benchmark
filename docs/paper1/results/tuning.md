# Tuned comparators


## BDC weight sweep (joint feasible)

| Set | w=0.1 | w=0.3 | w=0.5 | w=0.7 | w=0.9 | DCR-v1 Admission |
|---|---:|---:|---:|---:|---:|---:|
| dev (160) | 102 | 113 | **120** | 97 | 64 | 140 |
| expansion (1890) | 1223 | 1349 | **1427** | 1170 | 775 | 1629 |

- **Honest tuning** (weight picked on dev = 0.5): on expansion, DCR-v1 Admission solves 255 cases it cannot, it solves 53 DCR cannot (exact McNemar p = 7.6e-33).
- **Oracle weight on expansion** (0.5): DCR-only 255, comparator-only 53, p = 7.6e-33.
- **Virtual best over all five weights** (per-instance oracle): 1535/1890 vs DCR-v1 Admission 1629; DCR-only 194, oracle-only 100.

## BDDC weight sweep (joint feasible)

| Set | w=0.1 | w=0.3 | w=0.5 | w=0.7 | w=0.9 | DCR-v1 Admission |
|---|---:|---:|---:|---:|---:|---:|
| dev (160) | **84** | 60 | 38 | 36 | 20 | 140 |
| expansion (1890) | **1021** | 730 | 446 | 416 | 213 | 1629 |

- **Honest tuning** (weight picked on dev = 0.1): on expansion, DCR-v1 Admission solves 634 cases it cannot, it solves 26 DCR cannot (exact McNemar p = 1.3e-152).
- **Oracle weight on expansion** (0.1): DCR-only 634, comparator-only 26, p = 1.3e-152.
- **Virtual best over all five weights** (per-instance oracle): 1223/1890 vs DCR-v1 Admission 1629; DCR-only 437, oracle-only 31.

## BDHEFT weight sweep (joint feasible)

| Set | w=0.1 | w=0.3 | w=0.5 | w=0.7 | w=0.9 | DCR-v1 Admission |
|---|---:|---:|---:|---:|---:|---:|
| dev (160) | **92** | 80 | 72 | 68 | 68 | 140 |
| expansion (1890) | **1019** | 929 | 852 | 815 | 803 | 1629 |

- **Honest tuning** (weight picked on dev = 0.1): on expansion, DCR-v1 Admission solves 641 cases it cannot, it solves 31 DCR cannot (exact McNemar p = 2.9e-149).
- **Oracle weight on expansion** (0.1): DCR-only 641, comparator-only 31, p = 2.9e-149.
- **Virtual best over all five weights** (per-instance oracle): 1236/1890 vs DCR-v1 Admission 1629; DCR-only 452, oracle-only 59.
