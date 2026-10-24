# Robustness to noise and IoT/fog/cloud placement (dev)

59520 rows, 0 with errors.

## Joint feasibility under noise (% of all dev instances, mean over draws)

| Algorithm | nominal | ±10% | ±20% | ±30% | kept feasible at ±10% / ±20% / ±30% (of nominally feasible) |
|---|---:|---:|---:|---:|---|
| dcr-v3-rescue | 98.1 | 78.0 | 75.1 | 67.2 | 79% / 76% / 68% |
| dcr-v1-admission | 87.5 | 70.6 | 68.6 | 61.8 | 81% / 78% / 70% |
| dcr-v1 | 86.9 | 71.4 | 68.7 | 62.1 | 82% / 79% / 71% |
| dcr-v0 | 86.9 | 70.6 | 68.6 | 61.8 | 81% / 78% / 71% |
| dcr-v0-opt | 86.9 | 70.6 | 68.6 | 61.8 | 81% / 78% / 71% |
| bdc | 75.0 | 68.9 | 64.3 | 62.4 | 92% / 85% / 82% |
| bdsd | 58.8 | 58.2 | 57.9 | 57.6 | 99% / 98% / 98% |
| dbcs | 47.5 | 23.1 | 22.1 | 21.3 | 48% / 46% / 44% |
| bdheft | 45.0 | 37.6 | 34.4 | 33.7 | 79% / 71% / 71% |
| bddc | 23.8 | 23.5 | 24.2 | 24.0 | 97% / 96% / 93% |
| heft-ifc | 5.0 | 3.6 | 4.4 | 5.6 | 36% / 34% / 24% |
| peft-ifc | 0.6 | 0.9 | 2.4 | 2.8 | 50% / 50% / 40% |

## Median makespan / deadline under ±20% noise (nominally feasible schedules)

| Algorithm | median | p90 |
|---|---:|---:|
| dcr-v3-rescue | 0.551 | 0.994 |
| dcr-v1-admission | 0.451 | 0.978 |
| dcr-v1 | 0.441 | 0.979 |
| dcr-v0 | 0.441 | 0.977 |
| dcr-v0-opt | 0.441 | 0.977 |
| bdc | 0.375 | 0.954 |
| bdsd | 0.332 | 0.886 |
| dbcs | 0.193 | 0.972 |
| bdheft | 0.176 | 0.928 |
| bddc | 0.158 | 0.779 |
| heft-ifc | 0.841 | 1.074 |
| peft-ifc | 0.861 | 0.891 |

## Placement of nominal schedules (share of tasks / busy time / compute cost, %)

| Algorithm | IoT | Fog | Cloud |
|---|---|---|---|
| dcr-v3-rescue | 34 / 57 / 8 | 43 / 28 / 32 | 23 / 14 / 60 |
| dcr-v1-admission | 37 / 58 / 7 | 41 / 28 / 32 | 22 / 14 / 60 |
| dcr-v1 | 37 / 58 / 7 | 41 / 28 / 32 | 22 / 14 / 60 |
| dcr-v0 | 37 / 58 / 7 | 41 / 28 / 32 | 22 / 14 / 60 |
| dcr-v0-opt | 37 / 58 / 7 | 41 / 28 / 32 | 22 / 14 / 60 |
| bdc | 35 / 62 / 9 | 37 / 26 / 35 | 28 / 13 / 56 |
| bdsd | 29 / 63 / 11 | 43 / 28 / 41 | 28 / 8 / 48 |
| dbcs | 59 / 62 / 4 | 21 / 25 / 39 | 20 / 14 / 57 |
| bdheft | 38 / 59 / 5 | 37 / 27 / 37 | 26 / 14 / 57 |
| bddc | 39 / 42 / 4 | 32 / 37 / 38 | 29 / 21 / 58 |
| heft-ifc | 43 / 38 / 4 | 29 / 41 / 40 | 28 / 22 / 57 |
| peft-ifc | 31 / 36 / 3 | 32 / 41 / 38 | 37 / 23 / 58 |
